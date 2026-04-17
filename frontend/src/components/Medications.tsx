"use client";

import React, { useState, useEffect } from "react";
import { medicationsApi, type Medication } from "@/lib/api";

export default function Medications() {
  const [medications, setMedications] = useState<Medication[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAll, setShowAll] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    name: "",
    dosage: "",
    frequency: "",
    route: "",
    start_date: "",
    prescribed_by: "",
    notes: "",
  });

  const fetchMeds = async () => {
    try {
      setLoading(true);
      const res = await medicationsApi.list(showAll ? false : true);
      setMedications(res.data || []);
    } catch {
      setMedications([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchMeds(); }, [showAll]);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name) return;
    setSubmitting(true);
    try {
      await medicationsApi.create({
        name: form.name,
        dosage: form.dosage || undefined,
        frequency: form.frequency || undefined,
        route: form.route || undefined,
        start_date: form.start_date || undefined,
        prescribed_by: form.prescribed_by || undefined,
        notes: form.notes || undefined,
      });
      setShowAddModal(false);
      setForm({ name: "", dosage: "", frequency: "", route: "", start_date: "", prescribed_by: "", notes: "" });
      fetchMeds();
    } catch {
      // error handled silently
    } finally {
      setSubmitting(false);
    }
  };

  const routeColors: Record<string, string> = {
    oral: "bg-[var(--color-secondary)]",
    topical: "bg-[var(--color-success)]",
    injection: "bg-[var(--color-primary)]",
    inhalation: "bg-[var(--color-tertiary)]",
  };

  const getRouteColor = (route?: string | null) =>
    route ? (routeColors[route.toLowerCase()] || "bg-black") : "bg-black";

  return (
    <div className="dashboard-amber">
      {/* Header Row */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="font-headline text-3xl font-black tracking-tight" style={{ color: "#FCB201" }}>
            Medications
          </h2>
          <p className="text-sm font-bold opacity-60 mt-1" style={{ color: "#FCB201" }}>
            {medications.length} {showAll ? "total" : "active"} medication{medications.length !== 1 ? "s" : ""}
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setShowAll(!showAll)}
            className="px-4 py-2 bg-white text-black font-headline font-black uppercase tracking-widest text-xs brick-shadow rounded cursor-pointer hover:brightness-95"
          >
            {showAll ? "Active Only" : "Show All"}
          </button>
          <button
            onClick={() => setShowAddModal(true)}
            className="px-4 py-2 bg-[var(--color-primary)] text-white font-headline font-black uppercase tracking-widest text-xs brick-shadow rounded cursor-pointer hover:brightness-110 flex items-center gap-2"
          >
            <span className="material-symbols-outlined text-sm" style={{ color: "white" }}>add</span>
            Add Medication
          </button>
        </div>
      </div>

      {/* Medications Grid */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <span className="material-symbols-outlined text-5xl animate-spin" style={{ color: "#FCB201" }}>
            progress_activity
          </span>
        </div>
      ) : medications.length === 0 ? (
        <div className="bg-white brick-shadow rounded-xl p-16 flex flex-col items-center gap-4 studs-light">
          <span className="material-symbols-outlined text-7xl opacity-20" style={{ color: "#FCB201" }}>
            medication
          </span>
          <p className="font-headline font-black text-lg opacity-40" style={{ color: "#FCB201" }}>
            No medications found
          </p>
          <p className="text-xs font-bold opacity-30" style={{ color: "#FCB201" }}>
            Upload a prescription to auto-extract, or add manually
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {medications.map((med) => (
            <div
              key={med.id}
              className="bg-white brick-shadow rounded-xl p-5 flex flex-col gap-3 studs-light lego-card relative"
            >
              {/* Active Badge */}
              <div className="absolute top-3 right-3 mt-4 mr-1 z-10">
                <span
                  className={`text-[9px] font-black uppercase tracking-widest px-2 py-1 rounded ${
                    med.is_active ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-500"
                  }`}
                >
                  {med.is_active ? "Active" : "Inactive"}
                </span>
              </div>

              {/* Icon + Name */}
              <div className="flex items-center gap-3 mt-3">
                <div className={`w-10 h-10 rounded flex items-center justify-center brick-shadow flex-shrink-0 ${getRouteColor(med.route)}`}>
                  <span className="material-symbols-outlined text-white text-sm" style={{ color: "white" }}>
                    medication
                  </span>
                </div>
                <div className="min-w-0">
                  <p className="font-headline font-black text-sm leading-tight text-black truncate">
                    {med.name}
                  </p>
                  {med.generic_name && (
                    <p className="text-[10px] font-bold opacity-50 truncate text-black">
                      {med.generic_name}
                    </p>
                  )}
                </div>
              </div>

              {/* Details Grid */}
              <div className="grid grid-cols-2 gap-2 mt-1">
                {med.dosage && (
                  <div className="bg-black/5 rounded px-2 py-1">
                    <p className="text-[8px] font-black uppercase tracking-widest opacity-50 text-black">Dose</p>
                    <p className="text-xs font-black text-black">{med.dosage}</p>
                  </div>
                )}
                {med.frequency && (
                  <div className="bg-black/5 rounded px-2 py-1">
                    <p className="text-[8px] font-black uppercase tracking-widest opacity-50 text-black">Freq</p>
                    <p className="text-xs font-black text-black truncate">{med.frequency}</p>
                  </div>
                )}
                {med.route && (
                  <div className="bg-black/5 rounded px-2 py-1">
                    <p className="text-[8px] font-black uppercase tracking-widest opacity-50 text-black">Route</p>
                    <p className="text-xs font-black text-black capitalize">{med.route}</p>
                  </div>
                )}
                {med.prescribed_by && (
                  <div className="bg-black/5 rounded px-2 py-1">
                    <p className="text-[8px] font-black uppercase tracking-widest opacity-50 text-black">Doctor</p>
                    <p className="text-xs font-black text-black truncate">{med.prescribed_by}</p>
                  </div>
                )}
              </div>

              {/* Source tag */}
              {med.source_record_id && (
                <div className="flex items-center gap-1">
                  <span className="material-symbols-outlined text-xs opacity-40" style={{ color: "#FCB201" }}>
                    smart_toy
                  </span>
                  <span className="text-[9px] font-bold opacity-40" style={{ color: "#FCB201" }}>
                    AI-extracted
                  </span>
                </div>
              )}

              {/* Start date */}
              {med.start_date && (
                <p className="text-[9px] font-bold opacity-40 text-black">
                  Started {new Date(med.start_date).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })}
                </p>
              )}

              {/* Action Row */}
              <div className="flex gap-2 mt-1 pt-2 border-t border-black/10">
                <button
                  onClick={async (e) => { e.stopPropagation(); await medicationsApi.update(med.id, { is_active: !med.is_active }); fetchMeds(); }}
                  className={`flex-1 py-1.5 rounded text-[9px] font-black uppercase tracking-widest brick-shadow cursor-pointer flex items-center justify-center gap-1 ${med.is_active ? "bg-black/10 text-black hover:bg-black/20" : "bg-[var(--color-success)] text-white hover:brightness-110"}`}
                >
                  <span className="material-symbols-outlined text-[12px]" style={{ color: "inherit" }}>
                    {med.is_active ? "pause_circle" : "play_circle"}
                  </span>
                  {med.is_active ? "Pause" : "Resume"}
                </button>
                <button
                  onClick={async (e) => { e.stopPropagation(); if (confirm("Remove this medication?")) { await medicationsApi.delete(med.id); fetchMeds(); } }}
                  className="w-8 py-1.5 rounded brick-shadow cursor-pointer flex items-center justify-center bg-[var(--color-primary)]/10 hover:bg-[var(--color-primary)] group"
                >
                  <span className="material-symbols-outlined text-[12px] text-[var(--color-primary)] group-hover:text-white" style={{ color: "inherit" }}>delete</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add Medication Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-white brick-shadow-heavy rounded-2xl p-8 w-full max-w-md studs-light mx-4">
            <div className="flex items-center justify-between mb-6 mt-4">
              <h3 className="font-headline font-black text-xl text-black">Add Medication</h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="w-8 h-8 flex items-center justify-center rounded brick-shadow bg-black/5 cursor-pointer"
              >
                <span className="material-symbols-outlined text-sm text-black">close</span>
              </button>
            </div>

            <form onSubmit={handleAdd} className="flex flex-col gap-4">
              <div>
                <label className="text-[9px] font-black uppercase tracking-widest text-black/60 block mb-1">
                  Medication Name *
                </label>
                <input
                  required
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="e.g. Metformin"
                  className="w-full border-2 border-black/20 rounded px-3 py-2 text-sm font-bold text-black bg-black/5 focus:outline-none focus:border-[var(--color-primary)] brick-shadow"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-[9px] font-black uppercase tracking-widest text-black/60 block mb-1">
                    Dosage
                  </label>
                  <input
                    value={form.dosage}
                    onChange={(e) => setForm({ ...form, dosage: e.target.value })}
                    placeholder="500mg"
                    className="w-full border-2 border-black/20 rounded px-3 py-2 text-sm font-bold text-black bg-black/5 focus:outline-none focus:border-[var(--color-primary)] brick-shadow"
                  />
                </div>
                <div>
                  <label className="text-[9px] font-black uppercase tracking-widest text-black/60 block mb-1">
                    Frequency
                  </label>
                  <input
                    value={form.frequency}
                    onChange={(e) => setForm({ ...form, frequency: e.target.value })}
                    placeholder="Twice daily"
                    className="w-full border-2 border-black/20 rounded px-3 py-2 text-sm font-bold text-black bg-black/5 focus:outline-none focus:border-[var(--color-primary)] brick-shadow"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-[9px] font-black uppercase tracking-widest text-black/60 block mb-1">
                    Route
                  </label>
                  <select
                    value={form.route}
                    onChange={(e) => setForm({ ...form, route: e.target.value })}
                    className="w-full border-2 border-black/20 rounded px-3 py-2 text-sm font-bold text-black bg-black/5 focus:outline-none focus:border-[var(--color-primary)] brick-shadow"
                  >
                    <option value="">Select...</option>
                    <option value="oral">Oral</option>
                    <option value="topical">Topical</option>
                    <option value="injection">Injection</option>
                    <option value="inhalation">Inhalation</option>
                    <option value="sublingual">Sublingual</option>
                  </select>
                </div>
                <div>
                  <label className="text-[9px] font-black uppercase tracking-widest text-black/60 block mb-1">
                    Start Date
                  </label>
                  <input
                    type="date"
                    value={form.start_date}
                    onChange={(e) => setForm({ ...form, start_date: e.target.value })}
                    className="w-full border-2 border-black/20 rounded px-3 py-2 text-sm font-bold text-black bg-black/5 focus:outline-none focus:border-[var(--color-primary)] brick-shadow"
                  />
                </div>
              </div>

              <div>
                <label className="text-[9px] font-black uppercase tracking-widest text-black/60 block mb-1">
                  Prescribed By
                </label>
                <input
                  value={form.prescribed_by}
                  onChange={(e) => setForm({ ...form, prescribed_by: e.target.value })}
                  placeholder="Dr. Name"
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
                  <span className="material-symbols-outlined text-sm" style={{ color: "white" }}>add_circle</span>
                )}
                {submitting ? "Saving..." : "Add Medication"}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
