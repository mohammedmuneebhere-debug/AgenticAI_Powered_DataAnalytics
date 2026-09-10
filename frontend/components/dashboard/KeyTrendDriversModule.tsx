"use client";

import React from "react";
import type { NormalizedDashboardData } from "@/lib/adapter";

interface KeyTrendDriversModuleProps {
  data: NormalizedDashboardData;
}

export default function KeyTrendDriversModule({ data }: KeyTrendDriversModuleProps) {
  const { trendDrivers } = data;

  return (
    <div className="lg:col-span-7 bg-surface border border-surface-border/60 rounded-2xl flex flex-col overflow-hidden shadow-sm">
      <div className="flex items-center justify-between px-4 py-3 bg-surface-high/60 border-b border-surface-border/50">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-[18px] text-slate-300">offline_bolt</span>
          <span className="font-mono text-xs uppercase text-slate-200 font-bold tracking-wider">
            Key Trend Drivers
          </span>
        </div>
        <span className="font-mono text-[10px] text-slate-400 uppercase tracking-wider">
          Ranked by Signal Density
        </span>
      </div>

      <div className="p-3 divide-y divide-surface-border/50">
        {trendDrivers.map((driver) => {
          const isHigh = driver.strength === "High Strength";

          return (
            <div
              key={driver.rank}
              className="py-2.5 px-2 flex items-center justify-between gap-3 hover:bg-surface-high/30 transition-colors rounded-xl"
            >
              <div className="flex items-start gap-2.5 flex-1 min-w-0">
                <span
                  className={`font-mono text-xs font-bold mt-0.5 ${
                    isHigh ? "text-[var(--text-primary)]" : "text-slate-500"
                  }`}
                >
                  {driver.rank}
                </span>
                <div className="min-w-0">
                  <div className="font-sans text-xs text-[var(--text-primary)] font-semibold truncate">
                    {driver.title}
                  </div>
                  <div className="flex items-center gap-2 mt-0.5 font-mono text-[11px] text-slate-400 flex-wrap">
                    <span>
                      Source: <strong className="text-slate-300 font-medium">{driver.source}</strong>
                    </span>
                    <span>•</span>
                    <span className="text-secondary font-semibold">{driver.growth}</span>
                  </div>
                </div>
              </div>

              <span
                className={`font-mono text-[9px] uppercase px-2 py-0.5 rounded-full font-bold shrink-0 ${
                  isHigh
                    ? "bg-secondary-container/30 text-secondary border border-secondary/30"
                    : "bg-surface-high text-slate-400 border border-surface-border"
                }`}
              >
                {driver.strength}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
