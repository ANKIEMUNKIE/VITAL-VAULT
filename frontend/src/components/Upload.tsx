// src/components/Upload.tsx
"use client";
import React, { useRef, useState, useEffect } from 'react';
import anime from 'animejs';
import { recordsApi, type RecordListItem, type RecordUploadResponse, ApiError } from '@/lib/api';

interface UploadProps {
  onBack: () => void;
}

export default function Upload({ onBack }: UploadProps) {
  const [dragActive, setDragActive] = useState(false);
  const [uploadState, setUploadState] = useState<"IDLE" | "SORTING" | "STRUCTURING" | "VAULTING">("IDLE");
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [recentRecords, setRecentRecords] = useState<RecordListItem[]>([]);
  const [recordsLoading, setRecordsLoading] = useState(true);
  const uploadBoxRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Fetch recent records on mount
  useEffect(() => {
    loadRecords();
  }, []);

  const loadRecords = async () => {
    setRecordsLoading(true);
    try {
      const result = await recordsApi.list({ limit: 5 });
      setRecentRecords(result.data);
    } catch {
      // Silent fail — will show empty state
    } finally {
      setRecordsLoading(false);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
     if(e.target.files && e.target.files[0]) {
        handleFileUpload(e.target.files[0]);
     }
  };

  const handleFileUpload = async (file: File) => {
    if (isUploading) return;
    setUploadError("");
    setIsUploading(true);

    // Animate the upload box
    if(uploadBoxRef.current) {
       anime({
         targets: uploadBoxRef.current,
         scale: [0.95, 1.05, 1],
         rotateZ: [0, -2, 2, 0],
         duration: 600,
         easing: 'easeOutElastic(1, .6)'
       });
    }

    setUploadState("SORTING");

    try {
      // Actual API call to upload
      const result: RecordUploadResponse = await recordsApi.upload(file, file.name);
      
      setUploadState("STRUCTURING");

      // Poll for processing status
      const pollStatus = async () => {
        try {
          const status = await recordsApi.getStatus(result.record_id);
          if (status.status === "COMPLETED" || status.status === "MANUAL_REVIEW") {
            setUploadState("VAULTING");
            setTimeout(() => {
              setUploadState("IDLE");
              setIsUploading(false);
              loadRecords(); // Refresh the records list
            }, 1500);
          } else if (status.status === "FAILED") {
            setUploadState("IDLE");
            setIsUploading(false);
            setUploadError("Processing failed. The record has been saved for manual review.");
            loadRecords();
          } else {
            // Still processing — poll again
            setTimeout(pollStatus, 3000);
          }
        } catch {
          // If polling fails, just show success (record was uploaded)
          setUploadState("VAULTING");
          setTimeout(() => {
            setUploadState("IDLE");
            setIsUploading(false);
            loadRecords();
          }, 1500);
        }
      };

      // Start polling after a delay
      setTimeout(pollStatus, 2000);

    } catch (err) {
      setUploadState("IDLE");
      setIsUploading(false);
      const apiErr = err as ApiError;
      if (apiErr.status === 400) {
        setUploadError("Invalid file type. Please upload PDF, JPG, or PNG files.");
      } else if (apiErr.status === 413) {
        setUploadError("File too large. Maximum size is 50MB.");
      } else {
        setUploadError(apiErr.message || "Upload failed. Please try again.");
      }
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1048576).toFixed(1)} MB`;
  };

  const getStatusColor = (status: string): string => {
    switch (status) {
      case "COMPLETED": return "text-[var(--color-success)]";
      case "PENDING": case "PROCESSING": return "text-[var(--color-secondary)]";
      case "FAILED": case "MANUAL_REVIEW": return "text-[var(--color-primary)]";
      default: return "text-black/60";
    }
  };

  return (
    <div className="max-w-7xl mx-auto pb-20 fade-in-section relative z-30">
      
      {/* Hidden Native Input */}
      <input 
         type="file" 
         ref={fileInputRef} 
         onChange={handleFileSelect}
         className="hidden" 
         accept="image/*,application/pdf,.doc,.docx"
      />

      {/* Header & Back Action */}
      <div className="flex items-center gap-4 mb-12 ml-2">
        <button 
          onClick={onBack}
          className="w-12 h-12 bg-white text-black rounded-full brick-shadow flex items-center justify-center hover:bg-[var(--color-primary)] hover:text-white active:translate-y-[2px] transition-all"
        >
          <span className="material-symbols-outlined">arrow_back</span>
        </button>
        <div>
           <h1 className="font-headline text-4xl font-extrabold tracking-tight text-[var(--color-primary)]">Record Assembly</h1>
           <p className="font-body text-white/70 text-lg">AI-powered digitization: Turning clinical chaos into precision data.</p>
        </div>
      </div>

      {/* Error Banner */}
      {uploadError && (
        <div className="mb-8 bg-red-500 text-white px-6 py-4 rounded-xl font-bold text-sm flex items-center gap-3 brick-shadow">
          <span className="material-symbols-outlined">error</span>
          {uploadError}
          <button onClick={() => setUploadError("")} className="ml-auto opacity-70 hover:opacity-100">
            <span className="material-symbols-outlined text-sm">close</span>
          </button>
        </div>
      )}

      {/* The 4-Step LEGO Baseplate Flow */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 relative">
          {/* Step 1: Input */}
          <div className="relative bg-white text-black rounded-xl p-6 flex flex-col items-center studs-light border-b-8 border-[var(--color-secondary)] shadow-xl transition-all hover:-translate-y-1">
              <div className="absolute -top-3 left-6 bg-[var(--color-secondary)] text-white font-headline font-black px-4 py-1 rounded-full text-[10px] tracking-widest shadow-md">STEP 01</div>
              <div 
                  ref={uploadBoxRef}
                  onDragEnter={handleDrag}
                  onDragLeave={handleDrag}
                  onDragOver={handleDrag}
                  onDrop={handleDrop}
                  onClick={() => !isUploading && fileInputRef.current?.click()}
                  className={`mt-6 mb-8 w-full h-48 bg-[var(--color-inverse-surface)] rounded-xl flex items-center justify-center shadow-inner border-2 border-[var(--color-secondary)]/20 overflow-hidden relative cursor-pointer ${dragActive ? 'bg-[var(--color-primary)]/10 border-[var(--color-primary)] border-dashed' : ''} ${isUploading ? 'pointer-events-none opacity-60' : ''}`}
              >
                  <div className="flex flex-wrap gap-2 justify-center p-4 relative z-20">
                      <div className="w-12 h-8 bg-[var(--color-primary)] rounded shadow-[0_3px_0_0_rgba(0,0,0,0.5)] flex items-center justify-center -rotate-12">
                          <span className="material-symbols-outlined text-white text-sm">description</span>
                      </div>
                      <div className="w-10 h-10 bg-[var(--color-secondary)] rounded shadow-[0_3px_0_0_rgba(0,0,0,0.5)] flex items-center justify-center rotate-6">
                          <span className="material-symbols-outlined text-white text-sm">lab_research</span>
                      </div>
                      <div className="w-14 h-8 bg-[var(--color-tertiary)] rounded shadow-[0_3px_0_0_rgba(0,0,0,0.5)] flex items-center justify-center rotate-12">
                          <span className="material-symbols-outlined text-black text-sm">medication</span>
                      </div>
                  </div>
              </div>
              <h3 className="font-headline font-black text-[var(--color-secondary)] tracking-tight mb-2">SOURCE INTAKE</h3>
              <p className="text-[10px] text-center font-label text-black/60 uppercase tracking-wider font-bold">Upload messy documents or photos</p>
              <button 
                  onClick={(e) => { e.stopPropagation(); if (!isUploading) fileInputRef.current?.click(); }}
                  disabled={isUploading}
                  className="mt-6 w-full py-3 bg-[var(--color-secondary)] text-white rounded-lg font-headline font-extrabold flex items-center justify-center gap-2 brick-shadow hover:brightness-110 active:translate-y-[4px] transition-all text-xs disabled:opacity-50"
              >
                  {isUploading ? (
                    <><span className="material-symbols-outlined text-sm animate-spin">progress_activity</span> UPLOADING...</>
                  ) : (
                    <><span className="material-symbols-outlined text-sm">upload</span> UPLOAD BRICKS</>
                  )}
              </button>
          </div>

          {/* Step 2: Sorting */}
          <div className="relative bg-white text-black rounded-xl p-6 flex flex-col items-center studs-light border-b-8 border-dashed border-[var(--color-surface-container)] shadow-lg opacity-90 transition-all">
              <div className={`absolute -top-3 left-6 text-white font-headline font-black px-4 py-1 rounded-full text-[10px] tracking-widest shadow-md ${uploadState === 'SORTING' ? 'bg-[var(--color-primary)] animate-pulse' : 'bg-gray-400'}`}>STEP 02</div>
              <div className="mt-6 mb-8 w-full h-48 bg-[var(--color-inverse-surface)] rounded-xl flex items-center justify-center border-t-2 border-white relative overflow-hidden">
                  <div className="flex flex-col gap-2 relative z-20">
                      <div className="w-24 h-6 bg-[var(--color-secondary)]/20 rounded-lg animate-pulse flex items-center px-2">
                          <div className="h-2 w-full bg-[var(--color-secondary)] rounded-full"></div>
                      </div>
                      <div className="w-24 h-6 bg-[var(--color-primary)]/20 rounded-lg animate-pulse flex items-center px-2">
                          <div className="h-2 w-2/3 bg-[var(--color-primary)] rounded-full"></div>
                      </div>
                      <div className="w-24 h-6 bg-[var(--color-tertiary)]/40 rounded-lg animate-pulse flex items-center px-2">
                          <div className="h-2 w-1/2 bg-[var(--color-tertiary)] rounded-full"></div>
                      </div>
                  </div>
                  {uploadState === "SORTING" && (
                    <div className="absolute top-0 left-0 w-full h-2 bg-[var(--color-primary)] shadow-[0_0_15px_var(--color-primary)] opacity-50 sliding-scan-beam"></div>
                  )}
              </div>
              <h3 className="font-headline font-black text-black/80 tracking-tight mb-2">NEURAL SORTING</h3>
              <p className="text-[10px] text-center font-label text-black/60 uppercase tracking-wider font-bold">AI identifying record types</p>
              <div className="mt-6 flex items-center gap-2 text-[var(--color-secondary)] font-black text-[10px] uppercase tracking-widest">
                  <span className={`material-symbols-outlined text-sm ${uploadState === 'SORTING' ? 'animate-spin text-[var(--color-primary)]' : 'text-gray-400 opacity-50'}`}>progress_activity</span>
                  {uploadState === 'SORTING' ? 'ANALYZING...' : 'WAITING'}
              </div>
          </div>

          {/* Step 3: Structuring */}
          <div className="relative bg-white text-black rounded-xl p-6 flex flex-col items-center studs-light border-b-8 border-dashed border-[var(--color-surface-container)] shadow-lg opacity-80">
              <div className={`absolute -top-3 left-6 text-white font-headline font-black px-4 py-1 rounded-full text-[10px] tracking-widest shadow-md ${uploadState === 'STRUCTURING' ? 'bg-[var(--color-primary)] animate-pulse' : 'bg-gray-400'}`}>STEP 03</div>
              <div className="mt-6 mb-8 w-full h-48 bg-[var(--color-inverse-surface)] rounded-xl flex items-center justify-center border-t-2 border-white">
                  <div className="flex flex-col -space-y-1">
                      <div className="w-20 h-6 bg-[var(--color-secondary)] rounded-t shadow-[0_2px_0_0_rgba(0,0,0,0.5)] z-30 relative"></div>
                      <div className="w-20 h-6 bg-[var(--color-primary)] rounded shadow-[0_2px_0_0_rgba(0,0,0,0.5)] z-20 relative"></div>
                      <div className="w-20 h-6 bg-[var(--color-tertiary)] rounded-b shadow-[0_2px_0_0_rgba(0,0,0,0.5)] z-10 relative"></div>
                  </div>
              </div>
              <h3 className="font-headline font-black text-black/80 tracking-tight mb-2">DATA ASSEMBLY</h3>
              <p className="text-[10px] text-center font-label text-black/60 uppercase tracking-wider font-bold">Structuring clinical metadata</p>
              <div className={`mt-6 font-black text-[10px] uppercase tracking-widest ${uploadState === 'STRUCTURING' ? 'text-[var(--color-primary)] animate-pulse' : 'text-black/40'}`}>
                 {uploadState === 'STRUCTURING' ? 'ASSEMBLING...' : 'WAITING'}
              </div>
          </div>

          {/* Step 4: Vaulting */}
          <div className="relative bg-white text-black rounded-xl p-6 flex flex-col items-center studs-light border-b-8 border-dashed border-[var(--color-surface-container)] shadow-lg opacity-70">
              <div className={`absolute -top-3 left-6 text-white font-headline font-black px-4 py-1 rounded-full text-[10px] tracking-widest shadow-md ${uploadState === 'VAULTING' ? 'bg-[var(--color-success)] animate-pulse' : 'bg-gray-400'}`}>STEP 04</div>
              <div className="mt-6 mb-8 w-full h-48 bg-[var(--color-inverse-surface)] rounded-xl flex items-center justify-center border-t-2 border-white">
                  <span className={`material-symbols-outlined text-5xl ${uploadState === 'VAULTING' ? 'text-[var(--color-success)] animate-bounce' : 'text-black/20'}`}>lock</span>
              </div>
              <h3 className="font-headline font-black text-black/80 tracking-tight mb-2">VAULT DEPOSIT</h3>
              <p className="text-[10px] text-center font-label text-black/60 uppercase tracking-wider font-bold">Encryption & Final Sync</p>
              <div className={`mt-6 font-black text-[10px] uppercase tracking-widest ${uploadState === 'VAULTING' ? 'text-[var(--color-success)]' : 'text-black/40'}`}>
                 {uploadState === 'VAULTING' ? 'SECURED ✓' : 'LOCKED'}
              </div>
          </div>
      </div>

      {/* Bento Grid Insights (Real Records from API) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12 bg-white p-8 rounded-xl brick-shadow studs-light relative">
          
          {/* Left: Processing Queue — REAL DATA */}
          <div className="md:col-span-2">
              <div className="flex justify-between items-center mb-6">
                  <h2 className="font-headline font-black text-2xl tracking-tight text-black">Data Pipeline</h2>
                  <span className="px-3 py-1 bg-[var(--color-secondary)] text-white text-[10px] font-black rounded uppercase tracking-widest brick-shadow">
                    {recordsLoading ? '...' : `${recentRecords.length} Records`}
                  </span>
              </div>
              <div className="space-y-4">
                  {recordsLoading ? (
                    <div className="flex items-center justify-center py-12 text-black/40">
                      <span className="material-symbols-outlined animate-spin mr-2">progress_activity</span>
                      Loading records...
                    </div>
                  ) : recentRecords.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-12 text-black/40">
                      <span className="material-symbols-outlined text-4xl mb-2">folder_open</span>
                      <p className="font-bold text-sm">No records yet. Upload your first document above!</p>
                    </div>
                  ) : (
                    recentRecords.map((record) => (
                      <div key={record.id} className="flex items-center p-4 bg-[var(--color-inverse-surface)] rounded-lg border-l-8 border-[var(--color-secondary)]">
                          <div className="mr-4">
                            <span className="material-symbols-outlined text-[var(--color-secondary)]">
                              {record.processing_status === 'COMPLETED' ? 'check_circle' : 'picture_as_pdf'}
                            </span>
                          </div>
                          <div className="flex-grow">
                              <div className="font-black text-sm text-black">{record.title}</div>
                              <div className="text-[10px] text-black/60 font-bold uppercase tracking-widest">
                                {record.category?.label || 'Document'} • {formatFileSize(record.file_size_bytes)}
                              </div>
                          </div>
                          <div className="flex items-center gap-4">
                              <div className="text-right">
                                  <div className={`text-[10px] font-black tracking-widest ${getStatusColor(record.processing_status)}`}>
                                    {record.processing_status}
                                  </div>
                                  <div className="text-[9px] text-black/40 font-bold mt-1">
                                    {new Date(record.created_at).toLocaleDateString()}
                                  </div>
                              </div>
                          </div>
                      </div>
                    ))
                  )}
              </div>
          </div>

          {/* Right: Vault Engine Stats */}
          <div className="flex flex-col gap-6">
              <div className="bg-[var(--color-secondary)] text-white p-6 rounded-lg brick-shadow flex flex-col justify-between h-full">
                  <div>
                      <h3 className="font-headline font-black text-xl mb-4 flex items-center gap-2">
                          <span className="material-symbols-outlined">precision_manufacturing</span> VAULT ENGINE
                      </h3>
                      <div className="space-y-4 font-bold">
                          <div className="flex justify-between items-end border-b border-white/20 pb-2">
                              <span className="text-[10px] opacity-70 uppercase tracking-widest">Records</span>
                              <span className="font-black text-2xl leading-none text-white">{recentRecords.length}</span>
                          </div>
                          <div className="flex justify-between items-end border-b border-white/20 pb-2">
                              <span className="text-[10px] opacity-70 uppercase tracking-widest">Processed</span>
                              <span className="font-black text-2xl leading-none text-white">
                                {recentRecords.filter(r => r.processing_status === 'COMPLETED').length}
                              </span>
                          </div>
                      </div>
                  </div>
                  <div className="mt-8 flex items-center gap-2 bg-white/10 p-3 rounded-lg border border-white/10">
                      <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                      <span className="text-[10px] font-black uppercase tracking-widest">System Nominal • Modules Live</span>
                  </div>
              </div>
          </div>

      </div>

      <style dangerouslySetInnerHTML={{__html: `
        @keyframes scanBeam {
          0% { transform: translateY(-50px); opacity: 0; }
          50% { opacity: 1; }
          100% { transform: translateY(200px); opacity: 0; }
        }
        .sliding-scan-beam {
          animation: scanBeam 2s infinite linear;
        }
      `}} />
    </div>
  );
}
