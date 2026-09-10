"use client";

import React from "react";
import type { NormalizedDashboardData } from "@/lib/adapter";

interface SourceContributionModuleProps {
  data: NormalizedDashboardData;
}

export default function SourceContributionModule({ data }: SourceContributionModuleProps) {
  const { sourceContribution } = data;

  return (
    <div className="lg:col-span-6 bg-surface border border-surface-border/60 rounded-2xl flex flex-col overflow-hidden shadow-sm">
      <div className="flex items-center justify-between px-4 py-3 bg-surface-high/60 border-b border-surface-border/50">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-[18px] text-slate-300">pie_chart</span>
          <span className="font-mono text-xs uppercase text-slate-200 font-bold tracking-wider">
            Source Contribution Ingestion
          </span>
        </div>
        <span className="font-mono text-[10px] text-secondary font-semibold uppercase tracking-wider">
          100% Ingestion Parity
        </span>
      </div>

      <div className="p-4 flex flex-col gap-2.5">
        {sourceContribution.map((source, idx) => (
          <div
            key={idx}
            className="flex flex-col bg-surface-lowest p-2.5 border border-surface-border/70 rounded-xl"
          >
            <div className="flex justify-between font-sans text-xs mb-1.5">
              <span className="font-medium text-slate-200 flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${source.dotColor}`} />
                <span>{source.name}</span>
              </span>
              <span className="text-slate-400">
                {source.signals} <strong className="text-[var(--text-primary)]">({source.percentage}%)</strong>
              </span>
            </div>

            <div className="w-full h-1.5 bg-surface-highest rounded-full overflow-hidden">
              <div
                className={`h-1.5 rounded-full ${source.dotColor}`}
                style={{ width: `${source.percentage}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
