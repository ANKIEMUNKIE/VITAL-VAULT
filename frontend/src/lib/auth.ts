// src/lib/auth.ts
// JWT token management — stores access and refresh tokens in localStorage.

const ACCESS_TOKEN_KEY = "vv_access_token";
const REFRESH_TOKEN_KEY = "vv_refresh_token";
const USER_KEY = "vv_user";

export interface TokenPair {
  access_token: string;
  refresh_token: string;
}

export interface StoredUser {
  id: string;
  email: string;
  role: string;
}

// ─── Token helpers ─────────────────────────────────────────────────────────

export function getTokens(): TokenPair | null {
  if (typeof window === "undefined") return null;
  const access = localStorage.getItem(ACCESS_TOKEN_KEY);
  const refresh = localStorage.getItem(REFRESH_TOKEN_KEY);
  if (!access || !refresh) return null;
  return { access_token: access, refresh_token: refresh };
}

export function setTokens(tokens: TokenPair): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
  localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

// ─── User helpers ──────────────────────────────────────────────────────────

export function getStoredUser(): StoredUser | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function setStoredUser(user: StoredUser): void {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

// ─── Auth state check ──────────────────────────────────────────────────────

export function isAuthenticated(): boolean {
  return getTokens() !== null;
}

// ─── Parse JWT payload (without verification — just to read expiry) ──────

export function parseJwtPayload(token: string): Record<string, unknown> | null {
  try {
    const base64Url = token.split(".")[1];
    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split("")
        .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
        .join("")
    );
    return JSON.parse(jsonPayload);
  } catch {
    return null;
  }
}

export function isTokenExpired(token: string): boolean {
  const payload = parseJwtPayload(token);
  if (!payload || typeof payload.exp !== "number") return true;
  // Consider expired if less than 30 seconds remain
  return payload.exp * 1000 < Date.now() + 30_000;
}
