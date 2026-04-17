// src/components/Profile.tsx
"use client";
import React, { useState, useEffect } from 'react';
import anime from 'animejs';
import { usersApi, subscriptionsApi, type UserProfile as UserProfileType, type StorageStats, type SubscriptionUsage, ApiError } from '@/lib/api';

interface ProfileProps {
  onBack: () => void;
  userProfile?: UserProfileType | null;
  onProfileUpdate?: (profile: UserProfileType) => void;
}

export default function Profile({ onBack, userProfile, onProfileUpdate }: ProfileProps) {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [dateOfBirth, setDateOfBirth] = useState("");
  const [phone, setPhone] = useState("");
  const [gender, setGender] = useState("");
  const [bloodGroup, setBloodGroup] = useState("");
  const [storage, setStorage] = useState<StorageStats | null>(null);
  const [subscription, setSubscription] = useState<SubscriptionUsage | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState("");
  const [exporting, setExporting] = useState(false);

  // Populate form with real profile data
  useEffect(() => {
    if (userProfile) {
      setFullName(userProfile.full_name || "");
      setEmail(userProfile.email || "");
      setDateOfBirth(userProfile.date_of_birth || "");
      setPhone(userProfile.phone_number || "");
      setGender(userProfile.gender || "");
      setBloodGroup(userProfile.blood_group || "");
    }
  }, [userProfile]);

  // Fetch storage stats
  useEffect(() => {
    usersApi.getStorage().then(setStorage).catch(() => {});
    subscriptionsApi.getMySubscription().then(setSubscription).catch(() => {});
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setSaveMessage("");

    const btn = document.getElementById("profile-save-btn");
    if (btn) {
      anime({
        targets: btn,
        scale: [0.95, 1],
        duration: 300,
        easing: 'easeOutQuad'
      });
    }

    try {
      const updatedProfile = await usersApi.updateProfile({
        phone_number: phone || undefined,
        gender: gender || undefined,
        blood_group: bloodGroup || undefined,
      });
      setSaveMessage("Profile saved successfully!");
      if (onProfileUpdate) onProfileUpdate(updatedProfile);
    } catch (err) {
      const apiErr = err as ApiError;
      setSaveMessage(apiErr.message || "Failed to save profile.");
    } finally {
      setIsSaving(false);
      setTimeout(() => setSaveMessage(""), 3000);
    }
  };

  const formatBytes = (bytes: number): string => {
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
    if (bytes < 1073741824) return `${(bytes / 1048576).toFixed(1)} MB`;
    return `${(bytes / 1073741824).toFixed(2)} GB`;
  };

  return (
    <div className="max-w-4xl mx-auto pb-20 lego-animate">
      
      <div className="flex items-center gap-4 mb-8 ml-2">
        <button 
          onClick={onBack}
          className="w-10 h-10 bg-[var(--color-surface)] text-[var(--color-on-surface)] rounded-full brick-shadow flex items-center justify-center hover:brightness-110 active:translate-y-[2px] transition-all"
        >
          <span className="material-symbols-outlined">arrow_back</span>
        </button>
        <h2 className="font-headline tracking-tight font-black text-3xl text-[var(--color-secondary)]">
          Edit Patient Profile
        </h2>
      </div>

      {/* Save Message Banner */}
      {saveMessage && (
        <div className={`mb-6 px-6 py-3 rounded-lg font-bold text-sm flex items-center gap-2 brick-shadow ${
          saveMessage.includes("success") ? "bg-green-500 text-white" : "bg-red-500 text-white"
        }`}>
          <span className="material-symbols-outlined text-sm">
            {saveMessage.includes("success") ? "check_circle" : "error"}
          </span>
          {saveMessage}
        </div>
      )}

      <div className="bg-[var(--color-surface)] p-10 rounded-xl brick-shadow studs-light relative">
        <form onSubmit={handleSubmit} className="space-y-8 relative z-20">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="space-y-2">
              <label className="block font-black text-xs uppercase tracking-widest opacity-80">Full Name</label>
              <input 
                type="text" 
                value={fullName} 
                onChange={(e) => setFullName(e.target.value)}
                disabled
                className="w-full bg-white border-2 border-transparent rounded p-4 font-bold text-black focus:outline-none focus:border-[var(--color-secondary)] transition-all shadow-[inset_0_4px_6px_rgba(0,0,0,0.1),0_2px_0_rgba(255,255,255,1)] disabled:opacity-60" 
              />
              <p className="text-[9px] text-black/40 font-bold">Name cannot be changed after registration</p>
            </div>
            <div className="space-y-2">
              <label className="block font-black text-xs uppercase tracking-widest opacity-80">Date of Birth</label>
              <input 
                type="date" 
                value={dateOfBirth} 
                disabled
                className="w-full bg-white border-2 border-transparent rounded p-4 font-bold text-black focus:outline-none focus:border-[var(--color-secondary)] transition-all shadow-[inset_0_4px_6px_rgba(0,0,0,0.1),0_2px_0_rgba(255,255,255,1)] disabled:opacity-60" 
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="block font-black text-xs uppercase tracking-widest opacity-80">Connected Email Base</label>
            <input 
              type="email" 
              value={email} 
              disabled
              className="w-full bg-white border-2 border-transparent rounded p-4 font-bold text-black focus:outline-none focus:border-[var(--color-secondary)] transition-all shadow-[inset_0_4px_6px_rgba(0,0,0,0.1),0_2px_0_rgba(255,255,255,1)] disabled:opacity-60" 
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="space-y-2">
              <label className="block font-black text-xs uppercase tracking-widest opacity-80">Phone Number</label>
              <input 
                type="text" 
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="(555) 000-0000"
                className="w-full bg-white border-2 border-transparent rounded p-4 font-bold text-black focus:outline-none focus:border-[var(--color-secondary)] transition-all shadow-[inset_0_4px_6px_rgba(0,0,0,0.1),0_2px_0_rgba(255,255,255,1)]" 
              />
            </div>
            <div className="space-y-2">
              <label className="block font-black text-xs uppercase tracking-widest opacity-80">Gender</label>
              <select 
                value={gender}
                onChange={(e) => setGender(e.target.value)}
                className="w-full bg-white border-2 border-transparent rounded p-4 font-bold text-black focus:outline-none focus:border-[var(--color-secondary)] transition-all shadow-[inset_0_4px_6px_rgba(0,0,0,0.1),0_2px_0_rgba(255,255,255,1)]"
              >
                <option value="">Select</option>
                <option value="MALE">Male</option>
                <option value="FEMALE">Female</option>
                <option value="OTHER">Other</option>
              </select>
            </div>
            <div className="space-y-2">
              <label className="block font-black text-xs uppercase tracking-widest opacity-80">Blood Group</label>
              <select 
                value={bloodGroup}
                onChange={(e) => setBloodGroup(e.target.value)}
                className="w-full bg-white border-2 border-transparent rounded p-4 font-bold text-black focus:outline-none focus:border-[var(--color-secondary)] transition-all shadow-[inset_0_4px_6px_rgba(0,0,0,0.1),0_2px_0_rgba(255,255,255,1)]"
              >
                <option value="">Select</option>
                <option value="A+">A+</option>
                <option value="A-">A-</option>
                <option value="B+">B+</option>
                <option value="B-">B-</option>
                <option value="AB+">AB+</option>
                <option value="AB-">AB-</option>
                <option value="O+">O+</option>
                <option value="O-">O-</option>
              </select>
            </div>
          </div>

          {/* Account Info */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 pt-6 border-t-4 border-[var(--color-surface-container)]">
            <div className="bg-black/5 rounded-lg p-5">
              <p className="text-[10px] font-black uppercase tracking-widest opacity-50 mb-2">Account Status</p>
              <div className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${userProfile?.is_email_verified ? 'bg-green-500' : 'bg-orange-500'}`}></span>
                <span className="font-black text-sm">
                  {userProfile?.is_email_verified ? 'Email Verified' : 'Email Not Verified'}
                </span>
              </div>
              <div className="flex items-center gap-2 mt-2">
                <span className={`w-2 h-2 rounded-full ${userProfile?.mfa_enabled ? 'bg-green-500' : 'bg-gray-400'}`}></span>
                <span className="font-black text-sm">
                  {userProfile?.mfa_enabled ? 'MFA Enabled' : 'MFA Disabled'}
                </span>
              </div>
            </div>
            {storage && (
              <div className="bg-black/5 rounded-lg p-5">
                <p className="text-[10px] font-black uppercase tracking-widest opacity-50 mb-2">Storage Usage</p>
                <div className="flex items-end gap-2 mb-2">
                  <span className="font-black text-2xl">{storage.usage_percentage}%</span>
                  <span className="text-xs font-bold opacity-60 mb-1">
                    {formatBytes(storage.storage_used_bytes)} / {formatBytes(storage.storage_quota_bytes)}
                  </span>
                </div>
                <div className="w-full bg-black/10 h-2 rounded-full overflow-hidden">
                  <div 
                    className="bg-[var(--color-primary)] h-full rounded-full transition-all duration-500" 
                    style={{ width: `${Math.min(storage.usage_percentage, 100)}%` }}
                  ></div>
                </div>
                <p className="text-[9px] font-bold opacity-40 mt-2">{storage.records_count} records stored</p>
              </div>
            )}
          </div>

          <div className="pt-6 border-t-4 border-[var(--color-surface-container)] dashed flex justify-between items-center">
             <button
               type="button"
               disabled={exporting}
               onClick={async () => {
                 setExporting(true);
                 try {
                   const data = await usersApi.exportData();
                   const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
                   const url = URL.createObjectURL(blob);
                   const a = document.createElement('a');
                   a.href = url;
                   a.download = `vital-vault-export-${new Date().toISOString().slice(0,10)}.json`;
                   a.click();
                   URL.revokeObjectURL(url);
                 } catch { /* silent */ } finally { setExporting(false); }
               }}
               className="bg-black/10 text-black px-5 py-3 rounded font-headline uppercase tracking-widest text-xs font-black brick-shadow hover:bg-black/20 transition-all flex items-center gap-2 disabled:opacity-50"
             >
               <span className="material-symbols-outlined text-sm" style={{ color: 'inherit' }}>{exporting ? 'progress_activity' : 'download'}</span>
               {exporting ? 'Exporting...' : 'Export My Data (GDPR)'}
             </button>
             <button
               id="profile-save-btn"
               type="submit"
               disabled={isSaving}
               className="bg-[var(--color-primary)] text-white px-8 py-4 rounded font-headline uppercase tracking-widest text-sm font-black brick-shadow hover:brightness-110 active:translate-y-[4px] transition-all flex items-center justify-center gap-2 disabled:opacity-50"
             >
               {isSaving ? (
                 <><span className="material-symbols-outlined animate-spin">progress_activity</span> Saving...</>
               ) : (
                 <><span className="material-symbols-outlined">save</span> Save Block</>
               )}
             </button>
          </div>

          {/* Subscription Usage */}
          {subscription && (
            <div className="mt-6 pt-6 border-t-4 border-[var(--color-surface-container)]">
              <p className="text-[10px] font-black uppercase tracking-widest opacity-50 mb-4">Subscription — {subscription.tier} Tier</p>
              <div className="grid grid-cols-3 gap-4">
                {[
                  { label: 'Records', used: subscription.usage.records, max: subscription.limits.max_records, pct: subscription.percentages.records },
                  { label: 'Storage', used: `${subscription.usage.storage_mb}MB`, max: `${subscription.limits.max_storage_mb}MB`, pct: subscription.percentages.storage },
                  { label: 'Reminders', used: subscription.usage.reminders, max: subscription.limits.max_reminders, pct: subscription.percentages.reminders },
                ].map(stat => (
                  <div key={stat.label} className="bg-black/5 rounded-lg p-4">
                    <p className="text-[9px] font-black uppercase tracking-widest opacity-50 mb-2">{stat.label}</p>
                    <p className="font-black text-lg">{stat.used} <span className="text-xs opacity-40">/ {typeof stat.max === 'number' && stat.max < 0 ? '∞' : stat.max}</span></p>
                    <div className="w-full bg-black/10 h-1.5 rounded-full overflow-hidden mt-2">
                      <div
                        className={`h-full rounded-full transition-all duration-700 ${stat.pct > 80 ? 'bg-red-500' : stat.pct > 60 ? 'bg-amber-500' : 'bg-green-500'}`}
                        style={{ width: `${Math.min(stat.pct, 100)}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
              <div className="flex flex-wrap gap-2 mt-4">
                {subscription.limits.features.map(f => (
                  <span key={f} className="text-[8px] font-black uppercase tracking-widest px-2 py-1 rounded bg-[var(--color-primary)]/10 text-[var(--color-primary)] brick-shadow">{f}</span>
                ))}
              </div>
            </div>
          )}
        </form>
      </div>
    </div>
  );
}
