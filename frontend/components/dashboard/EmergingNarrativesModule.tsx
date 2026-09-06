"use client";

import React from "react";
import type { NormalizedDashboardData } from "@/lib/adapter";

interface EmergingNarrativesModuleProps {
  data: NormalizedDashboardData;
}

export default function EmergingNarrativesModule({ data }: EmergingNarrativesModuleProps) {
  const { narratives } = data;

  return (
    <div className="lg:col-span-5 bg-surface border border-surface-border/60 rounded-2xl flex flex-col overflow-hidden shadow-sm">
      <div className="flex items-center justify-between px-4 py-3 bg-surface-high/60 border-b border-surface-border/50">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-[18px] text-tertiary">chat</span>
          <span className="font-mono text-xs uppercase text-slate-200 font-bold tracking-wider">
            Emerging Narratives
          </span>
        </div>
        <span className="font-mono text-[10px] uppercase bg-surface-highest text-slate-200 border border-surface-border px-2.5 py-0.5 rounded-full font-bold">
          {narratives.length} Tracked
        </span>
      </div>

      <div className="p-3.5 flex flex-col gap-2 flex-1 justify-between">
        {narratives.map((item, idx) => (
          <div
            key={idx}
            className="p-2.5 bg-surface-lowest border border-surface-border/70 rounded-xl flex items-center justify-between gap-2"
          >
            <div className="flex items-center gap-2.5 min-w-0">
              <span className={`w-1.5 h-6 rounded-full shrink-0 ${item.color}`} />
              <div className="min-w-0">
                <div className="font-sans text-xs text-white font-semibold truncate">
                  {item.title}
                </div>
                <div className="font-sans text-[11px] text-slate-400 truncate">
                  {item.subtitle}
                </div>
              </div>
            </div>
            <span className="font-mono text-xs text-secondary font-bold shrink-0">
              {item.growth}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
