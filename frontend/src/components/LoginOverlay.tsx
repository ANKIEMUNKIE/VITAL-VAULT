"use client";

import React, { useState, useRef } from "react";
import anime from "animejs";
import { authApi, ApiError } from "@/lib/api";
import { setTokens, setStoredUser } from "@/lib/auth";

interface LoginOverlayProps {
  onLogin: () => void;
}

export default function LoginOverlay({ onLogin }: LoginOverlayProps) {
  const [isSignup, setIsSignup] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [dateOfBirth, setDateOfBirth] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const formRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const toggleSignup = (e: React.MouseEvent) => {
    e.preventDefault();
    if (!containerRef.current) return;

    anime({
      targets: containerRef.current,
      scale: [1, 0.9],
      opacity: [1, 0],
      duration: 200,
      easing: "easeInQuad",
      complete: () => {
        setIsSignup(!isSignup);
        setEmail("");
        setPassword("");
        setConfirmPassword("");
        setFullName("");
        setDateOfBirth("");
        setErrorMessage("");

        anime({
          targets: containerRef.current,
          scale: [0.9, 1],
          opacity: [0, 1],
          duration: 300,
          easing: "easeOutBack",
        });
      },
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage("");

    // Basic validation
    if (!email || !password) {
      setErrorMessage("Email and password are required.");
      triggerErrorShake();
      return;
    }

    if (isSignup) {
      if (password !== confirmPassword) {
        setErrorMessage("Passwords do not match!");
        triggerErrorShake();
        return;
      }
      if (!fullName) {
        setErrorMessage("Full name is required.");
        triggerErrorShake();
        return;
      }
      if (!dateOfBirth) {
        setErrorMessage("Date of birth is required.");
        triggerErrorShake();
        return;
      }
    }

    setIsLoading(true);

    try {
      if (isSignup) {
        // ── Register ──
        await authApi.register({
          email,
          password,
          full_name: fullName,
          date_of_birth: dateOfBirth,
        });

        // Auto-login after successful registration
        const loginResult = await authApi.login(email, password);
        setTokens({
          access_token: loginResult.access_token,
          refresh_token: loginResult.refresh_token,
        });
        setStoredUser(loginResult.user);
      } else {
        // ── Login ──
        const result = await authApi.login(email, password);
        setTokens({
          access_token: result.access_token,
          refresh_token: result.refresh_token,
        });
        setStoredUser(result.user);
      }

      // Success transition
      if (formRef.current) {
        anime({
          targets: formRef.current,
          opacity: [1, 0],
          translateY: [0, -100],
          duration: 500,
          easing: "easeInQuint",
          complete: () => {
            onLogin();
          },
        });
      } else {
        onLogin();
      }
    } catch (err) {
      const apiErr = err as ApiError;
      if (apiErr.status === 409) {
        setErrorMessage("This email is already registered. Try logging in.");
      } else if (apiErr.status === 401) {
        setErrorMessage("Invalid email or password.");
      } else if (apiErr.status === 422) {
        setErrorMessage("Please check your input fields.");
      } else if (apiErr.status === 423) {
        setErrorMessage("Account is locked. Try again later.");
      } else {
        setErrorMessage(apiErr.message || "Something went wrong. Please try again.");
      }
      triggerErrorShake();
    } finally {
      setIsLoading(false);
    }
  };

  const triggerErrorShake = () => {
    if (containerRef.current) {
      anime({
        targets: containerRef.current,
        translateX: [
          { value: -15, duration: 50 },
          { value: 15, duration: 50 },
          { value: -15, duration: 50 },
          { value: 15, duration: 50 },
          { value: 0, duration: 50 },
        ],
        easing: "linear",
      });
    }
  };

  const inputClass =
    "w-full bg-white border-2 border-transparent rounded p-4 font-bold text-black focus:outline-none focus:border-[var(--color-secondary)] transition-all placeholder:opacity-50 shadow-[inset_0_4px_6px_rgba(0,0,0,0.3),0_2px_0_rgba(255,255,255,0.7)]";

  return (
    <div
      id="login-view"
      className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-[var(--color-inverse-surface)]/80 backdrop-blur-md"
    >
      {/* Central Wrapper */}
      <div ref={formRef} className="w-full max-w-md mx-auto relative drop-shadow-2xl">
        <div ref={containerRef} className="w-full">
          {/* Error Banner */}
          {errorMessage && (
            <div className="mb-4 bg-red-500 text-white px-4 py-3 rounded-lg font-bold text-sm flex items-center gap-2 brick-shadow animate-in fade-in duration-300">
              <span className="material-symbols-outlined text-sm">error</span>
              {errorMessage}
            </div>
          )}

          {!isSignup ? (
            /* ==== LOGIN BLOCK ==== */
            <div className="bg-[var(--color-primary)] p-8 sm:p-10 rounded-xl brick-shadow-heavy studs-light flex flex-col w-full">
              <div className="flex items-center gap-3 mb-10 justify-center bg-[var(--color-primary)] p-3 rounded mx-4 shadow-[inset_0_-3px_0_rgba(0,0,0,0.2),inset_0_3px_0_rgba(255,255,255,0.2)]">
                <span className="material-symbols-outlined text-white text-3xl font-black rounded-full bg-[var(--color-inverse-surface)] p-2 brick-shadow">
                  vpn_key
                </span>
                <h1 className="text-4xl font-black font-headline tracking-tighter text-white drop-shadow-md">
                  Log In
                </h1>
              </div>

              <form className="space-y-6" onSubmit={handleSubmit}>
                <div className="relative group">
                  <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-[var(--color-on-surface)] opacity-40 group-focus-within:text-[var(--color-secondary)] group-focus-within:opacity-100 z-10 transition-all">
                    alternate_email
                  </span>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className={`${inputClass} pl-12`}
                    placeholder="Email Address"
                    disabled={isLoading}
                  />
                </div>

                <div className="relative group">
                  <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-[var(--color-on-surface)] opacity-40 group-focus-within:text-[var(--color-secondary)] group-focus-within:opacity-100 z-10 transition-all">
                    lock
                  </span>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className={`${inputClass} pl-12`}
                    placeholder="Password"
                    disabled={isLoading}
                  />
                </div>

                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full bg-[var(--color-tertiary)] text-[var(--color-on-tertiary)] py-4 rounded font-headline uppercase tracking-widest text-sm font-black brick-shadow hover:brightness-110 active:scale-95 transition-all flex items-center justify-center gap-2 mt-8 border-2 border-[var(--color-on-tertiary)]/20 shadow-[inset_0_-6px_0_rgba(0,0,0,0.2),0_6px_0_rgba(0,0,0,0.4)] hover:shadow-[inset_0_-4px_0_rgba(0,0,0,0.2),0_4px_0_rgba(0,0,0,0.4)] hover:translate-y-[2px] active:translate-y-[6px] active:shadow-[inset_0_0px_0_rgba(0,0,0,0.2),0_0px_0_rgba(0,0,0,0.4)] disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? (
                    <>
                      <span className="material-symbols-outlined animate-spin">
                        progress_activity
                      </span>{" "}
                      Authenticating...
                    </>
                  ) : (
                    <>
                      <span className="material-symbols-outlined">login</span> Unlock Vault
                    </>
                  )}
                </button>
              </form>

              <div className="text-center mt-8">
                <p className="text-white font-bold text-sm opacity-90 drop-shadow">
                  Need a new block ID?
                </p>
                <button
                  type="button"
                  onClick={toggleSignup}
                  disabled={isLoading}
                  className="mt-2 text-[var(--color-tertiary)] font-black uppercase text-xs tracking-widest hover:underline hover:text-white transition-all bg-[var(--color-inverse-surface)]/20 px-4 py-2 rounded"
                >
                  Snap into a new account &rarr;
                </button>
              </div>
            </div>
          ) : (
            /* ==== SIGN UP BLOCK ==== */
            <div className="bg-[var(--color-secondary)] p-8 sm:p-10 rounded-xl brick-shadow-heavy studs-dark flex flex-col w-full">
              <div className="flex items-center gap-3 mb-8 justify-center bg-[var(--color-secondary)] p-3 rounded mx-4 shadow-[inset_0_-3px_0_rgba(0,0,0,0.2),inset_0_3px_0_rgba(255,255,255,0.1)]">
                <span className="material-symbols-outlined text-[var(--color-secondary)] text-3xl font-black rounded-full bg-[var(--color-tertiary)] p-2 brick-shadow">
                  person_add
                </span>
                <h1 className="text-4xl font-black font-headline tracking-tighter text-white drop-shadow-md">
                  Sign Up
                </h1>
              </div>

              <form className="space-y-4" onSubmit={handleSubmit}>
                <div className="relative group">
                  <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-[var(--color-on-surface)] opacity-40 group-focus-within:text-[var(--color-primary)] group-focus-within:opacity-100 z-10 transition-all">
                    badge
                  </span>
                  <input
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className={`${inputClass} pl-12 py-3`}
                    placeholder="Full Name"
                    disabled={isLoading}
                  />
                </div>

                <div className="relative group">
                  <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-[var(--color-on-surface)] opacity-40 group-focus-within:text-[var(--color-primary)] group-focus-within:opacity-100 z-10 transition-all">
                    alternate_email
                  </span>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className={`${inputClass} pl-12 py-3`}
                    placeholder="Email Address"
                    disabled={isLoading}
                  />
                </div>

                <div className="relative group">
                  <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-[var(--color-on-surface)] opacity-40 group-focus-within:text-[var(--color-primary)] group-focus-within:opacity-100 z-10 transition-all">
                    calendar_today
                  </span>
                  <input
                    type="date"
                    value={dateOfBirth}
                    onChange={(e) => setDateOfBirth(e.target.value)}
                    className={`${inputClass} pl-12 py-3`}
                    placeholder="Date of Birth"
                    disabled={isLoading}
                  />
                </div>

                <div className="relative group">
                  <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-[var(--color-on-surface)] opacity-40 group-focus-within:text-[var(--color-primary)] group-focus-within:opacity-100 z-10 transition-all">
                    lock
                  </span>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className={`${inputClass} pl-12 py-3`}
                    placeholder="Create Password (min 8 chars)"
                    disabled={isLoading}
                  />
                </div>

                <div className="relative group">
                  <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-[var(--color-on-surface)] opacity-40 group-focus-within:text-[var(--color-primary)] group-focus-within:opacity-100 z-10 transition-all">
                    lock_reset
                  </span>
                  <input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className={`${inputClass} pl-12 py-3`}
                    placeholder="Confirm Password"
                    disabled={isLoading}
                  />
                </div>

                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full bg-[var(--color-success)] text-white py-4 rounded font-headline uppercase tracking-widest text-sm font-black brick-shadow hover:brightness-110 active:scale-95 transition-all flex items-center justify-center gap-2 mt-6 border-2 border-black/20 shadow-[inset_0_-6px_0_rgba(0,0,0,0.2),0_6px_0_rgba(0,0,0,0.4)] hover:shadow-[inset_0_-4px_0_rgba(0,0,0,0.2),0_4px_0_rgba(0,0,0,0.4)] hover:translate-y-[2px] active:translate-y-[6px] active:shadow-[inset_0_0px_0_rgba(0,0,0,0.2),0_0px_0_rgba(0,0,0,0.4)] disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? (
                    <>
                      <span className="material-symbols-outlined animate-spin">
                        progress_activity
                      </span>{" "}
                      Creating Account...
                    </>
                  ) : (
                    <>
                      <span className="material-symbols-outlined">how_to_reg</span>{" "}
                      Register Baseplate
                    </>
                  )}
                </button>
              </form>

              <div className="text-center mt-6">
                <p className="text-white/80 font-bold text-sm">Already hooked up?</p>
                <button
                  type="button"
                  onClick={toggleSignup}
                  disabled={isLoading}
                  className="mt-2 text-white font-black uppercase text-xs tracking-widest hover:underline transition-all bg-[var(--color-inverse-surface)]/20 px-4 py-2 rounded"
                >
                  &larr; Switch back to Log In
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
