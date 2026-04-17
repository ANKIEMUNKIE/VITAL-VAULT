"use client";

import React, { useState, useEffect } from "react";
import { appointmentsApi, type Appointment } from "@/lib/api";

const STATUS_STYLES: Record<string, { bg: string; label: string; icon: string }> = {
  SCHEDULED: { bg: "bg-[var(--color-secondary)]", label: "Scheduled", icon: "event" },
  COMPLETED: { bg: "bg-[var(--color-success)]", label: "Completed", icon: "task_alt" },
  CANCELLED: { bg: "bg-black/40", label: "Cancelled", icon: "cancel" },
  MISSED: { bg: "bg-[var(--color-primary)]", label: "Missed", icon: "event_busy" },
};

export default function Appointments() {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>("ALL");
  const [showAddModal, setShowAddModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    title: "",
    appointment_at: "",
    location: "",
    notes: "",
  });

  const fetchAppointments = async () => {
    try {
      setLoading(true);
      const res = await appointmentsApi.list(filter === "ALL" ? undefined : filter);
      setAppointments(res.data || []);
    } catch {
      setAppointments([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAppointments(); }, [filter]);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.title || !form.appointment_at) return;
    setSubmitting(true);
    try {
      await appointmentsApi.create({
        title: form.title,
        appointment_at: new Date(form.appointment_at).toISOString(),
        location: form.location || undefined,
        notes: form.notes || undefined,
      });
      setShowAddModal(false);
      setForm({ title: "", appointment_at: "", location: "", notes: "" });
      fetchAppointments();
    } catch {
      // silent
    } finally {
      setSubmitting(false);
    }
  };

  const scheduled = appointments.filter((a) => a.status === "SCHEDULED");
  const upcoming = scheduled
    .filter((a) => new Date(a.appointment_at) >= new Date())
    .sort((a, b) => new Date(a.appointment_at).getTime() - new Date(b.appointment_at).getTime());

  const filtered = filter === "ALL" ? appointments : appointments.filter((a) => a.status === filter);

  const isToday = (dateStr: string) => {
    const d = new Date(dateStr);
    const today = new Date();
    return d.toDateString() === today.toDateString();
  };

  const isTomorrow = (dateStr: string) => {
    const d = new Date(dateStr);
    const tom = new Date();
    tom.setDate(tom.getDate() + 1);
    return d.toDateString() === tom.toDateString();
  };

  const getDateLabel = (dateStr: string) => {
    if (isToday(dateStr)) return "Today";
    if (isTomorrow(dateStr)) return "Tomorrow";
    return new Date(dateStr).toLocaleDateString("en-IN", { weekday: "short", day: "numeric", month: "short" });
  };

  return (
    <div className="dashboard-amber">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="font-headline text-3xl font-black tracking-tight" style={{ color: "#FCB201" }}>
            Appointments
          </h2>
          <p className="text-sm font-bold opacity-60 mt-1" style={{ color: "#FCB201" }}>
            {scheduled.length} upcoming · {appointments.length} total
          </p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="px-4 py-2 bg-[var(--color-secondary)] text-white font-headline font-black uppercase tracking-widest text-xs brick-shadow rounded cursor-pointer hover:brightness-110 flex items-center gap-2"
        >
          <span className="material-symbols-outlined text-sm" style={{ color: "white" }}>event_available</span>
          Book Appointment
        </button>
      </div>

      {/* Next Upcoming Banner */}
      {upcoming[0] && (
        <div className="bg-[var(--color-secondary)] brick-shadow-heavy rounded-xl p-5 mb-8 flex items-center gap-5 studs-dark">
          <div className="w-16 h-16 bg-white/20 rounded-xl brick-shadow flex flex-col items-center justify-center flex-shrink-0">
            <p className="font-headline font-black text-2xl text-white leading-none">
              {new Date(upcoming[0].appointment_at).getDate()}
            </p>
            <p className="text-[9px] font-black uppercase tracking-widest text-white/70">
              {new Date(upcoming[0].appointment_at).toLocaleString("en-IN", { month: "short" })}
            </p>
          </div>
          <div className="flex-1">
            <p className="text-[9px] font-black uppercase tracking-widest text-white/60 mb-1">
              Next Appointment
            </p>
            <p className="font-headline font-black text-xl text-white leading-tight">{upcoming[0].title}</p>
            {upcoming[0].location && (
              <p className="text-sm text-white/70 font-bold mt-1 flex items-center gap-1">
                <span className="material-symbols-outlined text-sm" style={{ color: "inherit" }}>location_on</span>
                {upcoming[0].location}
              </p>
            )}
          </div>
          <div className="text-right">
            <p className="font-black text-white text-lg">
              {new Date(upcoming[0].appointment_at).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })}
            </p>
            <p className="text-[9px] font-black uppercase tracking-widest text-white/60">
              {getDateLabel(upcoming[0].appointment_at)}
            </p>
          </div>
        </div>
      )}

      {/* Filter Tabs */}
      <div className="flex gap-2 mb-6 flex-wrap">
        {["ALL", "SCHEDULED", "COMPLETED", "CANCELLED", "MISSED"].map((s) => (
          <button
            key={s}
            onClick={() => setFilter(s)}
            className={`px-3 py-2 rounded font-headline font-black uppercase tracking-widest text-[9px] brick-shadow cursor-pointer ${
              filter === s
                ? "bg-[var(--color-secondary)] text-white"
                : "bg-white text-black hover:brightness-95"
            }`}
          >
            {s === "ALL" ? "All" : STATUS_STYLES[s]?.label}
          </button>
        ))}
      </div>

      {/* Appointments List */}
      {loading ? (
        <div className="flex items-center justify-center h-48">
          <span className="material-symbols-outlined text-5xl animate-spin" style={{ color: "#FCB201" }}>
            progress_activity
          </span>
        </div>
      ) : filtered.length === 0 ? (
        <div className="bg-white brick-shadow rounded-xl p-16 flex flex-col items-center gap-4 studs-light">
          <span className="material-symbols-outlined text-7xl opacity-20" style={{ color: "#FCB201" }}>
            event_busy
          </span>
          <p className="font-headline font-black text-lg opacity-40" style={{ color: "#FCB201" }}>
            No appointments
          </p>
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {filtered
            .sort((a, b) => new Date(a.appointment_at).getTime() - new Date(b.appointment_at).getTime())
            .map((appt) => {
              const statusInfo = STATUS_STYLES[appt.status] || STATUS_STYLES.SCHEDULED;
              return (
                <div
                  key={appt.id}
                  className="bg-white brick-shadow rounded-xl p-4 flex items-center gap-4 studs-light lego-card"
                >
                  {/* Date Box */}
                  <div className={`w-14 h-14 rounded-xl flex flex-col items-center justify-center brick-shadow flex-shrink-0 ${statusInfo.bg}`}>
                    <p className="font-headline font-black text-xl text-white leading-none" style={{ color: "white" }}>
                      {new Date(appt.appointment_at).getDate()}
                    </p>
                    <p className="text-[8px] font-black uppercase tracking-widest text-white/80" style={{ color: "rgba(255,255,255,0.8)" }}>
                      {new Date(appt.appointment_at).toLocaleString("en-IN", { month: "short" })}
                    </p>
                  </div>

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="font-headline font-black text-sm text-black truncate">{appt.title}</p>
                      {(isToday(appt.appointment_at)) && (
                        <span className="text-[8px] font-black uppercase tracking-widest px-2 py-0.5 rounded bg-amber-400 text-black flex-shrink-0">Today</span>
                      )}
                      {(isTomorrow(appt.appointment_at)) && (
                        <span className="text-[8px] font-black uppercase tracking-widest px-2 py-0.5 rounded bg-blue-100 text-blue-800 flex-shrink-0">Tomorrow</span>
                      )}
                    </div>
                    <div className="flex items-center gap-3 mt-1 flex-wrap">
                      <span className="flex items-center gap-1 text-[9px] font-black text-black/40">
                        <span className="material-symbols-outlined text-[11px]" style={{ color: "inherit" }}>schedule</span>
                        {new Date(appt.appointment_at).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })}
                      </span>
                      {appt.location && (
                        <span className="flex items-center gap-1 text-[9px] font-black text-black/40 truncate">
                          <span className="material-symbols-outlined text-[11px]" style={{ color: "inherit" }}>location_on</span>
                          {appt.location}
                        </span>
                      )}
                      {appt.reminder_sent && (
                        <span className="flex items-center gap-1 text-[9px] font-black text-green-600">
                          <span className="material-symbols-outlined text-[11px]" style={{ color: "inherit" }}>notifications_active</span>
                          Reminded
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Status Badge */}
                  <div className="flex flex-col items-end gap-2 flex-shrink-0">
                    <span className={`text-[8px] font-black uppercase tracking-widest px-2 py-1 rounded text-white ${statusInfo.bg}`} style={{ color: "white" }}>
                      {statusInfo.label}
                    </span>
                    {appt.status === "SCHEDULED" && (
                      <div className="flex gap-1">
                        <button
                          onClick={async (e) => { e.stopPropagation(); await appointmentsApi.update(appt.id, { status: "COMPLETED" }); fetchAppointments(); }}
                          className="px-2 py-1 rounded text-[8px] font-black uppercase tracking-widest bg-[var(--color-success)] text-white brick-shadow cursor-pointer hover:brightness-110"
                          style={{ color: "white" }}
                        >
                          Done
                        </button>
                        <button
                          onClick={async (e) => { e.stopPropagation(); await appointmentsApi.update(appt.id, { status: "CANCELLED" }); fetchAppointments(); }}
                          className="px-2 py-1 rounded text-[8px] font-black uppercase tracking-widest bg-black/20 text-black brick-shadow cursor-pointer hover:bg-black/40"
                        >
                          Cancel
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
        </div>
      )}

      {/* Add Appointment Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-white brick-shadow-heavy rounded-2xl p-8 w-full max-w-md studs-light mx-4">
            <div className="flex items-center justify-between mb-6 mt-4">
              <h3 className="font-headline font-black text-xl text-black">Book Appointment</h3>
              <button onClick={() => setShowAddModal(false)} className="w-8 h-8 flex items-center justify-center rounded brick-shadow bg-black/5 cursor-pointer">
                <span className="material-symbols-outlined text-sm text-black">close</span>
              </button>
            </div>

            <form onSubmit={handleAdd} className="flex flex-col gap-4">
              <div>
                <label className="text-[9px] font-black uppercase tracking-widest text-black/60 block mb-1">Title *</label>
                <input
                  required
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                  placeholder="e.g. Cardiology Check-Up"
                  className="w-full border-2 border-black/20 rounded px-3 py-2 text-sm font-bold text-black bg-black/5 focus:outline-none focus:border-[var(--color-secondary)] brick-shadow"
                />
              </div>

              <div>
                <label className="text-[9px] font-black uppercase tracking-widest text-black/60 block mb-1">Date & Time *</label>
                <input
                  required
                  type="datetime-local"
                  value={form.appointment_at}
                  onChange={(e) => setForm({ ...form, appointment_at: e.target.value })}
                  className="w-full border-2 border-black/20 rounded px-3 py-2 text-sm font-bold text-black bg-black/5 focus:outline-none focus:border-[var(--color-secondary)] brick-shadow"
                />
              </div>

              <div>
                <label className="text-[9px] font-black uppercase tracking-widest text-black/60 block mb-1">Location</label>
                <input
                  value={form.location}
                  onChange={(e) => setForm({ ...form, location: e.target.value })}
                  placeholder="e.g. Apollo Hospitals, Block B"
                  className="w-full border-2 border-black/20 rounded px-3 py-2 text-sm font-bold text-black bg-black/5 focus:outline-none focus:border-[var(--color-secondary)] brick-shadow"
                />
              </div>

              <div>
                <label className="text-[9px] font-black uppercase tracking-widest text-black/60 block mb-1">Notes</label>
                <textarea
                  value={form.notes}
                  onChange={(e) => setForm({ ...form, notes: e.target.value })}
                  placeholder="Any preparation or notes..."
                  rows={3}
                  className="w-full border-2 border-black/20 rounded px-3 py-2 text-sm font-bold text-black bg-black/5 focus:outline-none focus:border-[var(--color-secondary)] brick-shadow resize-none"
                />
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="w-full bg-[var(--color-secondary)] text-white font-headline font-black uppercase tracking-widest text-xs py-3 rounded brick-shadow cursor-pointer hover:brightness-110 disabled:opacity-50 flex items-center justify-center gap-2 mt-2"
              >
                {submitting ? (
                  <span className="material-symbols-outlined text-sm animate-spin" style={{ color: "white" }}>progress_activity</span>
                ) : (
                  <span className="material-symbols-outlined text-sm" style={{ color: "white" }}>event_available</span>
                )}
                {submitting ? "Booking..." : "Book Appointment"}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
