"use client";

import React, { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useSocialIQ } from "@/context/SocialIQContext";
import { useTheme } from "@/context/ThemeContext";
import { getStoredUser, logout, type User } from "@/lib/auth";

export default function TopNavigation() {
  const { activeMode, setActiveMode, activeTopic, toolConfig, setToolConfig } = useSocialIQ();
  const { theme, toggleTheme, mounted } = useTheme();
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setUser(getStoredUser());
  }, []);

  useEffect(() => {
    const close = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, []);

  const isAuto = toolConfig.mode === "auto";

  const toggleOrchestration = () => {
    setToolConfig((prev) => ({
      ...prev,
      mode: prev.mode === "auto" ? "manual" : "auto",
    }));
  };

  return (
    <header className="fixed top-0 left-0 right-0 z-50 h-16 bg-[var(--bg-app)] border-b border-[var(--border-subtle)] flex items-center justify-between px-6 backdrop-blur-md">
      {/* Left: Logo + Mode Switcher + Active Context */}
      <div className="flex items-center gap-6">
        {/* Logo */}
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 bg-[var(--primary)] text-[var(--on-primary)] rounded-xl flex items-center justify-center shadow-sm">
            <span className="material-symbols-outlined text-[19px]">token</span>
          </div>
          <span className="font-bold text-lg tracking-tight text-[var(--text-primary)] font-sans">SOCIALIQ</span>
        </div>

        <div className="h-4 w-px bg-[var(--border-subtle)] hidden sm:block" />

        {/* Mode Switcher */}
        <nav
          className="flex items-center gap-1.5 p-1 bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-full"
          aria-label="View Mode"
        >
          <button
            type="button"
            onClick={() => setActiveMode("chat")}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-full font-medium text-xs transition-all ${
              activeMode === "chat"
                ? "bg-[var(--primary)] text-[var(--on-primary)] shadow-sm font-semibold"
                : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
            }`}
            title="Chat Mode"
          >
            <span className="material-symbols-outlined text-[16px]">chat</span>
            <span>Chat Mode</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveMode("dashboard")}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-full font-medium text-xs transition-all ${
              activeMode === "dashboard"
                ? "bg-[var(--primary)] text-[var(--on-primary)] shadow-sm font-semibold"
                : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
            }`}
            title="Dashboard Mode"
          >
            <span className="material-symbols-outlined text-[16px]">dashboard</span>
            <span>Dashboard Mode</span>
          </button>
        </nav>

        <div className="h-4 w-px bg-[var(--border-subtle)] hidden md:block" />

        {/* Active Context Tag */}
        <div className="hidden md:flex items-center gap-2">
          <span className="text-[11px] font-mono uppercase tracking-wider text-[var(--text-secondary)]">Context:</span>
          <span className="px-2.5 py-1 rounded-full bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-xs text-[var(--text-primary)] font-medium">
            {activeTopic}
          </span>
        </div>
      </div>

      {/* Right: Telemetry & Status Badges */}
      <div className="flex items-center gap-3">
        {/* Live Status Pill */}
        <div className="flex items-center gap-2 bg-[var(--bg-surface)] px-3 py-1.5 border border-[var(--border-subtle)] rounded-full">
          <span className="w-2 h-2 rounded-full bg-[var(--secondary)] animate-pulse" />
          <span className="text-[11px] font-mono tracking-wider text-[var(--secondary)] uppercase font-semibold">
            LIVE INTELLIGENCE
          </span>
        </div>

        {/* Auto Orchestration Pill */}
        <button
          type="button"
          onClick={toggleOrchestration}
          title="Toggle Auto/Manual Orchestration"
          className="hidden sm:flex items-center gap-2 bg-[var(--bg-surface)] hover:bg-[var(--bg-elevated)] px-3 py-1.5 border border-[var(--border-subtle)] rounded-full transition-colors"
        >
          <span className="text-[11px] font-mono uppercase text-[var(--text-secondary)]">Auto Orchestration:</span>
          <span
            className={`text-[11px] font-mono font-semibold ${
              isAuto ? "text-[var(--secondary)]" : "text-[var(--tertiary)]"
            }`}
          >
            {isAuto ? "ON" : "OFF"}
          </span>
        </button>

        {/* Theme Toggle */}
        <button
          type="button"
          onClick={toggleTheme}
          title={mounted && theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
          aria-label="Toggle color theme"
          className="w-9 h-9 rounded-full bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-[var(--text-primary)] flex items-center justify-center hover:border-[var(--border)] transition-colors shrink-0"
        >
          {mounted && (
            <span className="material-symbols-outlined text-[19px]">
              {theme === "dark" ? "light_mode" : "dark_mode"}
            </span>
          )}
        </button>

        {/* User Menu */}
        <div className="relative" ref={menuRef}>
          <button
            className="w-9 h-9 rounded-full bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-[var(--text-primary)] flex items-center justify-center hover:border-[var(--border)] transition-colors shrink-0"
            type="button"
            title="Account"
            aria-haspopup="menu"
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((prev) => !prev)}
          >
            <span className="material-symbols-outlined text-[19px]">person</span>
          </button>
          {menuOpen && (
            <div
              role="menu"
              className="absolute right-0 top-11 w-56 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] shadow-xl py-2 z-50"
            >
              <div className="px-4 py-2 border-b border-[var(--border-subtle)]">
                <p className="text-sm font-semibold text-[var(--text-primary)] truncate">
                  {user?.name || "Signed in user"}
                </p>
                <p className="text-xs text-[var(--text-secondary)] truncate">{user?.email}</p>
              </div>
              <button
                type="button"
                role="menuitem"
                onClick={() => {
                  setMenuOpen(false);
                  logout();
                }}
                className="w-full flex items-center gap-2 px-4 py-2 text-sm text-[var(--error)] hover:bg-[var(--bg-elevated)] transition-colors"
              >
                <span className="material-symbols-outlined text-[17px]">logout</span>
                Sign out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
