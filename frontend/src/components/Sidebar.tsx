"use client";

import React from "react";
import type { UserProfile } from "@/lib/api";

interface SidebarProps {
  currentView: string;
  onNavigate: (view: string) => void;
  onLogout: () => void;
  userProfile?: UserProfile | null;
}

export default function Sidebar({ currentView, onNavigate, onLogout, userProfile }: SidebarProps) {
  const navItems = [
    { id: "dashboard", icon: "space_dashboard", label: "Dashboard" },
    { id: "vault", icon: "folder_special", label: "My Vault" },
    { id: "timeline", icon: "timeline", label: "Timeline" },
    { id: "medications", icon: "medication", label: "Medications" },
    { id: "reminders", icon: "alarm", label: "Reminders" },
    { id: "appointments", icon: "event", label: "Appointments" },
    { id: "upload", icon: "upload_file", label: "Upload Records" },
    { id: "profile", icon: "manage_accounts", label: "Edit Profile" },
  ];

  return (
    <aside className="h-screen w-64 fixed left-0 top-0 bg-white flex flex-col p-4 gap-2 z-50 brick-shadow-heavy">
      <div className="flex items-center gap-3 px-2 py-6 studs-light pt-10">
        <img
          src="/vital_vault_logo.png"
          alt="Vital Vault Logo"
          className="h-12 w-auto object-contain flex-shrink-0 relative z-20 ml-2"
        />
        <div className="relative z-20">
          <h1 className="text-2xl font-black text-[var(--color-primary)] font-headline tracking-tighter">
            Vault
          </h1>
          <p className="font-headline uppercase tracking-widest text-[9px] font-black opacity-60 text-black">
            Patient Portal
          </p>
        </div>
      </div>

      {/* User Info */}
      {userProfile && (
        <div className="px-3 py-2 mb-2 bg-black/5 rounded-lg relative z-20">
          <p className="font-black text-xs text-black truncate">{userProfile.full_name || "Patient"}</p>
          <p className="text-[9px] font-bold text-black/50 truncate">{userProfile.email}</p>
        </div>
      )}
      
      <nav className="flex-1 flex flex-col gap-2 mt-4 relative z-20 px-2 overflow-y-auto pb-4">
        {navItems.map((item) => {
          const isActive = currentView === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`flex items-center gap-3 px-3 py-3 rounded brick-shadow active:scale-[0.97] transition-all cursor-pointer ${
                isActive 
                  ? "bg-[var(--color-secondary)] text-white hover:brightness-110" 
                  : "bg-black/5 text-black hover:bg-black/10"
              }`}
            >
              <span className="material-symbols-outlined text-sm">{item.icon}</span>
              <span className="font-headline uppercase tracking-widest text-[10px] font-black">
                {item.label}
              </span>
            </button>
          )
        })}
      </nav>

      <div className="mt-auto flex flex-col gap-3 pt-6 border-t-4 border-[var(--color-surface-container)] relative z-20 mb-4 px-2">
        <button 
          onClick={() => onNavigate("upload")}
          className="w-full bg-[#FFFFF0] text-black py-4 rounded font-headline uppercase tracking-widest text-xs font-black lego-brick lego-interactive flex items-center justify-center gap-2 hover:bg-white"
        >
          <span className="material-symbols-outlined">add_box</span> Add Record
        </button>
        <button
          onClick={onLogout}
          className="w-full flex items-center justify-center gap-3 px-4 py-3 bg-[#FFFFF0] text-black rounded lego-brick lego-interactive hover:bg-white"
        >
          <span className="material-symbols-outlined">logout</span>
          <span className="font-headline uppercase tracking-widest text-xs font-black">
            Log Out
          </span>
        </button>
      </div>
    </aside>
  );
}
