"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { login, register } from "@/lib/auth";
import { ThemeProvider, useTheme } from "@/context/ThemeContext";

type Mode = "login" | "register";

export default function LoginPage() {
  return (
    <ThemeProvider>
      <LoginPanel />
    </ThemeProvider>
  );
}

function LoginPanel() {
  const router = useRouter();
  const { theme, toggleTheme, mounted } = useTheme();
  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      if (mode === "login") {
        await login(email, password);
      } else {
        await register(email, name, password);
      }
      router.replace("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setSubmitting(false);
    }
  };

  const switchMode = () => {
    setMode((prev) => (prev === "login" ? "register" : "login"));
    setError(null);
  };

  return (
    <div className="min-h-screen bg-[var(--bg-app)] flex items-center justify-center p-4">
      <div className="w-full max-w-5xl grid grid-cols-1 lg:grid-cols-2 rounded-3xl border border-[var(--border-subtle)] overflow-hidden shadow-2xl">
        {/* Brand panel */}
        <div className="hidden lg:flex flex-col justify-between bg-[var(--bg-sidebar)] border-r border-[var(--border-subtle)] p-10">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 bg-[var(--primary)] text-[var(--on-primary)] rounded-xl flex items-center justify-center">
              <span className="material-symbols-outlined text-[20px]">token</span>
            </div>
            <span className="font-bold text-lg tracking-tight text-[var(--text-primary)]">
              SOCIALIQ
            </span>
          </div>

          <div className="space-y-6">
            <h1 className="text-3xl font-bold leading-tight text-[var(--text-primary)]">
              From social signals to
              <br />
              actionable intelligence.
            </h1>
            <ul className="space-y-4 text-sm text-[var(--text-secondary)]">
              <li className="flex items-center gap-3">
                <span className="material-symbols-outlined text-[20px] text-[var(--secondary)]">hub</span>
                Multi-agent pipeline across X, Telegram, Instagram &amp; Pinterest
              </li>
              <li className="flex items-center gap-3">
                <span className="material-symbols-outlined text-[20px] text-[var(--secondary)]">insights</span>
                Evidence-backed sentiment, trends &amp; scenario analysis
              </li>
              <li className="flex items-center gap-3">
                <span className="material-symbols-outlined text-[20px] text-[var(--secondary)]">verified</span>
                Blockchain-anchored provenance for every insight
              </li>
            </ul>
          </div>

          <p className="text-[11px] font-mono uppercase tracking-wider text-[var(--text-muted)]">
            Agentic AI · Social Intelligence · SIH 2026
          </p>
        </div>

        {/* Auth panel */}
        <div className="bg-[var(--bg-surface)] p-8 sm:p-12 flex flex-col justify-center">
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-2.5 lg:hidden">
              <div className="w-8 h-8 bg-[var(--primary)] text-[var(--on-primary)] rounded-xl flex items-center justify-center">
                <span className="material-symbols-outlined text-[18px]">token</span>
              </div>
              <span className="font-bold tracking-tight text-[var(--text-primary)]">SOCIALIQ</span>
            </div>
            <button
              type="button"
              onClick={toggleTheme}
              title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
              aria-label="Toggle color theme"
              className="ml-auto w-9 h-9 rounded-full border border-[var(--border-subtle)] flex items-center justify-center text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] transition-colors"
            >
              {mounted && (
                <span className="material-symbols-outlined text-[18px]">
                  {theme === "dark" ? "light_mode" : "dark_mode"}
                </span>
              )}
            </button>
          </div>

          <h2 className="text-2xl font-bold text-[var(--text-primary)]">
            {mode === "login" ? "Welcome back" : "Create your account"}
          </h2>
          <p className="mt-2 text-sm text-[var(--text-secondary)]">
            {mode === "login"
              ? "Sign in to your SOCIALIQ workspace."
              : "Set up your SOCIALIQ intelligence workspace."}
          </p>

          <form onSubmit={handleSubmit} className="mt-8 space-y-4">
            {mode === "register" && (
              <div>
                <label htmlFor="name" className="block text-xs font-mono uppercase tracking-wider text-[var(--text-secondary)] mb-1.5">
                  Name
                </label>
                <div className="relative">
                  <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-[18px] text-[var(--text-muted)]">
                    person
                  </span>
                  <input
                    id="name"
                    type="text"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Alex Analyst"
                    className="w-full bg-[var(--bg-input)] border border-[var(--border-subtle)] rounded-xl pl-10 pr-4 py-2.5 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--border)] transition-colors"
                  />
                </div>
              </div>
            )}

            <div>
              <label htmlFor="email" className="block text-xs font-mono uppercase tracking-wider text-[var(--text-secondary)] mb-1.5">
                Email
              </label>
              <div className="relative">
                <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-[18px] text-[var(--text-muted)]">
                  mail
                </span>
                <input
                  id="email"
                  type="email"
                  required
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@company.com"
                  className="w-full bg-[var(--bg-input)] border border-[var(--border-subtle)] rounded-xl pl-10 pr-4 py-2.5 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--border)] transition-colors"
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-xs font-mono uppercase tracking-wider text-[var(--text-secondary)] mb-1.5">
                Password
              </label>
              <div className="relative">
                <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-[18px] text-[var(--text-muted)]">
                  lock
                </span>
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  required
                  minLength={8}
                  autoComplete={mode === "login" ? "current-password" : "new-password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="At least 8 characters"
                  className="w-full bg-[var(--bg-input)] border border-[var(--border-subtle)] rounded-xl pl-10 pr-11 py-2.5 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--border)] transition-colors"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((prev) => !prev)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
                >
                  <span className="material-symbols-outlined text-[18px]">
                    {showPassword ? "visibility_off" : "visibility"}
                  </span>
                </button>
              </div>
            </div>

            {error && (
              <div className="flex items-center gap-2 rounded-xl border border-[var(--error)]/40 bg-[var(--error)]/10 px-3.5 py-2.5 text-xs text-[var(--error)]">
                <span className="material-symbols-outlined text-[16px]">error</span>
                <span>{error}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={submitting}
              className="w-full flex items-center justify-center gap-2 rounded-xl bg-[var(--primary)] text-[var(--on-primary)] py-2.5 text-sm font-semibold hover:bg-[var(--primary-hover)] disabled:opacity-50 transition-colors"
            >
              {submitting ? (
                <span className="material-symbols-outlined text-[18px] animate-spin">progress_activity</span>
              ) : (
                <span className="material-symbols-outlined text-[18px]">
                  {mode === "login" ? "login" : "person_add"}
                </span>
              )}
              {mode === "login" ? "Sign in" : "Create account"}
            </button>
          </form>

          <p className="mt-6 text-center text-xs text-[var(--text-secondary)]">
            {mode === "login" ? "New to SOCIALIQ?" : "Already have an account?"}{" "}
            <button
              type="button"
              onClick={switchMode}
              className="font-semibold text-[var(--text-primary)] hover:underline"
            >
              {mode === "login" ? "Create an account" : "Sign in"}
            </button>
          </p>

          <p className="mt-8 text-center text-[10px] font-mono uppercase tracking-wider text-[var(--text-muted)]">
            OAuth sign-in coming soon · email &amp; password for now
          </p>
        </div>
      </div>
    </div>
  );
}
