"use client";

import React, { useState, useEffect } from "react";
import { remindersApi, type Reminder } from "@/lib/api";

const REMINDER_TYPES = [
  { id: "MEDICATION", icon: "medication", label: "Medication", color: "bg-[var(--color-primary)]" },
  { id: "APPOINTMENT", icon: "event", label: "Appointment", color: "bg-[var(--color-secondary)]" },
  { id: "FOLLOW_UP", icon: "follow_the_signs", label: "Follow-Up", color: "bg-[var(--color-success)]" },
  { id: "VACCINATION", icon: "vaccines", label: "Vaccination", color: "bg-[var(--color-tertiary)]" },
  { id: "CUSTOM", icon: "alarm", label: "Custom", color: "bg-black" },
];

export default function Reminders() {
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    title: "",
    reminder_type: "MEDICATION",
    scheduled_at: "",
    body: "",
    recurrence_rule: "FREQ=DAILY",
  });

  const fetchReminders = async () => {
    try {
      setLoading(true);
      const res = await remindersApi.list();
      setReminders(res.data || []);
    } catch {
      setReminders([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchReminders(); }, []);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.title || !form.scheduled_at) return;
    setSubmitting(true);
    try {
      await remindersApi.create({
        title: form.title,
        reminder_type: form.reminder_type,
        scheduled_at: new Date(form.scheduled_at).toISOString(),
        body: form.body || undefined,
        recurrence_rule: form.recurrence_rule || undefined,
        delivery_channels: ["PUSH"],
      });
      setShowAddModal(false);
      setForm({ title: "", reminder_type: "MEDICATION", scheduled_at: "", body: "", recurrence_rule: "FREQ=DAILY" });
      fetchReminders();
    } catch {
      // silent
    } finally {
      setSubmitting(false);
    }
  };

  const handleToggle = async (reminder: Reminder) => {
    try {
      await remindersApi.update(reminder.id, { is_active: !reminder.is_active });
      fetchReminders();
    } catch { /* silent */ }
  };

  const handleDelete = async (id: string) => {
    try {
      await remindersApi.delete(id);
      fetchReminders();
    } catch { /* silent */ }
  };

  const getTypeInfo = (type: string) =>
    REMINDER_TYPES.find((t) => t.id === type) || REMINDER_TYPES[4];

  const activeReminders = reminders.filter((r) => r.is_active);
  const inactiveReminders = reminders.filter((r) => !r.is_active);

  return (
    <div className="dashboard-amber">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="font-headline text-3xl font-black tracking-tight" style={{ color: "#FCB201" }}>
            Reminders
          </h2>
          <p className="text-sm font-bold opacity-60 mt-1" style={{ color: "#FCB201" }}>
            {activeReminders.length} active · {inactiveReminders.length} paused
          </p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="px-4 py-2 bg-[var(--color-primary)] text-white font-headline font-black uppercase tracking-widest text-xs brick-shadow rounded cursor-pointer hover:brightness-110 flex items-center gap-2"
        >
          <span className="material-symbols-outlined text-sm" style={{ color: "white" }}>alarm_add</span>
          New Reminder
        </button>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-5 gap-3 mb-8">
        {REMINDER_TYPES.map((type) => {
          const count = reminders.filter((r) => r.reminder_type === type.id).length;
          return (
            <div key={type.id} className="bg-white brick-shadow rounded-xl p-4 flex flex-col items-center gap-2 studs-light">
              <div className={`w-8 h-8 rounded flex items-center justify-center brick-shadow ${type.color}`}>
                <span className="material-symbols-outlined text-white text-sm" style={{ color: "white" }}>
                  {type.icon}
                </span>
              </div>
              <p className="font-headline font-black text-2xl text-black">{count}</p>
              <p className="text-[8px] font-black uppercase tracking-widest text-black/50">{type.label}</p>
            </div>
          );
        })}
      </div>

      {/* Reminders List */}
      {loading ? (
        <div className="flex items-center justify-center h-48">
          <span className="material-symbols-outlined text-5xl animate-spin" style={{ color: "#FCB201" }}>
            progress_activity
          </span>
        </div>
      ) : reminders.length === 0 ? (
        <div className="bg-white brick-shadow rounded-xl p-16 flex flex-col items-center gap-4 studs-light">
          <span className="material-symbols-outlined text-7xl opacity-20" style={{ color: "#FCB201" }}>
            alarm_off
          </span>
          <p className="font-headline font-black text-lg opacity-40" style={{ color: "#FCB201" }}>
            No reminders yet
          </p>
          <p className="text-xs font-bold opacity-30" style={{ color: "#FCB201" }}>
            Upload a prescription to auto-create reminders, or add one manually
          </p>
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {reminders.map((reminder) => {
            const typeInfo = getTypeInfo(reminder.reminder_type);
            const scheduledDate = new Date(reminder.scheduled_at);
            return (
              <div
                key={reminder.id}
                className={`bg-white brick-shadow rounded-xl p-4 flex items-center gap-4 studs-light transition-opacity ${!reminder.is_active ? "opacity-50" : ""}`}
              >
                {/* Type Icon */}
                <div className={`w-12 h-12 rounded flex items-center justify-center brick-shadow flex-shrink-0 ${typeInfo.color}`}>
                  <span className="material-symbols-outlined text-white" style={{ color: "white" }}>
                    {typeInfo.icon}
                  </span>
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <p className="font-headline font-black text-sm text-black leading-tight">{reminder.title}</p>
                  {reminder.body && (
                    <p className="text-xs text-black/50 font-bold mt-0.5 truncate">{reminder.body}</p>
                  )}
                  <div className="flex items-center gap-3 mt-1">
                    <span className="flex items-center gap-1 text-[9px] font-black uppercase tracking-widest text-black/40">
                      <span className="material-symbols-outlined text-[12px]" style={{ color: "inherit" }}>schedule</span>
                      {scheduledDate.toLocaleDateString("en-IN", { day: "numeric", month: "short" })}
                      {" · "}
                      {scheduledDate.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })}
                    </span>
                    {reminder.recurrence_rule && (
                      <span className="flex items-center gap-1 text-[9px] font-black uppercase tracking-widest text-black/40">
                        <span className="material-symbols-outlined text-[12px]" style={{ color: "inherit" }}>repeat</span>
                        {reminder.recurrence_rule.replace("FREQ=", "").toLowerCase()}
                      </span>
                    )}
                  </div>
                </div>

                {/* Type badge */}
                <span className={`text-[8px] font-black uppercase tracking-widest px-2 py-1 rounded text-white flex-shrink-0 ${typeInfo.color}`}
                  style={{ color: "white" }}>
                  {typeInfo.label}
                </span>

                {/* Toggle + Delete */}
                <div className="flex items-center gap-2 flex-shrink-0">
                  <button
                    onClick={() => handleToggle(reminder)}
                    className={`w-9 h-9 rounded flex items-center justify-center brick-shadow cursor-pointer ${reminder.is_active ? "bg-[var(--color-success)]" : "bg-black/10"}`}
                    title={reminder.is_active ? "Pause" : "Activate"}
                  >
                    <span className="material-symbols-outlined text-sm" style={{ color: reminder.is_active ? "white" : "#666" }}>
                      {reminder.is_active ? "pause" : "play_arrow"}
                    </span>
                  </button>
                  <button
                    onClick={() => handleDelete(reminder.id)}
                    className="w-9 h-9 rounded flex items-center justify-center brick-shadow cursor-pointer bg-[var(--color-primary)]/10 hover:bg-[var(--color-primary)] group"
                  >
                    <span className="material-symbols-outlined text-sm text-[var(--color-primary)] group-hover:text-white" style={{ color: "inherit" }}>
                      delete
                    </span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Add Reminder Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-white brick-shadow-heavy rounded-2xl p-8 w-full max-w-md studs-light mx-4">
            <div className="flex items-center justify-between mb-6 mt-4">
              <h3 className="font-headline font-black text-xl text-black">New Reminder</h3>
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
                  placeholder="e.g. Take Metformin"
                  className="w-full border-2 border-black/20 rounded px-3 py-2 text-sm font-bold text-black bg-black/5 focus:outline-none focus:border-[var(--color-primary)] brick-shadow"
                />
              </div>

              <div>
                <label className="text-[9px] font-black uppercase tracking-widest text-black/60 block mb-1">Type</label>
                <div className="grid grid-cols-5 gap-2">
                  {REMINDER_TYPES.map((type) => (
                    <button
                      type="button"
                      key={type.id}
                      onClick={() => setForm({ ...form, reminder_type: type.id })}
                      className={`flex flex-col items-center gap-1 p-2 rounded brick-shadow cursor-pointer text-[8px] font-black uppercase tracking-widest ${form.reminder_type === type.id ? type.color + " text-white" : "bg-black/5 text-black"}`}
                    >
                      <span className="material-symbols-outlined text-sm" style={{ color: form.reminder_type === type.id ? "white" : "inherit" }}>{type.icon}</span>
                      {type.label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-[9px] font-black uppercase tracking-widest text-black/60 block mb-1">Date & Time *</label>
                <input
                  required
                  type="datetime-local"
                  value={form.scheduled_at}
                  onChange={(e) => setForm({ ...form, scheduled_at: e.target.value })}
                  className="w-full border-2 border-black/20 rounded px-3 py-2 text-sm font-bold text-black bg-black/5 focus:outline-none focus:border-[var(--color-primary)] brick-shadow"
                />
              </div>

              <div>
                <label className="text-[9px] font-black uppercase tracking-widest text-black/60 block mb-1">Repeat</label>
                <select
                  value={form.recurrence_rule}
                  onChange={(e) => setForm({ ...form, recurrence_rule: e.target.value })}
                  className="w-full border-2 border-black/20 rounded px-3 py-2 text-sm font-bold text-black bg-black/5 focus:outline-none focus:border-[var(--color-primary)] brick-shadow"
                >
                  <option value="">One-time</option>
                  <option value="FREQ=DAILY">Daily</option>
                  <option value="FREQ=WEEKLY">Weekly</option>
                  <option value="FREQ=MONTHLY">Monthly</option>
                  <option value="FREQ=DAILY;BYHOUR=8,20">Twice daily (8am, 8pm)</option>
                </select>
              </div>

              <div>
                <label className="text-[9px] font-black uppercase tracking-widest text-black/60 block mb-1">Note (optional)</label>
                <input
                  value={form.body}
                  onChange={(e) => setForm({ ...form, body: e.target.value })}
                  placeholder="e.g. Take with food"
                  className="w-full border-2 border-black/20 rounded px-3 py-2 text-sm font-bold text-black bg-black/5 focus:outline-none focus:border-[var(--color-primary)] brick-shadow"
                />
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="w-full bg-[var(--color-primary)] text-white font-headline font-black uppercase tracking-widest text-xs py-3 rounded brick-shadow cursor-pointer hover:brightness-110 disabled:opacity-50 flex items-center justify-center gap-2 mt-2"
              >
                {submitting ? (
                  <span className="material-symbols-outlined text-sm animate-spin" style={{ color: "white" }}>progress_activity</span>
                ) : (
                  <span className="material-symbols-outlined text-sm" style={{ color: "white" }}>alarm_add</span>
                )}
                {submitting ? "Creating..." : "Set Reminder"}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
