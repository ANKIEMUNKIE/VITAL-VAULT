"use client";

import React, { useState, useEffect, useRef } from "react";
import { recordsApi, type RecordListItem, type RecordDetail } from "@/lib/api";

const CATEGORIES = [
  { slug: "", label: "All Records", icon: "folder_open" },
  { slug: "lab_report", label: "Lab Reports", icon: "science" },
  { slug: "prescription", label: "Prescriptions", icon: "medication" },
  { slug: "imaging", label: "Imaging", icon: "radiology" },
  { slug: "discharge", label: "Discharge", icon: "local_hospital" },
  { slug: "vaccination", label: "Vaccination", icon: "vaccines" },
  { slug: "insurance", label: "Insurance", icon: "shield" },
  { slug: "other", label: "Other", icon: "description" },
];

const STATUS_COLORS: Record<string, { dot: string; label: string }> = {
  PENDING: { dot: "bg-yellow-400", label: "Queued" },
  OCR_PROCESSING: { dot: "bg-blue-400 animate-pulse", label: "Reading..." },
  AI_PROCESSING: { dot: "bg-purple-400 animate-pulse", label: "Analyzing..." },
  PROCESSED: { dot: "bg-green-500", label: "Done" },
  FAILED: { dot: "bg-red-500", label: "Failed" },
  MANUAL_REVIEW: { dot: "bg-orange-400", label: "Review" },
};

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function Vault() {
  const [records, setRecords] = useState<RecordListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState("");
  const [selectedRecord, setSelectedRecord] = useState<RecordDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [pollingIds, setPollingIds] = useState<Set<string>>(new Set());
  const pollRef = useRef<Record<string, ReturnType<typeof setInterval>>>({});

  const fetchRecords = async () => {
    try {
      setLoading(true);
      const res = await recordsApi.list({
        category: selectedCategory || undefined,
        limit: 50,
      });
      setRecords(res.data || []);
    } catch {
      setRecords([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchRecords(); }, [selectedCategory]);

  // Poll status for records that are still processing
  useEffect(() => {
    const pending = records.filter(
      (r) => ["PENDING", "OCR_PROCESSING", "AI_PROCESSING"].includes(r.processing_status)
    );

    pending.forEach((r) => {
      if (!pollRef.current[r.id]) {
        pollRef.current[r.id] = setInterval(async () => {
          try {
            const status = await recordsApi.getStatus(r.id);
            if (!["PENDING", "OCR_PROCESSING", "AI_PROCESSING"].includes(status.status)) {
              clearInterval(pollRef.current[r.id]);
              delete pollRef.current[r.id];
              fetchRecords(); // refresh the list
            } else {
              // Update status inline
              setRecords((prev) =>
                prev.map((rec) =>
                  rec.id === r.id ? { ...rec, processing_status: status.status } : rec
                )
              );
            }
          } catch { /* ignore */ }
        }, 3000);
      }
    });

    // Cleanup intervals for records no longer pending
    Object.keys(pollRef.current).forEach((id) => {
      if (!pending.find((r) => r.id === id)) {
        clearInterval(pollRef.current[id]);
        delete pollRef.current[id];
      }
    });

    return () => {
      Object.values(pollRef.current).forEach(clearInterval);
    };
  }, [records]);

  const openDetail = async (record: RecordListItem) => {
    setDetailLoading(true);
    setSelectedRecord(null);
    try {
      const detail = await recordsApi.get(record.id);
      setSelectedRecord(detail);
    } catch {
      setSelectedRecord(null);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this record? This cannot be undone.")) return;
    try {
      await recordsApi.delete(id);
      setSelectedRecord(null);
      fetchRecords();
    } catch { /* silent */ }
  };

  return (
    <div className="dashboard-amber">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="font-headline text-3xl font-black tracking-tight" style={{ color: "#FCB201" }}>
            Medical Vault
          </h2>
          <p className="text-sm font-bold opacity-60 mt-1" style={{ color: "#FCB201" }}>
            {records.length} record{records.length !== 1 ? "s" : ""}
            {selectedCategory ? ` · ${CATEGORIES.find((c) => c.slug === selectedCategory)?.label}` : ""}
          </p>
        </div>
      </div>

      {/* Category Filter */}
      <div className="flex gap-2 mb-8 flex-wrap">
        {CATEGORIES.map((cat) => (
          <button
            key={cat.slug}
            onClick={() => setSelectedCategory(cat.slug)}
            className={`flex items-center gap-2 px-3 py-2 rounded font-headline font-black uppercase tracking-widest text-[9px] brick-shadow cursor-pointer ${
              selectedCategory === cat.slug
                ? "bg-[var(--color-primary)] text-white"
                : "bg-white text-black hover:brightness-95"
            }`}
          >
            <span className="material-symbols-outlined text-[14px]" style={{ color: "inherit" }}>
              {cat.icon}
            </span>
            {cat.label}
          </button>
        ))}
      </div>

      <div className="flex gap-6">
        {/* Records List */}
        <div className={`flex flex-col gap-3 ${selectedRecord ? "w-1/2" : "w-full"}`}>
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <span className="material-symbols-outlined text-5xl animate-spin" style={{ color: "#FCB201" }}>
                progress_activity
              </span>
            </div>
          ) : records.length === 0 ? (
            <div className="bg-white brick-shadow rounded-xl p-16 flex flex-col items-center gap-4 studs-light">
              <span className="material-symbols-outlined text-7xl opacity-20" style={{ color: "#FCB201" }}>
                folder_open
              </span>
              <p className="font-headline font-black text-lg opacity-40" style={{ color: "#FCB201" }}>
                No records found
              </p>
              <p className="text-xs font-bold opacity-30" style={{ color: "#FCB201" }}>
                Upload your medical documents to get started
              </p>
            </div>
          ) : (
            records.map((record) => {
              const statusInfo = STATUS_COLORS[record.processing_status] || STATUS_COLORS.PENDING;
              const isSelected = selectedRecord?.id === record.id;
              return (
                <div
                  key={record.id}
                  onClick={() => openDetail(record)}
                  className={`bg-white brick-shadow rounded-xl p-4 flex items-center gap-4 studs-light lego-card cursor-pointer ${
                    isSelected ? "ring-2 ring-[var(--color-primary)] ring-offset-2" : "hover:brightness-98"
                  }`}
                >
                  {/* File Icon */}
                  <div className="w-12 h-12 bg-[var(--color-surface-container)] rounded-lg flex items-center justify-center brick-shadow flex-shrink-0">
                    <span className="material-symbols-outlined text-white text-lg" style={{ color: "white" }}>
                      {record.mime_type?.includes("pdf") ? "picture_as_pdf" : "image"}
                    </span>
                  </div>

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <p className="font-headline font-black text-sm text-black truncate">{record.title}</p>
                    <div className="flex items-center gap-3 mt-1 flex-wrap">
                      {record.document_date && (
                        <span className="text-[9px] font-bold text-black/40">
                          {new Date(record.document_date).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })}
                        </span>
                      )}
                      <span className="text-[9px] font-bold text-black/30">
                        {formatBytes(record.file_size_bytes)}
                      </span>
                    </div>
                    {record.tags && record.tags.length > 0 && (
                      <div className="flex gap-1 mt-1 flex-wrap">
                        {record.tags.map((tag) => (
                          <span key={tag} className="text-[8px] font-black uppercase tracking-widest px-1.5 py-0.5 rounded bg-black/5 text-black/50">
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Status */}
                  <div className="flex flex-col items-end gap-2 flex-shrink-0">
                    <div className="flex items-center gap-1.5">
                      <div className={`w-2 h-2 rounded-full ${statusInfo.dot}`} />
                      <span className="text-[8px] font-black uppercase tracking-widest text-black/50">
                        {statusInfo.label}
                      </span>
                    </div>
                    <span className="text-[8px] font-bold text-black/30">
                      {new Date(record.created_at).toLocaleDateString("en-IN", { day: "numeric", month: "short" })}
                    </span>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Detail Panel */}
        {(selectedRecord || detailLoading) && (
          <div className="w-1/2 flex-shrink-0">
            <div className="bg-white brick-shadow-heavy rounded-xl p-6 studs-light sticky top-4">
              {detailLoading ? (
                <div className="flex items-center justify-center h-48">
                  <span className="material-symbols-outlined text-4xl animate-spin" style={{ color: "#FCB201" }}>
                    progress_activity
                  </span>
                </div>
              ) : selectedRecord ? (
                <>
                  <div className="flex items-start justify-between mb-5 mt-4">
                    <div className="flex-1 min-w-0">
                      <p className="font-headline font-black text-lg text-black leading-tight">{selectedRecord.title}</p>
                      {selectedRecord.document_date && (
                        <p className="text-xs font-bold text-black/40 mt-1">
                          {new Date(selectedRecord.document_date).toLocaleDateString("en-IN", { day: "numeric", month: "long", year: "numeric" })}
                        </p>
                      )}
                    </div>
                    <button
                      onClick={() => setSelectedRecord(null)}
                      className="w-8 h-8 flex items-center justify-center rounded brick-shadow bg-black/5 cursor-pointer flex-shrink-0 ml-2"
                    >
                      <span className="material-symbols-outlined text-sm text-black">close</span>
                    </button>
                  </div>

                  {/* Processing Status */}
                  <div className="flex items-center gap-2 mb-5">
                    <div className={`w-2.5 h-2.5 rounded-full ${STATUS_COLORS[selectedRecord.processing_status]?.dot || "bg-gray-400"}`} />
                    <span className="text-xs font-black uppercase tracking-widest text-black/50">
                      {STATUS_COLORS[selectedRecord.processing_status]?.label || selectedRecord.processing_status}
                    </span>
                  </div>

                  {/* AI Extraction Results */}
                  {selectedRecord.extraction && (
                    <div className="mb-5 space-y-3">
                      <p className="text-[10px] font-black uppercase tracking-widest text-black/40 flex items-center gap-1">
                        <span className="material-symbols-outlined text-[14px]" style={{ color: "inherit" }}>smart_toy</span>
                        AI Extraction
                      </p>

                      {selectedRecord.extraction.diagnosed_conditions?.length ? (
                        <div className="bg-[var(--color-primary)]/5 rounded-lg p-3">
                          <p className="text-[8px] font-black uppercase tracking-widest text-[var(--color-primary)] mb-1">Conditions</p>
                          <div className="flex flex-wrap gap-1">
                            {selectedRecord.extraction.diagnosed_conditions.map((cond, i) => (
                              <span key={i} className="text-[9px] font-black px-2 py-0.5 rounded bg-[var(--color-primary)]/10 text-[var(--color-primary)]">
                                {cond}
                              </span>
                            ))}
                          </div>
                        </div>
                      ) : null}

                      {selectedRecord.extraction.extracted_medications?.length ? (
                        <div className="bg-[var(--color-secondary)]/5 rounded-lg p-3">
                          <p className="text-[8px] font-black uppercase tracking-widest text-[var(--color-secondary)] mb-2">Medications</p>
                          <div className="space-y-1">
                            {(selectedRecord.extraction.extracted_medications as Record<string, string>[]).map((med, i) => (
                              <div key={i} className="flex items-center gap-2">
                                <span className="w-1 h-1 rounded-full bg-[var(--color-secondary)] flex-shrink-0" />
                                <p className="text-xs font-bold text-black">
                                  {med.name} {med.dosage && `— ${med.dosage}`} {med.frequency && `(${med.frequency})`}
                                </p>
                              </div>
                            ))}
                          </div>
                        </div>
                      ) : null}

                      {selectedRecord.extraction.ai_summary && (
                        <div className="bg-black/5 rounded-lg p-3">
                          <p className="text-[8px] font-black uppercase tracking-widest text-black/40 mb-1">AI Summary</p>
                          <p className="text-xs font-bold text-black leading-relaxed">{selectedRecord.extraction.ai_summary}</p>
                        </div>
                      )}

                      {selectedRecord.extraction.confidence_score != null && (
                        <div className="flex items-center gap-2">
                          <div className="flex-1 h-2 bg-black/10 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-[var(--color-success)] rounded-full"
                              style={{ width: `${(selectedRecord.extraction.confidence_score * 100).toFixed(0)}%` }}
                            />
                          </div>
                          <span className="text-[9px] font-black text-black/40">
                            {(selectedRecord.extraction.confidence_score * 100).toFixed(0)}% confidence
                          </span>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Actions */}
                  <div className="flex gap-3">
                    {selectedRecord.download_url && (
                      <a
                        href={selectedRecord.download_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex-1 bg-[var(--color-secondary)] text-white font-headline font-black uppercase tracking-widest text-[9px] py-2.5 rounded brick-shadow flex items-center justify-center gap-2 hover:brightness-110 cursor-pointer no-underline"
                      >
                        <span className="material-symbols-outlined text-sm" style={{ color: "white" }}>download</span>
                        Download
                      </a>
                    )}
                    <button
                      onClick={() => handleDelete(selectedRecord.id)}
                      className="flex-1 bg-[var(--color-primary)]/10 text-[var(--color-primary)] font-headline font-black uppercase tracking-widest text-[9px] py-2.5 rounded brick-shadow flex items-center justify-center gap-2 hover:bg-[var(--color-primary)] hover:text-white cursor-pointer"
                    >
                      <span className="material-symbols-outlined text-sm" style={{ color: "inherit" }}>delete</span>
                      Delete
                    </button>
                  </div>
                </>
              ) : null}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
