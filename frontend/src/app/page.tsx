"use client";
/* eslint-disable @next/next/no-img-element */

import React, { useState, useEffect } from "react";
import LandingPage from "@/components/LandingPage";
import LoginOverlay from "@/components/LoginOverlay";
import Sidebar from "@/components/Sidebar";
import Dashboard from "@/components/Dashboard";
import Profile from "@/components/Profile";
import Upload from "@/components/Upload";
import Timeline from "@/components/Timeline";
import Vault from "@/components/Vault";
import Medications from "@/components/Medications";
import Reminders from "@/components/Reminders";
import Appointments from "@/components/Appointments";
import anime from "animejs";
import { isAuthenticated as checkAuth, getTokens, clearTokens, getStoredUser } from "@/lib/auth";
import { authApi, usersApi, type UserProfile } from "@/lib/api";

export default function Home() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [showLoginOverlay, setShowLoginOverlay] = useState(false);
  const [pendingRoute, setPendingRoute] = useState<string | undefined>(undefined);
  const [currentView, setCurrentView] = useState("dashboard");
  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);

  // Check for existing valid token on mount → auto-login
  useEffect(() => {
    if (checkAuth()) {
      setIsAuthenticated(true);
      // Fetch profile in background
      usersApi.getMe().then(setUserProfile).catch(() => {
        // Token might be expired and refresh failed
        clearTokens();
        setIsAuthenticated(false);
      });
    }
    setIsCheckingAuth(false);
  }, []);

  // Fetch user profile when user authenticates
  useEffect(() => {
    if (isAuthenticated && !userProfile) {
      usersApi.getMe().then(setUserProfile).catch(() => {
        // Silent fail — profile will show fallback data
      });
    }
  }, [isAuthenticated, userProfile]);

  // Trigger a seamless, robust AnimeJS Timeline when switching to Authenticated State
  useEffect(() => {
    if (isAuthenticated) {
      // 1. Gather all elements for the entrance animation
      const navElements = document.querySelectorAll('aside nav button, aside .border-t button, aside .w-12.h-12, aside h1, aside p');
      const headerElements = document.querySelectorAll('header .flex.items-center, header button, header img');
      const bricks = document.querySelectorAll('section.grid > div, .lego-card, .lg\\:col-span-4 > div, .fixed.bottom-8.right-8, .fixed.bottom-10.right-10');
      
      const allElements = [...Array.from(navElements), ...Array.from(headerElements), ...Array.from(bricks)] as HTMLElement[];

      // Instantly ensure they are visible but scaled down/zero opacity for Anime to grab
      allElements.forEach((el) => {
        el.style.opacity = "0";
        el.classList.remove("lego-animate");
      });

      // 2. Play the Staggered Master Entrance Timeline
      const tl = anime.timeline({
        easing: 'easeOutElastic(1, .8)',
      });

      tl.add({
        targets: navElements,
        opacity: [0, 1],
        translateX: [-20, 0],
        duration: 800,
        delay: anime.stagger(50)
      })
      .add({
        targets: headerElements,
        opacity: [0, 1],
        translateY: [-20, 0],
        duration: 800,
        delay: anime.stagger(50)
      }, '-=600')
      .add({
        targets: bricks,
        opacity: [0, 1],
        translateY: [40, 0],
        duration: 1000,
        delay: anime.stagger(100)
      }, '-=600');

      // 3. Fully Interactive Physics via AnimeJS
      const tactileTargets = document.querySelectorAll(
        "aside nav button, aside .border-t button, section.grid > div, .lego-card, .lg\\:col-span-4 > div, header button, .fixed.bottom-10.right-10, input, button"
      );
      
      tactileTargets.forEach((brick) => {
        const el = brick as HTMLElement;
        el.style.transition = ""; // Strip slow CSS transitions to let AnimeJS fly
        
        el.addEventListener("mouseenter", () => {
          anime({
            targets: el,
            scale: 1.03,
            translateY: -4,
            boxShadow: '0 12px 0 0 rgba(0, 0, 0, 0.1)',
            duration: 400,
            easing: "easeOutElastic(1.5, 0.8)",
          });
        });

        el.addEventListener("mouseleave", () => {
          anime({
            targets: el,
            scale: 1,
            translateY: 0,
            boxShadow: '0 4px 0 0 rgba(0, 0, 0, 0.15)',
            duration: 600,
            easing: "easeOutElastic(1, 0.5)",
          });
        });

        el.addEventListener("mousedown", () => {
          anime({
            targets: el,
            scale: 0.95,
            translateY: 4,
            boxShadow: '0 0px 0 0 rgba(0, 0, 0, 0)',
            duration: 100,
            easing: "easeOutQuad",
          });
        });

        el.addEventListener("mouseup", () => {
          anime({
            targets: el,
            scale: 1.03,
            translateY: -4,
            boxShadow: '0 12px 0 0 rgba(0, 0, 0, 0.1)',
            duration: 400,
            easing: "easeOutElastic(1.5, 0.8)",
          });
        });
      });
    }
  }, [isAuthenticated, currentView]);

  const handleLogout = async () => {
    const tokens = getTokens();
    
    // Animate out first
    const authView = document.getElementById("authenticated-view");
    if (authView) {
      anime({
        targets: authView,
        opacity: [1, 0],
        duration: 400,
        easing: "easeInQuad",
        complete: async () => {
          // Call logout API to revoke refresh token
          if (tokens?.refresh_token) {
            try {
              await authApi.logout(tokens.refresh_token);
            } catch {
              // Ignore — we'll clear tokens locally regardless
            }
          }
          clearTokens();
          setUserProfile(null);
          setIsAuthenticated(false);
          setCurrentView("dashboard");
        },
      });
    } else {
      if (tokens?.refresh_token) {
        try {
          await authApi.logout(tokens.refresh_token);
        } catch {
          // Ignore
        }
      }
      clearTokens();
      setUserProfile(null);
      setIsAuthenticated(false);
      setCurrentView("dashboard");
    }
  };

  // Show nothing while checking initial auth
  if (isCheckingAuth) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--color-inverse-surface)]">
        <div className="flex flex-col items-center gap-4">
          <span className="material-symbols-outlined text-5xl text-[var(--color-primary)] animate-spin">
            progress_activity
          </span>
          <p className="text-[var(--color-primary)] font-headline font-black uppercase tracking-widest text-sm">
            Loading Vault...
          </p>
        </div>
      </div>
    );
  }

  return (
    <>
      {!isAuthenticated && (
        <LandingPage onLogin={(route?: string) => {
          setPendingRoute(route);
          setShowLoginOverlay(true);
        }} />
      )}

      {/* Login Overlay — shown above landing page when vault CTA is clicked */}
      {!isAuthenticated && showLoginOverlay && (
        <LoginOverlay
          onLogin={() => {
            setShowLoginOverlay(false);
            setIsAuthenticated(true);
            if (pendingRoute) setCurrentView(pendingRoute.toLowerCase());
          }}
        />
      )}
      {/* Authenticated Dashboard Wrapper */}
      <div
        id="authenticated-view"
        style={{ display: isAuthenticated ? "block" : "none", opacity: isAuthenticated ? 1 : 0 }}
        className="transition-opacity duration-500"
      >
        <Sidebar 
          currentView={currentView} 
          onNavigate={(view) => setCurrentView(view)} 
          onLogout={handleLogout}
          userProfile={userProfile}
        />

        <main className="ml-64 min-h-screen relative p-8">
          {/* Top Navigation Block */}
          <header className="w-full bg-[var(--color-surface)] brick-shadow rounded p-5 mb-8 flex justify-between items-center studs-light relative z-30">
            <div className="flex items-center gap-4 mt-4 relative z-20">
              <h2 className="font-headline tracking-tight font-black text-2xl text-[var(--color-secondary)] ml-2">
                Medical Overview
              </h2>
              <div className="h-8 w-1 bg-[var(--color-surface-container)] mx-2"></div>
              <span className="text-sm font-bold uppercase tracking-widest opacity-80 bg-transparent text-[#FCB201] px-3 py-1 rounded">
                {userProfile?.full_name || getStoredUser()?.email || "Patient"}
              </span>
            </div>
            <div className="flex items-center gap-5 mt-4 relative z-40 pr-2">
              <div className="relative">
                <button 
                  onClick={() => setIsNotificationsOpen(!isNotificationsOpen)}
                  className="w-12 h-12 bg-black text-white rounded brick-shadow flex items-center justify-center hover:bg-[var(--color-primary)] hover:text-white transition-colors cursor-pointer"
                >
                  <span className="material-symbols-outlined">notifications</span>
                  {/* Ping Indicator */}
                  <span className="absolute -top-1 -right-1 w-4 h-4 bg-[var(--color-success)] border-2 border-white rounded-full animate-pulse tracking-widest text-[8px] flex items-center justify-center text-black font-black">2</span>
                </button>

                {/* Notifications Dropdown Panel */}
                {isNotificationsOpen && (
                  <div className="absolute top-16 right-0 w-80 bg-white text-black p-6 rounded-xl brick-shadow-heavy border-4 border-[var(--color-surface-container)] z-50 animate-in fade-in slide-in-from-top-4 duration-300">
                    <h3 className="font-headline font-black text-lg mb-4 border-b pb-2">Active Notifications</h3>
                    <div className="space-y-4">
                      <div className="flex items-start gap-4">
                        <div className="w-8 h-8 rounded bg-[var(--color-primary)] flex-shrink-0 flex items-center justify-center brick-shadow">
                          <span className="material-symbols-outlined text-white text-sm">medication</span>
                        </div>
                        <div>
                          <p className="font-black text-sm leading-tight text-[var(--color-primary)]">Time to consume Medication</p>
                          <p className="text-xs font-bold opacity-60">Omeprazole 40mg • Required before meals</p>
                        </div>
                      </div>
                      <div className="flex items-start gap-4 mt-2 pt-4 border-t border-black/10">
                        <div className="w-8 h-8 rounded bg-[var(--color-secondary)] flex-shrink-0 flex items-center justify-center brick-shadow">
                          <span className="material-symbols-outlined text-white text-sm">schedule</span>
                        </div>
                        <div>
                          <p className="font-black text-sm leading-tight text-[var(--color-secondary)]">Upcoming Consultation</p>
                          <p className="text-xs font-bold opacity-60">Dr. Aris Thorne • Tomorrow at 10:00 AM</p>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              <div onClick={() => setCurrentView("profile")} className="w-14 h-14 bg-[var(--color-tertiary)] rounded brick-shadow p-1 cursor-pointer border-solid border-2 border-[var(--color-surface)] hover:scale-105 transition-transform flex items-center justify-center">
                {userProfile?.full_name ? (
                  <span className="text-xl font-black text-[var(--color-on-tertiary)]">
                    {userProfile.full_name.charAt(0).toUpperCase()}
                  </span>
                ) : (
                  <img
                    alt="Avatar"
                    className="w-full h-full object-cover rounded-sm"
                    src="https://lh3.googleusercontent.com/aida-public/AB6AXuARNRAxDWETpUuESo2wut6B_-eulBDY17jdsDVhHdCsT9ZBVbW5nEE-aAKluQ6fNFEl9sgnJer8fL_K9-Bpd45fGamMpjNzq7HCOaUMXws4eSa-addbw63uAg-flKvuxxRhY813pxZm3N2wJKXJ_1OVQ5ab9XAOmyWmVRLQs9ALuO9Ub3mpM2TVF02rnvRvndKMlxcCkTpAXVlnY5SEPNxA1xdjq40XgGvb7wnpK2kOVKvnQDo1X0VtqVqazOpUVKnj8p0yA2luwmRA"
                  />
                )}
              </div>
            </div>
          </header>

          <div key={currentView} className="fade-in-section">
            {currentView === "dashboard" && <Dashboard onNavigate={(view) => setCurrentView(view)} />}
            {currentView === "profile" && <Profile onBack={() => setCurrentView("dashboard")} userProfile={userProfile} onProfileUpdate={setUserProfile} />}
            {currentView === "upload" && <Upload onBack={() => setCurrentView("dashboard")} />}
            {currentView === "timeline" && <Timeline userProfile={userProfile} />}
            {currentView === "vault" && <Vault />}
            {currentView === "medications" && <Medications />}
            {currentView === "reminders" && <Reminders />}
            {currentView === "appointments" && <Appointments />}
          </div>
        </main>

        {/* Contextual FAB */}
        <button 
          onClick={() => setCurrentView("upload")}
          className="fixed bottom-10 right-10 w-24 h-24 bg-[#e50914] text-white rounded-full flex items-center justify-center brick-shadow-heavy transition-all z-50 border-4 border-white lego-animate cursor-pointer hover:scale-110 active:scale-95"
          style={{ boxShadow: '0 10px 30px rgba(229, 9, 20, 0.4)' }}
        >
          <span className="material-symbols-outlined text-4xl font-black">add</span>
        </button>
      </div>
    </>
  );
}
