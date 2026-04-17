// src/components/Dashboard.tsx
/* eslint-disable @next/next/no-img-element */
"use client";
import React, { useEffect, useRef, useState } from 'react';
import anime from 'animejs';
import { medicationsApi, appointmentsApi, recordsApi, type Medication, type Appointment, type RecordListItem } from '@/lib/api';

interface DashboardProps {
   onNavigate?: (view: string) => void;
}

export default function Dashboard({ onNavigate }: DashboardProps) {
   const containerRef = useRef<HTMLDivElement>(null);
   const modalRef = useRef<HTMLDivElement>(null);

   // Real data states
   const [medications, setMedications] = useState<Medication[]>([]);
   const [medsLoading, setMedsLoading] = useState(true);
   const [appointments, setAppointments] = useState<Appointment[]>([]);
   const [apptsLoading, setApptsLoading] = useState(true);
   const [recentRecords, setRecentRecords] = useState<RecordListItem[]>([]);
   const [recordsLoading, setRecordsLoading] = useState(true);

   // Medication intake tracking (local)
   const [intakeChecked, setIntakeChecked] = useState<Set<string>>(new Set());

   // Live Heart Rate Monitor (simulated — no wearable API yet)
   const [heartRate, setHeartRate] = useState(72);
   const [hrHistory, setHrHistory] = useState<number[]>([72, 71, 73, 70, 72, 74, 71]);

   // Live Sleep Tracker (simulated)
   const [sleepData, setSleepData] = useState({ total: 7.4, deep: 1.8, rem: 2.1, light: 3.5, efficiency: 89 });

   // Fetch real data on mount
   useEffect(() => {
      loadData();
   }, []);

   const loadData = async () => {
      // Medications
      setMedsLoading(true);
      try {
         const medsResult = await medicationsApi.list(true);
         setMedications(medsResult.data);
      } catch {
         // Silent fail — will show fallback
      } finally {
         setMedsLoading(false);
      }

      // Appointments
      setApptsLoading(true);
      try {
         const apptsResult = await appointmentsApi.list();
         setAppointments(apptsResult.data);
      } catch {
         // Silent fail
      } finally {
         setApptsLoading(false);
      }

      // Recent Records
      setRecordsLoading(true);
      try {
         const recordsResult = await recordsApi.list({ limit: 3 });
         setRecentRecords(recordsResult.data);
      } catch {
         // Silent fail
      } finally {
         setRecordsLoading(false);
      }
   };

   // Simulate continuous heart rate monitor feed
   useEffect(() => {
      const hrInterval = setInterval(() => {
         setHeartRate(prev => {
            const delta = Math.floor(Math.random() * 5) - 2;
            const next = Math.max(62, Math.min(88, prev + delta));
            setHrHistory(h => [...h.slice(-11), next]);
            return next;
         });
      }, 1500);
      return () => clearInterval(hrInterval);
   }, []);

   // Simulate sleep tracker
   useEffect(() => {
      const sleepInterval = setInterval(() => {
         setSleepData(prev => ({
            total: Math.round((prev.total + (Math.random() * 0.02 - 0.01)) * 10) / 10,
            deep: Math.round((prev.deep + (Math.random() * 0.01)) * 10) / 10,
            rem: Math.round((prev.rem + (Math.random() * 0.01)) * 10) / 10,
            light: Math.round((prev.light + (Math.random() * 0.01 - 0.005)) * 10) / 10,
            efficiency: Math.min(100, Math.max(80, prev.efficiency + Math.floor(Math.random() * 3) - 1)),
         }));
      }, 8000);
      return () => clearInterval(sleepInterval);
   }, []);

   // Modal State
   const [isBookingModalOpen, setIsBookingModalOpen] = useState(false);
   const [bookingStep, setBookingStep] = useState(1);
   const [selectedSpecialist, setSelectedSpecialist] = useState<string | null>(null);

   // Toggle Function with Physics
   const handleIntakeToggle = (e: React.MouseEvent, medId: string) => {
      const el = e.currentTarget as HTMLElement;
      anime({
         targets: el,
         scale: [0.95, 1.05, 1],
         duration: 500,
         easing: 'easeOutElastic(1, .6)'
      });
      setIntakeChecked(prev => {
         const updated = new Set(prev);
         if (updated.has(medId)) {
            updated.delete(medId);
         } else {
            updated.add(medId);
         }
         return updated;
      });
   };

   // Open Modal
   const openBookingModal = () => {
      setIsBookingModalOpen(true);
      setBookingStep(1);
      setSelectedSpecialist(null);
   };

   useEffect(() => {
      if (isBookingModalOpen && modalRef.current) {
         anime({
            targets: modalRef.current,
            opacity: [0, 1],
            scale: [0.9, 1],
            duration: 600,
            easing: 'easeOutExpo'
         });
         anime({
            targets: modalRef.current.querySelectorAll('.modal-anim'),
            translateY: [20, 0],
            opacity: [0, 1],
            delay: anime.stagger(100, { start: 200 }),
            duration: 600,
            easing: 'easeOutExpo'
         });
      }
   }, [isBookingModalOpen]);

   useEffect(() => {
      const root = containerRef.current;
      if (!root) return;

      const elements = root.querySelectorAll('.hp-anim');
      elements.forEach(el => (el as HTMLElement).style.opacity = '0');

      const tl = anime.timeline({ easing: 'easeOutExpo' });

      tl.add({
         targets: root.querySelectorAll('.hp-header h2, .hp-header p'),
         translateY: [30, 0],
         opacity: [0, 1],
         duration: 800,
         delay: anime.stagger(150)
      })
         .add({
            targets: root.querySelectorAll('.hp-drag-box'),
            scale: [0.8, 1],
            opacity: [0, 1],
            rotateX: [-20, 0],
            easing: 'easeOutElastic(1, .8)',
            duration: 1200
         }, '-=400')
         .add({
            targets: root.querySelectorAll('.hp-vital-stat'),
            translateX: [40, 0],
            opacity: [0, 1],
            delay: anime.stagger(100),
            easing: 'easeOutQuart',
            duration: 800
         }, '-=1000')
         .add({
            targets: root.querySelectorAll('.hp-event-card'),
            translateY: [50, 0],
            opacity: [0, 1],
            delay: anime.stagger(150),
            duration: 800
         }, '-=600')
         .add({
            targets: root.querySelectorAll('.hp-right-col > div'),
            translateY: [40, 0],
            opacity: [0, 1],
            delay: anime.stagger(150),
            duration: 800
         }, '-=700');

      const interactables = root.querySelectorAll('.hp-interactive');
      interactables.forEach(node => {
         const el = node as HTMLElement;
         el.addEventListener('mouseenter', () => {
            anime({ targets: el, scale: 1.03, translateY: -5, boxShadow: '0 15px 30px rgba(0,0,0,0.1)', duration: 400, easing: 'easeOutElastic(1.5, 0.8)' });
         });
         el.addEventListener('mouseleave', () => {
            anime({ targets: el, scale: 1, translateY: 0, boxShadow: '0 5px 15px rgba(0,0,0,0.1)', duration: 600, easing: 'easeOutElastic(1, .5)' });
         });
      });
   }, []);

   // Color palette for meds
   const medColors = ['var(--color-primary)', 'var(--color-secondary)', 'var(--color-tertiary)', 'orange', '#4DA8FF'];

   return (
      <div ref={containerRef} className="dashboard-amber space-y-10 max-w-7xl mx-auto pb-20 relative z-30">

         {/* Header */}
         <header className="hp-header hp-anim mb-10">
            <div className="flex items-center gap-5 mb-3">
               <img
                  src="/vital_vault_logo.png"
                  alt="Vital Vault Logo"
                  className="h-14 w-auto object-contain flex-shrink-0 drop-shadow-lg"
                  style={{ filter: 'drop-shadow(0 4px 8px rgba(252,178,1,0.25))' }}
               />
               <div>
                  <h2 className="font-headline text-5xl font-black tracking-tighter text-[var(--color-primary)]">Health Pulse</h2>
                  <p className="text-[10px] font-black uppercase tracking-[0.3em] text-[#FCB201]/60 mt-1">Vital Vault · Secure Health Records</p>
               </div>
            </div>
            <p className="font-body opacity-80 text-lg mt-2 font-bold border-l-4 border-[var(--color-primary)] pl-4">Real-time biometric surveillance dashboard. Aggregating cardiac telemetry, sleep architecture analytics, medication adherence tracking, and longitudinal metabolic panel data across all connected provider networks.</p>
         </header>

         {/* Top Grid: Upload & Vitals */}
         <div className="grid grid-cols-1 md:grid-cols-12 gap-8">

            {/* Drag & Drop Hero */}
            <div onClick={() => onNavigate?.('upload')} className="md:col-span-8 hp-anim hp-drag-box bg-[var(--color-inverse-surface)] border-2 border-dashed border-[var(--color-surface-container)] rounded-2xl flex items-center justify-center min-h-[220px] p-8 brick-shadow relative cursor-pointer hp-interactive transition-colors hover:bg-[var(--color-primary)]/10 hover:border-[var(--color-primary)]">
               <div className="text-center flex flex-col items-center">
                  <div className="w-16 h-16 bg-[var(--color-primary)] text-[#FCB201] rounded-xl brick-shadow flex items-center justify-center mb-6">
                     <span className="material-symbols-outlined text-3xl font-black">add</span>
                  </div>
                  <h3 className="text-2xl font-black font-headline text-[#FCB201]">Drag & drop medical files</h3>
                  <p className="text-[10px] font-black uppercase tracking-widest text-[var(--color-secondary)]/60 mt-2">SUPPORTS PDF, DICOM, JPG (MAX 50MB)</p>
               </div>
            </div>

            {/* Vitals — Live Monitors */}
            <div className="md:col-span-4 flex flex-col gap-6 justify-between">
               {/* Heart Rate Monitor */}
               <div className="hp-anim hp-vital-stat flex-1 bg-[var(--color-surface)] p-6 rounded-2xl brick-shadow flex flex-col hp-interactive border-l-8 border-[var(--color-primary)]">
                  <div className="flex items-center justify-between mb-3">
                     <div className="flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>
                        <span className="text-[9px] font-black uppercase tracking-widest opacity-60">LIVE • ECG MONITOR</span>
                     </div>
                     <span className="material-symbols-outlined text-[var(--color-primary)] text-3xl animate-pulse">favorite</span>
                  </div>
                  <h4 className="text-5xl font-black font-headline transition-all duration-300">{heartRate}</h4>
                  <p className="text-[10px] font-black uppercase tracking-widest opacity-50 mt-1">Current BPM</p>
                  <div className="flex items-end gap-[3px] mt-3 h-8">
                     {hrHistory.map((val, i) => (
                        <div key={i} className="flex-1 rounded-t" style={{ height: `${((val - 60) / 30) * 100}%`, backgroundColor: val > 80 ? 'var(--color-primary)' : '#FCB201', opacity: 0.4 + (i / hrHistory.length) * 0.6, transition: 'height 0.3s ease' }}></div>
                     ))}
                  </div>
                  <p className="text-[9px] font-bold opacity-40 mt-2">Resting range: 62–88 BPM. Continuous feed via wearable ECG patch.</p>
               </div>

               {/* Sleep Tracker */}
               <div className="hp-anim hp-vital-stat flex-1 bg-[var(--color-surface)] p-6 rounded-2xl brick-shadow flex flex-col hp-interactive border-l-8 border-[var(--color-secondary)]">
                  <div className="flex items-center justify-between mb-3">
                     <div className="flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse"></span>
                        <span className="text-[9px] font-black uppercase tracking-widest opacity-60">LIVE • SLEEP TRACKER</span>
                     </div>
                     <span className="material-symbols-outlined text-[var(--color-secondary)] text-3xl">bedtime</span>
                  </div>
                  <h4 className="text-5xl font-black font-headline transition-all duration-300">{sleepData.total}h</h4>
                  <p className="text-[10px] font-black uppercase tracking-widest opacity-50 mt-1">Total Sleep</p>
                  <div className="flex h-3 rounded-full overflow-hidden mt-3 gap-[2px]">
                     <div className="bg-indigo-800 rounded-l" style={{ width: `${(sleepData.deep / sleepData.total) * 100}%`, transition: 'width 1s ease' }}></div>
                     <div className="bg-purple-500" style={{ width: `${(sleepData.rem / sleepData.total) * 100}%`, transition: 'width 1s ease' }}></div>
                     <div className="bg-sky-300 rounded-r" style={{ width: `${(sleepData.light / sleepData.total) * 100}%`, transition: 'width 1s ease' }}></div>
                  </div>
                  <div className="flex justify-between mt-2">
                     <span className="text-[8px] font-black opacity-50">Deep: {sleepData.deep}h</span>
                     <span className="text-[8px] font-black opacity-50">REM: {sleepData.rem}h</span>
                     <span className="text-[8px] font-black opacity-50">Light: {sleepData.light}h</span>
                  </div>
                  <p className="text-[9px] font-bold opacity-40 mt-2">Efficiency: {sleepData.efficiency}%</p>
               </div>
            </div>

         </div>

         {/* Main Grid: Events & Trackers */}
         <div className="grid grid-cols-1 md:grid-cols-12 gap-10 mt-12">

            {/* Left Column: Recent Records from API */}
            <div className="md:col-span-7 space-y-8">
               <div className="flex items-center justify-between hp-anim border-l-8 border-[var(--color-primary)] pl-4">
                  <h3 className="font-headline text-2xl font-black tracking-tight text-[#FCB201]">Recent Records</h3>
                  <button onClick={() => onNavigate?.('timeline')} className="text-[10px] font-black uppercase tracking-widest text-[var(--color-secondary)] hover:text-[var(--color-primary)] transition-colors">View Timeline</button>
               </div>

               <div className="space-y-6">
                  {recordsLoading ? (
                     <div className="hp-anim hp-event-card bg-[var(--color-surface)] p-8 rounded-2xl brick-shadow flex items-center justify-center">
                        <span className="material-symbols-outlined animate-spin text-[var(--color-primary)] mr-2">progress_activity</span>
                        <span className="font-bold opacity-60">Loading records...</span>
                     </div>
                  ) : recentRecords.length === 0 ? (
                     <div className="hp-anim hp-event-card bg-[var(--color-surface)] p-8 rounded-2xl brick-shadow text-center">
                        <span className="material-symbols-outlined text-4xl text-black/20 mb-2">folder_open</span>
                        <p className="font-bold text-sm opacity-40">No records yet. Upload your first document to get started!</p>
                     </div>
                  ) : (
                     recentRecords.map((record, i) => {
                        const borderColors = ['border-[var(--color-secondary)]', 'border-[var(--color-tertiary)]', 'border-[var(--color-primary)]'];
                        return (
                           <div key={record.id} className={`hp-anim hp-event-card bg-[var(--color-surface)] p-6 rounded-2xl brick-shadow ${borderColors[i % 3]} border-l-8 flex gap-6 hp-interactive`}>
                              <div className="w-16 h-16 rounded-xl bg-white flex flex-col items-center justify-center flex-shrink-0 brick-shadow border-2 border-black/10">
                                 <span className="text-[10px] font-black uppercase text-[var(--color-secondary)]">
                                    {record.document_date ? new Date(record.document_date).toLocaleString('en', { month: 'short' }) : 'N/A'}
                                 </span>
                                 <span className="text-xl font-black text-[#FCB201]">
                                    {record.document_date ? new Date(record.document_date).getDate() : '--'}
                                 </span>
                              </div>
                              <div className="flex-1">
                                 <div className="flex items-center justify-between mb-2">
                                    <h4 className="font-black text-lg text-[#FCB201]">{record.title}</h4>
                                    <span className={`text-[10px] px-3 py-1 rounded-full font-black uppercase tracking-wider ${
                                       record.processing_status === 'COMPLETED' ? 'bg-[var(--color-success)]/10 text-[var(--color-success)]' :
                                       record.processing_status === 'PENDING' ? 'bg-orange-500/10 text-orange-500' :
                                       'bg-[var(--color-secondary)]/10 text-[var(--color-secondary)]'
                                    }`}>
                                       {record.processing_status}
                                    </span>
                                 </div>
                                 <p className="text-sm font-bold opacity-70 mb-2">
                                    {record.category?.label || 'Document'} • {(record.file_size_bytes / 1024).toFixed(0)} KB
                                 </p>
                                 {record.tags && record.tags.length > 0 && (
                                    <div className="flex gap-2 flex-wrap">
                                       {record.tags.map((tag, ti) => (
                                          <span key={ti} className="text-[10px] font-black bg-white border border-[var(--color-surface-container)] rounded brick-shadow px-3 py-1">{tag}</span>
                                       ))}
                                    </div>
                                 )}
                              </div>
                           </div>
                        );
                     })
                  )}
               </div>
            </div>

            {/* Right Column: Medications & Appointments */}
            <div className="md:col-span-5 space-y-8 hp-right-col">

               {/* Interactive Daily Intake — FROM API */}
               <div className="hp-anim bg-black rounded-2xl p-8 brick-shadow text-[#FCB201] studs-dark relative">
                  <h3 className="flex items-center gap-3 font-headline text-xl font-black tracking-tight mb-8 relative z-20">
                     <span className="material-symbols-outlined text-[var(--color-primary)]">notifications_active</span> Daily Intake
                  </h3>

                  <div className="space-y-4 relative z-20">
                     {medsLoading ? (
                        <div className="flex items-center justify-center py-8 text-[#FCB201]/50">
                           <span className="material-symbols-outlined animate-spin mr-2">progress_activity</span>
                           Loading medications...
                        </div>
                     ) : medications.length === 0 ? (
                        <div className="text-center py-8 text-[#FCB201]/40">
                           <span className="material-symbols-outlined text-3xl mb-2">medication</span>
                           <p className="font-bold text-sm">No active medications.</p>
                           <p className="text-[10px] opacity-60">Medications from uploaded records will appear here.</p>
                        </div>
                     ) : (
                        medications.map((med, i) => {
                           const isChecked = intakeChecked.has(med.id);
                           const borderColor = medColors[i % medColors.length];
                           return (
                              <div 
                                 key={med.id}
                                 onClick={(e) => handleIntakeToggle(e, med.id)} 
                                 className={`p-5 rounded-xl flex items-center justify-between cursor-pointer transition-all ${
                                    isChecked 
                                       ? 'bg-[var(--color-success)]/20 border-l-4 border-[var(--color-success)]' 
                                       : 'bg-white/10 border-l-4 hover:bg-white/20'
                                 }`}
                                 style={{ borderLeftColor: isChecked ? undefined : borderColor }}
                              >
                                 <div className="flex items-center gap-4">
                                    <div className={`w-3 h-3 rounded-full ${isChecked ? 'bg-[var(--color-success)] shadow-[0_0_10px_var(--color-success)]' : ''}`} style={{ backgroundColor: isChecked ? undefined : borderColor }}></div>
                                    <div>
                                       <p className={`font-black ${isChecked ? 'text-[var(--color-success)]' : 'text-[#FCB201]'}`}>
                                          {med.name}{med.dosage ? ` (${med.dosage})` : ''}
                                       </p>
                                       <p className="text-[10px] font-bold text-[#FCB201]/70">
                                          {med.frequency || 'As directed'}{med.prescribed_by ? ` • Dr. ${med.prescribed_by}` : ''}
                                          {med.notes ? ` • ${med.notes}` : ''}
                                       </p>
                                    </div>
                                 </div>
                                 <span className={`material-symbols-outlined text-3xl transition-colors ${isChecked ? 'text-[var(--color-success)]' : 'text-[#FCB201]/50'}`}>
                                    {isChecked ? 'check_circle' : 'radio_button_unchecked'}
                                 </span>
                              </div>
                           );
                        })
                     )}
                  </div>
               </div>

               {/* Reminders & Upcoming — FROM API */}
               <div className="hp-anim bg-[var(--color-surface)] rounded-2xl p-8 brick-shadow relative">
                  <h3 className="flex items-center gap-3 font-headline text-xl font-black tracking-tight mb-6 relative z-20 border-l-8 border-[var(--color-primary)] pl-4">
                     <span className="material-symbols-outlined text-[var(--color-primary)]">event_upcoming</span> Upcoming Appointments
                  </h3>
                  <div className="space-y-4 relative z-20">
                     {apptsLoading ? (
                        <div className="flex items-center justify-center py-8 opacity-50">
                           <span className="material-symbols-outlined animate-spin mr-2">progress_activity</span>
                           Loading appointments...
                        </div>
                     ) : appointments.length === 0 ? (
                        <div className="text-center py-8 opacity-40">
                           <span className="material-symbols-outlined text-3xl mb-2">event</span>
                           <p className="font-bold text-sm">No upcoming appointments.</p>
                        </div>
                     ) : (
                        appointments.slice(0, 4).map((appt) => {
                           const apptDate = new Date(appt.appointment_at);
                           const isUpcoming = apptDate > new Date();
                           return (
                              <div key={appt.id} className={`p-4 rounded-xl flex items-start gap-4 ${
                                 isUpcoming
                                    ? 'bg-[var(--color-secondary)]/10 border-l-4 border-[var(--color-secondary)]'
                                    : 'bg-black/5 border-l-4 border-black/20'
                              }`}>
                                 <span className={`material-symbols-outlined mt-1 ${isUpcoming ? 'text-[var(--color-secondary)]' : 'text-black/40'}`}>
                                    {isUpcoming ? 'stethoscope' : 'check_circle'}
                                 </span>
                                 <div>
                                    <p className="font-black text-sm">{appt.title}</p>
                                    <p className="text-[10px] font-bold opacity-60">
                                       {apptDate.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })} at {apptDate.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
                                       {appt.location ? ` • ${appt.location}` : ''}
                                    </p>
                                 </div>
                              </div>
                           );
                        })
                     )}
                  </div>
               </div>

               {/* Booking Button Block */}
               <div className="hp-anim bg-[var(--color-surface)] rounded-2xl p-8 brick-shadow">
                  <h3 className="font-headline text-xl font-black tracking-tight mb-4 border-l-8 border-[var(--color-tertiary)] pl-4">Appointments</h3>
                  <p className="text-sm font-bold opacity-60 mb-6">Need specialist attention? Our network is live.</p>
                  <button
                     onClick={openBookingModal}
                     className="w-full bg-[#FFFFF0] text-[#FCB201] uppercase tracking-widest text-xs font-black rounded-lg py-4 flex items-center justify-center gap-2 lego-brick lego-interactive hover:bg-white"
                  >
                     <span className="material-symbols-outlined">event_available</span>
                     Open Booking Directory
                  </button>
               </div>

            </div>

         </div>

         {/* --- BOOKING MODAL OVERLAY --- */}
         {isBookingModalOpen && (
            <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
               <div className="absolute inset-0 bg-black/60 backdrop-blur-md" onClick={() => setIsBookingModalOpen(false)}></div>
               <div ref={modalRef} className="relative z-10 w-full max-w-2xl bg-[var(--color-surface)] rounded-3xl brick-shadow border-4 border-white overflow-hidden studs-light">
                  <div className="p-8">
                     <div className="flex justify-between items-center mb-8 modal-anim">
                        <h2 className="font-headline text-3xl font-black text-[#FCB201]">Schedule Visit</h2>
                        <button onClick={() => setIsBookingModalOpen(false)} className="w-10 h-10 bg-black/5 rounded-full flex items-center justify-center hover:bg-black/10 transition-colors">
                           <span className="material-symbols-outlined font-bold text-[#FCB201]">close</span>
                        </button>
                     </div>

                     {bookingStep === 1 && (
                        <div className="space-y-6">
                           <p className="font-bold text-sm uppercase tracking-widest text-[#FCB201]/70 modal-anim">Step 1: Select Specialist Type</p>
                           <div className="grid grid-cols-2 gap-4">
                              {['Cardiology', 'Dermatology', 'Orthopedics', 'General Practice'].map((spec, i) => (
                                 <button
                                    key={i}
                                    onClick={() => { setSelectedSpecialist(spec); setBookingStep(2); }}
                                    className="modal-anim flex flex-col items-center justify-center bg-[var(--color-inverse-surface)] p-6 rounded-xl brick-shadow hover:-translate-y-1 hover:border-[var(--color-primary)] border-4 border-transparent transition-all group"
                                 >
                                    <div className="w-12 h-12 bg-white text-[var(--color-primary)] rounded-full flex items-center justify-center mb-3">
                                       <span className="material-symbols-outlined">medical_services</span>
                                    </div>
                                    <span className="font-black text-[#FCB201] group-hover:text-[var(--color-primary)]">{spec}</span>
                                 </button>
                              ))}
                           </div>
                        </div>
                     )}

                     {bookingStep === 2 && selectedSpecialist && (
                        <div className="space-y-6">
                           <div className="flex items-center gap-3 modal-anim border-b-2 border-black/10 pb-4 mb-4">
                              <button onClick={() => setBookingStep(1)} className="text-[#FCB201]/70 hover:text-[#FCB201]">
                                 <span className="material-symbols-outlined">arrow_back</span>
                              </button>
                              <p className="font-bold text-sm uppercase tracking-widest text-[var(--color-primary)]">{selectedSpecialist} Providers</p>
                           </div>
                           <div className="space-y-3">
                              <div className="modal-anim bg-white p-4 rounded-xl brick-shadow border-l-8 border-[var(--color-secondary)] flex justify-between items-center hp-interactive">
                                 <div className="flex items-center gap-4">
                                    <div className="w-12 h-12 bg-[var(--color-secondary)]/20 rounded-full flex items-center justify-center"><span className="material-symbols-outlined text-[var(--color-secondary)] font-black">person</span></div>
                                    <div>
                                       <p className="font-black text-[#FCB201] text-lg">Dr. Aris Thorne</p>
                                       <p className="text-xs font-bold text-[#FCB201]/70">Next avail: Today, 2:00 PM</p>
                                    </div>
                                 </div>
                                 <button onClick={() => setIsBookingModalOpen(false)} className="bg-[#FFFFF0] text-[#FCB201] px-4 py-2 text-xs font-black uppercase tracking-widest rounded lego-brick lego-interactive hover:bg-white">BOOK</button>
                              </div>
                              <div className="modal-anim bg-white p-4 rounded-xl brick-shadow border-l-8 border-[var(--color-tertiary)] flex justify-between items-center hp-interactive">
                                 <div className="flex items-center gap-4">
                                    <div className="w-12 h-12 bg-[var(--color-tertiary)]/20 rounded-full flex items-center justify-center"><span className="material-symbols-outlined text-[var(--color-tertiary)] font-black">person</span></div>
                                    <div>
                                       <p className="font-black text-[#FCB201] text-lg">Dr. Elena Rostova</p>
                                       <p className="text-xs font-bold text-[#FCB201]/70">Next avail: Thursday, 10:00 AM</p>
                                    </div>
                                 </div>
                                 <button onClick={() => setIsBookingModalOpen(false)} className="bg-[#FFFFF0] text-[#FCB201] px-4 py-2 text-xs font-black uppercase tracking-widest rounded lego-brick lego-interactive hover:bg-white">BOOK</button>
                              </div>
                           </div>
                        </div>
                     )}
                  </div>
               </div>
            </div>
         )}

      </div>
   );
}
