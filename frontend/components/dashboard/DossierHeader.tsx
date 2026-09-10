"use client";

import React from "react";
import type { NormalizedDashboardData } from "@/lib/adapter";

interface DossierHeaderProps {
  data: NormalizedDashboardData;
}

export default function DossierHeader({ data }: DossierHeaderProps) {
  const handleShare = () => {
    if (navigator.share) {
      navigator.share({ title: `SocialIQ Dossier: ${data.topic}`, url: window.location.href });
    } else {
      navigator.clipboard.writeText(window.location.href);
      alert("Dossier link copied to clipboard.");
    }
  };

  const handleExportRaw = () => {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `SocialIQ_Dossier_${data.topic.replace(/\s+/g, "_")}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleSetAlert = () => {
    alert(`Realtime alert threshold configured for target: [${data.topic}]`);
  };

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 bg-surface p-4 rounded-2xl border border-surface-border/60 shadow-sm">
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2.5">
          <span className="text-2xl font-bold text-[var(--text-primary)] tracking-tight">{data.topic}</span>
          <span className="font-mono text-[10px] uppercase bg-secondary-container/30 text-secondary border border-secondary/30 px-2.5 py-1 rounded-full font-semibold">
            Live Social Intelligence
          </span>
        </div>

        <div className="h-4 w-px bg-surface-border hidden sm:block" />

        <div className="flex flex-wrap items-center gap-2 font-sans text-xs text-slate-400">
          <span className="bg-surface-high px-2.5 py-1 rounded-full border border-surface-border flex items-center gap-1.5 text-slate-300">
            <span className="material-symbols-outlined text-[13px] text-secondary">schedule</span>
            <span>{data.lastUpdated}</span>
          </span>
          <span className="bg-surface-high px-2.5 py-1 rounded-full border border-surface-border flex items-center gap-1.5 text-slate-300">
            <span className="material-symbols-outlined text-[13px] text-slate-300">analytics</span>
            <span>{data.signalsAnalyzed}</span>
          </span>
          <span className="bg-surface-high px-2.5 py-1 rounded-full border border-surface-border flex items-center gap-1.5 text-slate-300">
            <span className="material-symbols-outlined text-[13px] text-tertiary">hub</span>
            <span>{data.activeSourcesCount} active sources</span>
          </span>
        </div>
      </div>

      <div className="flex items-center gap-2 flex-wrap">
        <button
          type="button"
          onClick={handleShare}
          className="flex items-center gap-1.5 bg-surface-high hover:bg-surface-highest border border-surface-border text-slate-200 px-3.5 py-1.5 rounded-full font-sans text-xs transition-colors"
        >
          <span className="material-symbols-outlined text-[15px]">share</span>
          <span>Share Dossier</span>
        </button>

        <button
          type="button"
          onClick={handleExportRaw}
          className="flex items-center gap-1.5 bg-surface-high hover:bg-surface-highest border border-surface-border text-slate-200 px-3.5 py-1.5 rounded-full font-sans text-xs transition-colors"
        >
          <span className="material-symbols-outlined text-[15px]">file_download</span>
          <span>Export Raw Data</span>
        </button>

        <button
          type="button"
          onClick={handleSetAlert}
          className="flex items-center gap-1.5 bg-[var(--primary)] hover:bg-[var(--primary-hover)] text-[var(--on-primary)] px-4 py-1.5 rounded-full font-sans text-xs font-bold transition-colors"
        >
          <span className="material-symbols-outlined text-[15px]">notifications_active</span>
          <span>Set Alert</span>
        </button>
      </div>
    </div>
  );
}
