"use client";

import React from "react";
import { useSocialIQ } from "@/context/SocialIQContext";

export default function TopNavigation() {
  const { activeMode, setActiveMode, activeTopic, toolConfig, setToolConfig } = useSocialIQ();

  const isAuto = toolConfig.mode === "auto";

  const toggleOrchestration = () => {
    setToolConfig((prev) => ({
      ...prev,
      mode: prev.mode === "auto" ? "manual" : "auto",
    }));
  };

  return (
    <header className="fixed top-0 left-0 right-0 z-50 h-16 bg-[#090a0f] border-b border-border-subtle flex items-center justify-between px-6 backdrop-blur-md">
      {/* Left: Logo + Mode Switcher + Active Context */}
      <div className="flex items-center gap-6">
        {/* Logo */}
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 bg-white text-black rounded-xl flex items-center justify-center shadow-sm">
            <span className="material-symbols-outlined text-[19px]">token</span>
          </div>
          <span className="font-bold text-lg tracking-tight text-white font-sans">SOCIALIQ</span>
        </div>

        <div className="h-4 w-px bg-border-subtle hidden sm:block" />

        {/* Mode Switcher */}
        <nav
          className="flex items-center gap-1.5 p-1 bg-[#13151b] border border-border-subtle rounded-full"
          aria-label="View Mode"
        >
          <button
            type="button"
            onClick={() => setActiveMode("chat")}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-full font-medium text-xs transition-all ${
              activeMode === "chat"
                ? "bg-white text-black shadow-sm font-semibold"
                : "text-on-surface-variant hover:text-white"
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
                ? "bg-white text-black shadow-sm font-semibold"
                : "text-on-surface-variant hover:text-white"
            }`}
            title="Dashboard Mode"
          >
            <span className="material-symbols-outlined text-[16px]">dashboard</span>
            <span>Dashboard Mode</span>
          </button>
        </nav>

        <div className="h-4 w-px bg-border-subtle hidden md:block" />

        {/* Active Context Tag */}
        <div className="hidden md:flex items-center gap-2">
          <span className="text-[11px] font-mono uppercase tracking-wider text-on-surface-variant">Context:</span>
          <span className="px-2.5 py-1 rounded-full bg-[#1a1d24] border border-border-subtle text-xs text-white font-medium">
            {activeTopic}
          </span>
        </div>
      </div>

      {/* Right: Telemetry & Status Badges */}
      <div className="flex items-center gap-3">
        {/* Live Status Pill */}
        <div className="flex items-center gap-2 bg-[#13151b] px-3 py-1.5 border border-border-subtle rounded-full">
          <span className="w-2 h-2 rounded-full bg-secondary animate-pulse" />
          <span className="text-[11px] font-mono tracking-wider text-secondary uppercase font-semibold">
            LIVE INTELLIGENCE
          </span>
        </div>

        {/* Auto Orchestration Pill */}
        <button
          type="button"
          onClick={toggleOrchestration}
          title="Toggle Auto/Manual Orchestration"
          className="hidden sm:flex items-center gap-2 bg-[#13151b] hover:bg-[#1a1d24] px-3 py-1.5 border border-border-subtle rounded-full transition-colors"
        >
          <span className="text-[11px] font-mono uppercase text-on-surface-variant">Auto Orchestration:</span>
          <span
            className={`text-[11px] font-mono font-semibold ${
              isAuto ? "text-secondary" : "text-tertiary"
            }`}
          >
            {isAuto ? "ON" : "OFF"}
          </span>
        </button>

        {/* User Avatar */}
        <button
          className="w-9 h-9 rounded-full bg-[#1a1d24] border border-border-subtle text-white flex items-center justify-center hover:border-slate-500 transition-colors shrink-0"
          type="button"
          title="Account Profile"
        >
          <span className="material-symbols-outlined text-[19px]">person</span>
        </button>
      </div>
    </header>
  );
}
