"use client";
import React, { useEffect, useRef, useState } from "react";
import anime from "animejs";
import { recordsApi, appointmentsApi, type RecordListItem, type Appointment, type UserProfile } from "@/lib/api";
import { getStoredUser } from "@/lib/auth";

interface TimelineProps {
  userProfile?: UserProfile | null;
}

// A unified timeline event for rendering
interface TimelineNode {
  id: string;
  date: string;
  type: "RECORD" | "APPOINTMENT";
  title: string;
  category?: string | null;
  status?: string;
  description?: string;
  tags?: string[] | null;
  icon: string;
  color: string;
  side: "left" | "right";
}

export default function Timeline({ userProfile }: TimelineProps) {
  const lineRef = useRef<HTMLDivElement>(null);
  const [timelineNodes, setTimelineNodes] = useState<TimelineNode[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  // Fetch timeline data from multiple API endpoints
  useEffect(() => {
    loadTimeline();
  }, []);

  const loadTimeline = async () => {
    setIsLoading(true);
    setError("");

    try {
      // Fetch records and appointments in parallel
      const [recordsResult, appointmentsResult] = await Promise.allSettled([
        recordsApi.list({ limit: 50 }),
        appointmentsApi.list(),
      ]);

      const nodes: TimelineNode[] = [];
      const colors = [
        "var(--color-primary)",
        "var(--color-secondary)",
        "var(--color-tertiary)",
        "var(--color-success)",
      ];
      const icons: Record<string, string> = {
        lab_report: "bloodtype",
        prescription: "medication",
        imaging: "radiology",
        consultation: "stethoscope",
        discharge: "home_health",
        default: "description",
      };

      // Process records
      if (recordsResult.status === "fulfilled") {
        recordsResult.value.data.forEach((record: RecordListItem, i: number) => {
          nodes.push({
            id: record.id,
            date: record.document_date || record.created_at.split("T")[0],
            type: "RECORD",
            title: record.title,
            category: record.category?.label || null,
            status: record.processing_status,
            tags: record.tags,
            icon: icons[record.category?.slug || "default"] || icons.default,
            color: colors[i % colors.length],
            side: i % 2 === 0 ? "right" : "left",
          });
        });
      }

      // Process appointments
      if (appointmentsResult.status === "fulfilled") {
        appointmentsResult.value.data.forEach((appt: Appointment, i: number) => {
          nodes.push({
            id: appt.id,
            date: appt.appointment_at.split("T")[0],
            type: "APPOINTMENT",
            title: appt.title,
            category: "Appointment",
            status: appt.status,
            description: appt.location || undefined,
            icon: "event",
            color: colors[(i + 2) % colors.length],
            side: (nodes.length + i) % 2 === 0 ? "right" : "left",
          });
        });
      }

      // Sort by date descending
      nodes.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());

      // Re-assign sides after sorting
      nodes.forEach((node, i) => {
        node.side = i % 2 === 0 ? "right" : "left";
      });

      setTimelineNodes(nodes);
    } catch {
      setError("Failed to load timeline data.");
    } finally {
      setIsLoading(false);
    }
  };

  // Animate after data loads
  useEffect(() => {
    if (isLoading || timelineNodes.length === 0) return;

    const tl = anime.timeline({ easing: 'easeOutExpo' });

    tl.add({
      targets: '.timeline-header h1, .timeline-header p',
      translateY: [40, 0],
      opacity: [0, 1],
      delay: anime.stagger(150),
      duration: 1000
    })
    .add({
      targets: lineRef.current,
      scaleY: [0, 1],
      opacity: [0, 0.3],
      duration: 1500,
      easing: 'easeInOutQuart'
    }, '-=500');

    const cards = document.querySelectorAll('.timeline-node');
    
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const el = entry.target as HTMLElement;
          const card = el.querySelector('.timeline-card');
          const icon = el.querySelector('.timeline-icon');
          
          anime({
            targets: icon,
            scale: [0, 1.2, 1],
            rotate: [anime.random(-60, 60), 0],
            duration: 800,
            easing: 'easeOutElastic(1, .6)'
          });

          anime({
            targets: card,
            translateX: el.classList.contains('timeline-left') ? [50, 0] : [-50, 0],
            opacity: [0, 1],
            delay: 100,
            duration: 800,
            easing: 'easeOutElastic(1, .8)'
          });

          if (card) {
             (card as HTMLElement).addEventListener('mouseenter', () => {
                anime({ targets: card, scale: 1.02, translateY: -4, duration: 400, easing: 'easeOutElastic(1.5, .8)' });
                if (icon) anime({ targets: icon, scale: 1.15, rotateZ: 10, duration: 400, easing: 'easeOutExpo' });
             });
             (card as HTMLElement).addEventListener('mouseleave', () => {
                anime({ targets: card, scale: 1, translateY: 0, duration: 600, easing: 'easeOutElastic(1, .5)' });
                if (icon) anime({ targets: icon, scale: 1, rotateZ: 0, duration: 600, easing: 'easeOutExpo' });
             });
          }

          observer.unobserve(el);
          el.style.opacity = '1';
        }
      });
    }, { threshold: 0.1, rootMargin: "0px 0px -100px 0px" });

    cards.forEach(card => {
       (card as HTMLElement).style.opacity = '0';
       observer.observe(card);
    });

    return () => observer.disconnect();
  }, [isLoading, timelineNodes]);

  const formatDate = (dateStr: string): string => {
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
  };

  const getStatusBadge = (status?: string) => {
    if (!status) return null;
    const colors: Record<string, string> = {
      COMPLETED: 'bg-[var(--color-success)] text-white',
      PENDING: 'bg-orange-500 text-white',
      PROCESSING: 'bg-[var(--color-secondary)] text-white',
      SCHEDULED: 'bg-[var(--color-primary)] text-white',
      CANCELLED: 'bg-red-500 text-white',
      MANUAL_REVIEW: 'bg-yellow-500 text-black',
    };
    return (
      <span className={`text-[10px] px-3 py-1 rounded-full font-black uppercase tracking-wider ${colors[status] || 'bg-gray-400 text-white'}`}>
        {status}
      </span>
    );
  };

  return (
    <div className="max-w-5xl mx-auto pb-40 fade-in-section relative z-30">
        
      {/* Header Section */}
      <header className="mb-20 max-w-4xl timeline-header relative z-20">
        <div className="flex items-center gap-4 mb-4">
          <span className="bg-[var(--color-primary)] text-white px-3 py-1 rounded text-xs font-black tracking-widest uppercase brick-shadow">Patient History</span>
          <div className="h-[1px] flex-grow bg-[var(--color-surface-container)]"></div>
        </div>
        <h1 className="text-6xl font-black font-headline tracking-tighter text-[var(--color-primary)] mb-6 leading-tight">
            Your Health, <br/>
            <span className="text-[var(--color-secondary)] italic">Chronologically Secured.</span>
        </h1>
        <p className="text-lg font-bold opacity-70 max-w-xl leading-relaxed bg-[var(--color-surface)] p-6 rounded-xl brick-shadow">
            {userProfile?.full_name 
              ? `${userProfile.full_name}'s comprehensive longitudinal medical history timeline. Each node is indexed to its corresponding record for instant cross-reference.`
              : 'A comprehensive longitudinal medical history timeline spanning all your medical records and appointments. Each node is indexed to its corresponding record for instant cross-reference.'
            }
        </p>
      </header>

      {/* Loading State */}
      {isLoading && (
        <div className="flex flex-col items-center justify-center py-20">
          <span className="material-symbols-outlined text-5xl text-[var(--color-primary)] animate-spin mb-4">progress_activity</span>
          <p className="font-headline font-black text-sm uppercase tracking-widest text-[var(--color-primary)]">Loading Timeline...</p>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-red-500 text-white px-6 py-4 rounded-xl font-bold text-sm flex items-center gap-3 brick-shadow mb-8">
          <span className="material-symbols-outlined">error</span>
          {error}
          <button onClick={loadTimeline} className="ml-auto bg-white/20 px-4 py-2 rounded font-black text-xs uppercase tracking-widest hover:bg-white/30">
            Retry
          </button>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !error && timelineNodes.length === 0 && (
        <div className="flex flex-col items-center justify-center py-20 bg-[var(--color-surface)] rounded-2xl brick-shadow">
          <span className="material-symbols-outlined text-6xl text-black/20 mb-4">timeline</span>
          <h3 className="font-headline font-black text-xl text-black/40 mb-2">No Timeline Events Yet</h3>
          <p className="font-bold text-sm text-black/30">Upload medical records to start building your health timeline.</p>
        </div>
      )}

      {/* Timeline Section — Dynamic from API */}
      {!isLoading && timelineNodes.length > 0 && (
        <section className="relative py-10 z-20">
          {/* Central Vertical Line */}
          <div 
             ref={lineRef}
             className="absolute left-[5%] md:left-1/2 top-0 bottom-0 w-2 lg:w-4 -translate-x-1/2 origin-top rounded-full z-10"
             style={{ background: 'linear-gradient(to bottom, transparent, var(--color-primary), var(--color-secondary), var(--color-tertiary), transparent)' }}
          ></div>

          <div className="space-y-32 relative z-20">
            {timelineNodes.map((node, i) => (
              <div 
                key={node.id} 
                className={`timeline-node ${node.side === 'left' ? 'timeline-left flex flex-col md:flex-row-reverse' : 'timeline-right flex flex-col md:flex-row'} items-center justify-between w-full relative z-20`}
              >
                {/* Date & Title Side */}
                <div className={`hidden md:block md:w-5/12 ${node.side === 'left' ? 'text-left pl-12' : 'text-right pr-12'} relative z-20`}>
                   <span className="font-bold text-sm tracking-widest block mb-2 uppercase" style={{ color: node.color }}>{formatDate(node.date)}</span>
                   <h3 className="text-2xl font-black font-headline text-white">{node.type === 'RECORD' ? (node.category || 'Medical Record') : 'Appointment'}</h3>
                </div>
                
                {/* Icon */}
                <div className="absolute left-[5%] md:left-1/2 md:relative -translate-x-1/2 md:translate-x-0 z-30">
                   <div className="timeline-icon w-12 h-12 rounded brick-shadow flex items-center justify-center border-4 border-white" style={{ backgroundColor: node.color }}>
                      <span className="material-symbols-outlined text-white z-20 relative">{node.icon}</span>
                   </div>
                </div>
                
                {/* Card */}
                <div className={`w-[85%] ${node.side === 'left' ? 'ml-auto md:mr-0 md:w-5/12 md:pr-12' : 'ml-auto md:ml-0 md:w-5/12 md:pl-12'} relative z-20`}>
                   <div 
                     className={`timeline-card p-6 rounded-xl brick-shadow flex flex-col gap-4 relative z-20 ${
                       node.side === 'left' 
                         ? 'bg-[var(--color-surface)] text-black md:border-r-8 md:border-l-0 border-l-8' 
                         : 'bg-transparent border-l-8'
                     }`}
                     style={{ borderColor: node.color }}
                   >
                      <div className="flex items-center gap-3 flex-wrap">
                         <span className="text-white p-2 rounded brick-shadow text-xs font-black uppercase tracking-wider flex items-center gap-2" style={{ backgroundColor: node.color }}>
                            <span className="material-symbols-outlined text-sm">{node.icon}</span>
                            {node.title}
                         </span>
                         {getStatusBadge(node.status)}
                      </div>
                      
                      {node.description && (
                        <p className={`text-sm font-bold leading-relaxed p-3 rounded ${
                          node.side === 'left' ? 'bg-white text-black' : 'bg-transparent text-[#FCB201]'
                        }`}>
                           {node.description}
                        </p>
                      )}

                      {node.tags && node.tags.length > 0 && (
                        <div className="flex gap-2 flex-wrap">
                          {node.tags.map((tag, ti) => (
                            <span key={ti} className="bg-black/10 text-black/70 px-3 py-1 rounded text-[10px] font-black uppercase tracking-wider">
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}

                      <p className="text-[10px] font-bold opacity-40 uppercase tracking-widest">
                        {node.type === 'RECORD' ? '📄 Medical Record' : '📅 Appointment'} • {formatDate(node.date)}
                      </p>
                   </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

    </div>
  );
}
