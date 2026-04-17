"use client";
import React, { useEffect, useRef, useState } from 'react';
import anime from 'animejs';

interface LandingPageProps {
  onLogin: (route?: string) => void;
}

export default function LandingPage({ onLogin }: LandingPageProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const pathRef = useRef<SVGPathElement>(null);

  // Stats Counter state
  const [stats, setStats] = useState({
    patients: 0,
    satisfaction: 0,
    records: 0
  });

  useEffect(() => {
    // 1. Hero Text Reveal (Anime.js V4 style stagger)
    const titleText = "Vital Vault";
    const titleElement = document.querySelector('.hero-title');
    if (titleElement) {
        titleElement.innerHTML = titleText.replace(/\S/g, "<span class='letter inline-block opacity-0'>$&</span>");
        
        anime.timeline({loop: false})
        .add({
            targets: '.hero-title .letter',
            translateY: [40,0],
            opacity: [0,1],
            easing: "easeOutExpo",
            duration: 1200,
            delay: (el, i) => 30 * i
        })
        .add({
            targets: '.hero-subtitle',
            translateY: [20, 0],
            opacity: [0, 1],
            easing: "easeOutExpo",
            duration: 800,
        }, '-=800')
        .add({
            targets: '.hero-cta',
            scale: [0.9, 1],
            opacity: [0, 1],
            easing: "easeOutElastic(1, .6)",
            duration: 1000,
        }, '-=600');
    }

    // 2. Background Stagger Grid Pulse
    anime({
      targets: '.stud-pulse',
      scale: [0.8, 1.1, 1],
      opacity: [1, 0.5, 1],
      delay: anime.stagger(200, {grid: [10, 5], from: 'center'}),
      loop: true,
      direction: 'alternate',
      easing: 'easeInOutQuad',
      duration: 2000
    });

    // 3. Scroll Interactions (Feature Cards & SVGs)
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const el = entry.target;

                // Feature Cards Stagger
                if (el.classList.contains('features-grid')) {
                    anime({
                        targets: el.querySelectorAll('.feature-card'),
                        translateY: [60, 0],
                        opacity: [0, 1],
                        delay: anime.stagger(80),
                        duration: 800,
                        easing: 'easeOutExpo'
                    });
                    observer.unobserve(el);
                }

                // SVG Line Drawing
                if (el.classList.contains('how-it-works')) {
                    anime({
                        targets: pathRef.current,
                        strokeDashoffset: [anime.setDashoffset, 0],
                        easing: 'easeInOutSine',
                        duration: 1500,
                        delay: 300
                    });
                    
                    anime({
                        targets: el.querySelectorAll('.step-card'),
                        scale: [0.8, 1],
                        opacity: [0, 1],
                        delay: anime.stagger(400),
                        duration: 800,
                        easing: 'easeOutElastic(1, .6)'
                    });
                    observer.unobserve(el);
                }

                // Counters Activation
                if (el.classList.contains('stats-section')) {
                    const statsObj = { p: 0, s: 0, r: 0 };
                    anime({
                        targets: statsObj,
                        p: 10000,
                        s: 98,
                        r: 250,
                        round: 1,
                        easing: 'easeOutExpo',
                        duration: 2000,
                        update: function() {
                            setStats({
                                patients: statsObj.p,
                                satisfaction: statsObj.s,
                                records: statsObj.r
                            });
                        }
                    });
                    observer.unobserve(el);
                }
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('.scroll-trigger').forEach(node => observer.observe(node));

    // Interactive Hover on LEGO cards (Micro-scale + Rotate Bounce)
    document.querySelectorAll('.feature-card').forEach(el => {
       const htmlEl = el as HTMLElement;
       htmlEl.addEventListener('mouseenter', () => {
           anime({
               targets: htmlEl,
               scale: 1.03,
               rotate: anime.random(-1, 1) + 'deg',
               duration: 400,
               easing: 'easeOutElastic(1.5, 0.8)' // Simulating createSpring(stiffness:200, damping:10)
           });
       });
       htmlEl.addEventListener('mouseleave', () => {
           anime({
               targets: htmlEl,
               scale: 1,
               rotate: '0deg',
               duration: 600,
               easing: 'easeOutElastic(1, 0.5)'
           });
       });
    });

    return () => observer.disconnect();
  }, []);

  // 4. Draggable Sandbox Implementation
  const handleDragStart = (e: React.MouseEvent | React.TouchEvent, i: number) => {
    const el = e.currentTarget as HTMLElement;
    const isTouch = e.type === 'touchstart';
    const clientX = isTouch ? (e as React.TouchEvent).touches[0].clientX : (e as React.MouseEvent).clientX;
    const clientY = isTouch ? (e as React.TouchEvent).touches[0].clientY : (e as React.MouseEvent).clientY;

    const rect = el.getBoundingClientRect();
    const offsetX = clientX - rect.left;
    const offsetY = clientY - rect.top;

    // Elevate on grab
    anime({ targets: el, scale: 1.1, rotate: 2, boxShadow: '0 20px 0 0 rgba(0,0,0,0.2)', duration: 300, easing: 'easeOutElastic(1.5, .8)' });

    const moveAt = (pageX: number, pageY: number) => {
        el.style.left = pageX - offsetX + 'px';
        el.style.top = pageY - offsetY + 'px';
    };

    const onMouseMove = (moveEvent: MouseEvent | TouchEvent) => {
        const moveX = moveEvent.type === 'touchmove' ? (moveEvent as TouchEvent).touches[0].pageX : (moveEvent as MouseEvent).pageX;
        const moveY = moveEvent.type === 'touchmove' ? (moveEvent as TouchEvent).touches[0].pageY : (moveEvent as MouseEvent).pageY;
        moveAt(moveX, moveY);
    };

    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('touchmove', onMouseMove);

    const onMouseUp = () => {
        document.removeEventListener('mousemove', onMouseMove);
        document.removeEventListener('touchmove', onMouseMove);
        
        // Spring physics release
        anime({ targets: el, scale: 1, rotate: 0, boxShadow: '0 4px 0 0 rgba(0,0,0,0.4)', duration: 600, easing: 'easeOutElastic(1, .5)' });
        document.removeEventListener('mouseup', onMouseUp);
        document.removeEventListener('touchend', onMouseUp);
    };

    document.addEventListener('mouseup', onMouseUp);
    document.addEventListener('touchend', onMouseUp);
  };

  return (
    <div ref={containerRef} className="w-full min-h-screen bg-[#FFCB05] text-black font-body overflow-x-hidden selection:bg-[var(--color-primary)] selection:text-white pb-32">
       
       {/* -------------------- HERO SECTION -------------------- */}
       <section className="relative min-h-[90vh] flex flex-col items-center justify-center text-center p-6 border-b-8 border-black">
          {/* Animated Auto-Grid Pattern Background */}
          <div className="absolute inset-0 z-0 overflow-hidden flex flex-wrap justify-center items-center opacity-20 pointer-events-none">
             {Array.from({length: 50}).map((_, i) => (
                <div key={i} className="stud-pulse w-16 h-16 m-4 rounded-full border-[6px] border-black opacity-50"></div>
             ))}
          </div>

          <div className="relative z-10 max-w-4xl bg-white p-12 rounded-3xl lego-brick mb-10 translate-y-8 hp-interactive">
             {/* Vital Vault Logo */}
             <div className="flex justify-center mb-6">
                <img
                   src="/vital_vault_logo.png"
                   alt="Vital Vault - Secure Health Records"
                   className="h-28 w-auto object-contain drop-shadow-lg"
                />
             </div>
             
             <h1 className="hero-title text-6xl md:text-[100px] font-black font-headline text-black tracking-tighter leading-none mb-4"></h1>
          </div>

          <button 
             onClick={() => onLogin()} 
             className="hero-cta opacity-0 bg-[#FFFFF0] text-black text-2xl font-black font-headline uppercase tracking-widest px-10 py-6 rounded-xl lego-brick lego-interactive z-20 hover:bg-white"
          >
             Enter The Vault
          </button>
       </section>

       {/* -------------------- FEATURES GRID -------------------- */}
       <section className="py-32 px-6 max-w-7xl mx-auto scroll-trigger features-grid border-b-8 border-black border-dashed">
          <div className="text-center mb-16">
             <span className="bg-black text-white px-4 py-2 font-black uppercase text-sm rounded-lg lego-brick mb-4 inline-block">App Modules</span>
             <h2 className="text-5xl font-black font-headline tracking-tighter">Everything Clicks into Place</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
             {[
               { id: 'Records', icon: 'folder_open', color: 'bg-[#FF6B35]', route: 'upload' },
               { id: 'Prescriptions', icon: 'pill', color: 'bg-[#00C9A7]', route: 'dashboard' },
               { id: 'Doctors', icon: 'medical_services', color: 'bg-[#FF4C8B]', route: 'dashboard' },
               { id: 'Timeline', icon: 'history', color: 'bg-[#4DA8FF]', route: 'timeline' },
             ].map((feature, i) => (
                <div key={i} onClick={() => onLogin(feature.route)} className={`feature-card opacity-0 ${feature.color} p-8 rounded-2xl lego-brick cursor-pointer relative overflow-hidden group`}>
                   {/* Stud detail top left */}
                   <div className="absolute top-4 left-4 w-6 h-6 rounded-full bg-white/20 border-2 border-black/20"></div>
                   <div className="mt-8 flex flex-col items-center text-center gap-4">
                      <span className="material-symbols-outlined text-6xl drop-shadow-md group-hover:scale-110 transition-transform">{feature.icon}</span>
                      <h3 className="text-2xl font-black font-headline">{feature.id}</h3>
                   </div>
                </div>
             ))}
          </div>
       </section>

       {/* -------------------- HOW IT WORKS (SVG LINE DRAWING) -------------------- */}
       <section className="py-32 px-6 max-w-6xl mx-auto scroll-trigger how-it-works">
          <div className="text-center mb-16">
             <h2 className="text-5xl font-black font-headline tracking-tighter">Build Your Protocol In 3 Steps</h2>
          </div>

          <div className="relative flex flex-col md:flex-row items-center justify-between gap-12 pt-10">
             {/* Animated SVG Path connecting nodes */}
             <svg className="absolute top-1/2 left-0 w-full h-full -translate-y-1/2 -z-10 hidden md:block" style={{ overflow: 'visible' }}>
                 <path ref={pathRef} d="M 100,50 Q 300,150 500,50 T 1000,50" fill="none" stroke="var(--color-primary)" strokeWidth="12" strokeLinecap="round" strokeDasharray="1000" strokeDashoffset="1000" />
             </svg>

             {[
               { no: 1, title: 'Upload', desc: 'Securely drop your files into the vault. AI auto-categorizes them.' },
               { no: 2, title: 'Assemble', desc: 'Our system stacks your health data into a chronological timeline.' },
               { no: 3, title: 'Connect', desc: 'Share your complete block with specialists globally.' }
             ].map((step, i) => (
                <div key={i} className="step-card opacity-0 bg-white border-4 border-black p-8 rounded-2xl flex-1 text-center lego-brick relative bg-white z-10 w-full max-w-sm">
                   <div className="absolute -top-6 left-1/2 -translate-x-1/2 w-12 h-12 bg-black text-white rounded-full font-black text-2xl flex items-center justify-center lego-brick">
                      {step.no}
                   </div>
                   <h3 className="text-2xl font-black font-headline mt-6 mb-2">{step.title}</h3>
                   <p className="font-bold opacity-70">{step.desc}</p>
                </div>
             ))}
          </div>
       </section>

       {/* -------------------- STATS COUNTERS -------------------- */}
       <section className="py-20 px-6 bg-[var(--color-primary)] scroll-trigger stats-section border-y-8 border-black mt-20">
          <div className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-8">
             <div className="bg-white p-8 rounded-2xl text-center lego-brick flex flex-col gap-2">
                <span className="text-5xl font-headline font-black text-black">+{stats.patients.toLocaleString()}</span>
                <span className="font-black text-sm uppercase tracking-widest text-black/50">Active Vaults</span>
             </div>
             <div className="bg-white p-8 rounded-2xl text-center lego-brick flex flex-col gap-2">
                <span className="text-5xl font-headline font-black text-[var(--color-success)]">{stats.satisfaction}%</span>
                <span className="font-black text-sm uppercase tracking-widest text-black/50">Data Recovery Score</span>
             </div>
             <div className="bg-white p-8 rounded-2xl text-center lego-brick flex flex-col gap-2">
                <span className="text-5xl font-headline font-black text-black">{stats.records}k+</span>
                <span className="font-black text-sm uppercase tracking-widest text-black/50">Files Assembled</span>
             </div>
          </div>
       </section>

       {/* -------------------- FOOTER CTA -------------------- */}
       <footer className="pt-32 pb-20 px-6 text-center max-w-4xl mx-auto">
          <h2 className="text-5xl font-black font-headline tracking-tighter mb-8">Ready to Connect Your Pieces?</h2>
          <button 
             onClick={() => onLogin()}
             className="bg-[#FFFFF0] text-black text-3xl font-black font-headline uppercase tracking-widest px-12 py-8 rounded-2xl lego-brick lego-interactive mx-auto hover:bg-white"
          >
             Start Building Free
          </button>
       </footer>

    </div>
  );
}
