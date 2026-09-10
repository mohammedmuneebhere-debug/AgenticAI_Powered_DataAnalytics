"use client";

import React from "react";
import type { NormalizedDashboardData } from "@/lib/adapter";

interface ExecutiveSynthesisProps {
  data: NormalizedDashboardData;
}

export default function ExecutiveSynthesis({ data }: ExecutiveSynthesisProps) {
  const { executiveSynthesis } = data;

  return (
    <div className="bg-surface-high border border-surface-border p-5 rounded-2xl relative overflow-hidden shadow-sm">
      <div className="flex flex-wrap items-center justify-between pb-3 mb-3 border-b border-surface-border gap-2">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-lg bg-surface-highest flex items-center justify-center">
            <span className="material-symbols-outlined text-[var(--text-primary)] text-[16px]">neurology</span>
          </div>
          <span className="font-mono text-xs uppercase text-[var(--text-primary)] font-bold tracking-wider">
            {executiveSynthesis.title}
          </span>
        </div>

        <div className="flex items-center gap-3 font-mono text-[11px] flex-wrap">
          <span className="text-slate-400">
            Confidence: <span className="text-secondary font-bold">{executiveSynthesis.confidence}%</span>
          </span>
          <span className="text-surface-border">|</span>
          <span className="text-slate-400">
            Sources: <span className="text-slate-200 font-medium">{executiveSynthesis.sourcesCount} verified</span>
          </span>
          <span className="text-surface-border">|</span>
          <span className="text-slate-400">
            Signals Analyzed: <span className="text-slate-200 font-medium">{executiveSynthesis.signalsCount.toLocaleString()}</span>
          </span>
        </div>
      </div>

      <p className="font-sans text-sm text-slate-200 leading-relaxed">
        {executiveSynthesis.text}
      </p>

      <div className="flex flex-wrap items-center gap-2 mt-4">
        <span className="font-mono text-[10px] uppercase text-slate-400">Primary Vectors:</span>
        {executiveSynthesis.primaryVectors.map((vec, i) => (
          <span
            key={i}
            className="font-mono text-[11px] bg-surface-lowest text-slate-200 px-3 py-1 border border-surface-border rounded-full font-medium"
          >
            {vec}
          </span>
        ))}
      </div>
    </div>
  );
}
