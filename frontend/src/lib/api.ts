// src/lib/api.ts
// Centralized API client for Vital-Vault backend communication.
// Handles JWT injection, token refresh on 401, and typed request/response helpers.

import { getTokens, setTokens, clearTokens } from "./auth";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_PREFIX = "/api/v1";

// ─── Low-level fetch wrapper ───────────────────────────────────────────────

interface RequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  skipAuth?: boolean;
}

async function refreshAccessToken(): Promise<string | null> {
  const tokens = getTokens();
  if (!tokens?.refresh_token) return null;

  try {
    const res = await fetch(`${API_BASE}${API_PREFIX}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: tokens.refresh_token }),
    });

    if (!res.ok) {
      clearTokens();
      return null;
    }

    const data = await res.json();
    setTokens({
      access_token: data.access_token,
      refresh_token: tokens.refresh_token, // keep existing refresh token
    });
    return data.access_token;
  } catch {
    clearTokens();
    return null;
  }
}

export async function apiFetch<T = unknown>(
  path: string,
  options: RequestOptions = {}
): Promise<T> {
  const { body, skipAuth, headers: extraHeaders, ...rest } = options;

  const headers: Record<string, string> = {
    ...(extraHeaders as Record<string, string>),
  };

  // Don't set Content-Type for FormData (browser sets multipart boundary)
  if (body && !(body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  // Inject JWT if available
  if (!skipAuth) {
    const tokens = getTokens();
    if (tokens?.access_token) {
      headers["Authorization"] = `Bearer ${tokens.access_token}`;
    }
  }

  const url = path.startsWith("http") ? path : `${API_BASE}${API_PREFIX}${path}`;

  let res = await fetch(url, {
    ...rest,
    headers,
    body: body instanceof FormData ? body : body ? JSON.stringify(body) : undefined,
  });

  // On 401, try refreshing the token once
  if (res.status === 401 && !skipAuth) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      headers["Authorization"] = `Bearer ${newToken}`;
      res = await fetch(url, {
        ...rest,
        headers,
        body: body instanceof FormData ? body : body ? JSON.stringify(body) : undefined,
      });
    }
  }

  // 204 No Content
  if (res.status === 204) {
    return undefined as T;
  }

  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({ error: { message: res.statusText } }));
    const message = errorBody?.error?.message || errorBody?.detail || res.statusText;
    throw new ApiError(message, res.status, errorBody);
  }

  return res.json();
}

export class ApiError extends Error {
  status: number;
  body: unknown;

  constructor(message: string, status: number, body?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

// ─── Auth API ──────────────────────────────────────────────────────────────

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: {
    id: string;
    role: string;
    email: string;
  };
}

export interface RegisterResponse {
  user_id: string;
  email: string;
  role: string;
  message: string;
}

export const authApi = {
  login: (email: string, password: string) =>
    apiFetch<LoginResponse>("/auth/login", {
      method: "POST",
      body: { email, password },
      skipAuth: true,
    }),

  register: (data: {
    email: string;
    password: string;
    full_name: string;
    date_of_birth: string;
    role?: string;
  }) =>
    apiFetch<RegisterResponse>("/auth/register", {
      method: "POST",
      body: data,
      skipAuth: true,
    }),

  logout: (refresh_token: string) =>
    apiFetch("/auth/logout", {
      method: "POST",
      body: { refresh_token },
    }),
};

// ─── Records API ───────────────────────────────────────────────────────────

export interface RecordListItem {
  id: string;
  title: string;
  category?: { slug: string; label: string } | null;
  document_date?: string | null;
  processing_status: string;
  tags?: string[] | null;
  file_size_bytes: number;
  mime_type?: string | null;
  created_at: string;
}

export interface RecordListResponse {
  data: RecordListItem[];
  pagination: { page: number; limit: number; total: number };
}

export interface RecordUploadResponse {
  record_id: string;
  status: string;
  message: string;
  estimated_processing_seconds: number;
}

export interface RecordStatusResponse {
  record_id: string;
  status: string;
  progress_hint?: string | null;
}

export interface RecordDetail {
  id: string;
  title: string;
  document_date?: string | null;
  processing_status: string;
  category?: { slug: string; label: string } | null;
  extraction?: {
    diagnosed_conditions?: string[] | null;
    extracted_medications?: Record<string, unknown>[] | null;
    ai_summary?: string | null;
    confidence_score?: number | null;
    doctor_name?: string | null;
    hospital_name?: string | null;
  } | null;
  download_url?: string | null;
  tags?: string[] | null;
  file_size_bytes: number;
  created_at: string;
}

export const recordsApi = {
  list: (params?: { category?: string; page?: number; limit?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.category) searchParams.set("category", params.category);
    if (params?.page) searchParams.set("page", String(params.page));
    if (params?.limit) searchParams.set("limit", String(params.limit));
    const qs = searchParams.toString();
    return apiFetch<RecordListResponse>(`/records${qs ? `?${qs}` : ""}`);
  },

  get: (recordId: string) => apiFetch<RecordDetail>(`/records/${recordId}`),

  getStatus: (recordId: string) =>
    apiFetch<RecordStatusResponse>(`/records/${recordId}/status`),

  upload: (file: File, title?: string, categorySlug?: string, documentDate?: string) => {
    const formData = new FormData();
    formData.append("file", file);
    if (title) formData.append("title", title);
    if (categorySlug) formData.append("category_slug", categorySlug);
    if (documentDate) formData.append("document_date", documentDate);
    return apiFetch<RecordUploadResponse>("/records/upload", {
      method: "POST",
      body: formData,
    });
  },

  delete: (recordId: string) =>
    apiFetch(`/records/${recordId}`, { method: "DELETE" }),
};

// ─── Medications API ───────────────────────────────────────────────────────

export interface Medication {
  id: string;
  name: string;
  generic_name?: string | null;
  dosage?: string | null;
  frequency?: string | null;
  route?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  is_active: boolean;
  prescribed_by?: string | null;
  notes?: string | null;
  source_record_id?: string | null;
  created_at: string;
}

export interface MedicationListResponse {
  data: Medication[];
}

export const medicationsApi = {
  list: (active = true) =>
    apiFetch<MedicationListResponse>(`/medications?active=${active}`),

  create: (data: {
    name: string;
    dosage?: string;
    frequency?: string;
    route?: string;
    start_date?: string;
    prescribed_by?: string;
    notes?: string;
  }) =>
    apiFetch<Medication>("/medications", { method: "POST", body: data }),

  update: (id: string, data: { is_active?: boolean; dosage?: string; frequency?: string }) =>
    apiFetch<Medication>(`/medications/${id}`, { method: "PATCH", body: data }),

  delete: (id: string) =>
    apiFetch(`/medications/${id}`, { method: "DELETE" }),
};

// ─── Appointments API ──────────────────────────────────────────────────────

export interface Appointment {
  id: string;
  title: string;
  doctor_id?: string | null;
  appointment_at: string;
  location?: string | null;
  notes?: string | null;
  status: string;
  reminder_sent: boolean;
  created_at: string;
}

export interface AppointmentListResponse {
  data: Appointment[];
}

export const appointmentsApi = {
  list: (status?: string) => {
    const qs = status ? `?appointment_status=${status}` : "";
    return apiFetch<AppointmentListResponse>(`/appointments${qs}`);
  },

  create: (data: {
    title: string;
    appointment_at: string;
    doctor_id?: string;
    location?: string;
    notes?: string;
  }) =>
    apiFetch<Appointment>("/appointments", { method: "POST", body: data }),

  update: (id: string, data: { status?: string; title?: string; location?: string }) =>
    apiFetch<Appointment>(`/appointments/${id}`, { method: "PATCH", body: data }),

  delete: (id: string) =>
    apiFetch(`/appointments/${id}`, { method: "DELETE" }),
};

// ─── Timeline API ──────────────────────────────────────────────────────────

export interface TimelineEvent {
  type: string;
  record_id?: string | null;
  appointment_id?: string | null;
  title: string;
  category?: string | null;
  summary?: string | null;
  doctor?: string | null;
  tags?: string[] | null;
}

export interface TimelineDay {
  date: string;
  events: TimelineEvent[];
}

export interface TimelineResponse {
  patient_id: string;
  timeline: TimelineDay[];
}

export const timelineApi = {
  get: (patientId: string) =>
    apiFetch<TimelineResponse>(`/patients/${patientId}/timeline`),
};

// ─── User API ──────────────────────────────────────────────────────────────

export interface UserProfile {
  id: string;
  email: string;
  role: string;
  phone_number?: string | null;
  is_email_verified: boolean;
  mfa_enabled: boolean;
  full_name?: string | null;
  date_of_birth?: string | null;
  gender?: string | null;
  blood_group?: string | null;
  created_at: string;
}

export interface StorageStats {
  storage_used_bytes: number;
  storage_quota_bytes: number;
  usage_percentage: number;
  records_count: number;
}

export const usersApi = {
  getMe: () => apiFetch<UserProfile>("/users/me"),
  updateProfile: (data: Partial<UserProfile>) =>
    apiFetch<UserProfile>("/users/me", { method: "PATCH", body: data }),
  getStorage: () => apiFetch<StorageStats>("/users/me/storage"),
  exportData: () => apiFetch<Record<string, unknown>>("/users/me/data-export"),
};

// ─── Reminders API ─────────────────────────────────────────────────────────

export interface Reminder {
  id: string;
  title: string;
  reminder_type: string;
  scheduled_at: string;
  is_active: boolean;
  body?: string | null;
  recurrence_rule?: string | null;
  created_at: string;
}

export interface ReminderListResponse {
  data: Reminder[];
}

export const remindersApi = {
  list: () => apiFetch<ReminderListResponse>("/reminders"),

  create: (data: {
    title: string;
    reminder_type: string;
    scheduled_at: string;
    body?: string;
    recurrence_rule?: string;
    medication_id?: string;
    delivery_channels?: string[];
  }) => apiFetch<Reminder>("/reminders", { method: "POST", body: data }),

  update: (id: string, data: { is_active?: boolean; title?: string; scheduled_at?: string }) =>
    apiFetch<Reminder>(`/reminders/${id}`, { method: "PATCH", body: data }),

  delete: (id: string) => apiFetch(`/reminders/${id}`, { method: "DELETE" }),
};

// ─── Subscriptions API ─────────────────────────────────────────────────────

export interface SubscriptionUsage {
  tier: string;
  limits: {
    max_records: number;
    max_storage_mb: number;
    max_reminders: number;
    max_shared_doctors: number;
    ai_extractions_per_month: number;
    features: string[];
  };
  usage: { records: number; reminders: number; storage_mb: number };
  percentages: { records: number; storage: number; reminders: number };
}

export const subscriptionsApi = {
  getMySubscription: () => apiFetch<SubscriptionUsage>("/subscriptions/me"),
};

// ─── Users API ─────────────────────────────────────────────────────────────

// Removed duplicate usersApi

// ─── Health check ──────────────────────────────────────────────────────────

export const healthApi = {
  check: () => apiFetch<{ status: string; version: string }>(`${API_BASE}/health`, { skipAuth: true }),
};
