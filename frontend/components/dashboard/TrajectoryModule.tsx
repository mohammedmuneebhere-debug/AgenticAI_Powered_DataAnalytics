"use client";

import React, { useState } from "react";
import type { NormalizedDashboardData } from "@/lib/adapter";

interface TrajectoryModuleProps {
  data: NormalizedDashboardData;
}

export default function TrajectoryModule({ data }: TrajectoryModuleProps) {
  const [activeRange, setActiveRange] = useState<"1H" | "24H" | "7D" | "30D">("24H");
  const { trajectory } = data;

  return (
    <div className="lg:col-span-8 bg-surface border border-surface-border/60 rounded-2xl flex flex-col overflow-hidden shadow-sm">
      <div className="flex items-center justify-between px-4 py-3 bg-surface-high/60 border-b border-surface-border/50">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-[18px] text-white">show_chart</span>
          <span className="font-mono text-xs uppercase text-slate-200 font-bold tracking-wider">
            Conversation Volume &amp; Trajectory
          </span>
        </div>
        <div className="flex items-center gap-1 bg-surface-lowest p-1 border border-surface-border rounded-full">
          {(["1H", "24H", "7D", "30D"] as const).map((range) => (
            <button
              key={range}
              onClick={() => setActiveRange(range)}
              type="button"
              className={`px-2.5 py-0.5 font-mono text-[10px] rounded-full transition-colors ${
                activeRange === range
                  ? "bg-white text-slate-950 font-bold"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              {range}
            </button>
          ))}
        </div>
      </div>

      <div className="p-4 flex-1 flex flex-col justify-between">
        <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
          <div className="flex items-center gap-4">
            <div>
              <div className="font-mono text-[10px] uppercase text-slate-500">Peak Volume (14:00 UTC)</div>
              <div className="font-sans text-lg font-bold text-white">{trajectory.peakVolume}</div>
            </div>
            <div className="h-6 w-px bg-surface-border" />
            <div>
              <div className="font-mono text-[10px] uppercase text-slate-500">Mean Velocity</div>
              <div className="font-sans text-lg font-bold text-secondary">{trajectory.meanVelocity}</div>
            </div>
          </div>
          <div className="flex items-center gap-2 bg-surface-lowest px-3 py-1 rounded-full border border-surface-border">
            <span className="w-2 h-2 rounded-full bg-white" />
            <span className="font-sans text-xs text-slate-200 font-medium">
              {trajectory.spikeEvent}
            </span>
          </div>
        </div>

        {/* Solid SVG Line & Area (Zero Gradients) */}
        <div className="w-full h-56 relative bg-surface-lowest border border-surface-border/70 rounded-xl p-3 flex flex-col justify-between overflow-hidden">
          <div className="absolute inset-0 grid grid-rows-4 divide-y divide-surface-border/40 pointer-events-none">
            <div /><div /><div /><div />
          </div>

          <svg className="w-full h-full relative z-10" preserveAspectRatio="none" viewBox="0 0 700 180">
            {/* Step / Volume reference bars */}
            <rect x="50" y="140" width="10" height="30" rx="3" fill="#1e222d" />
            <rect x="110" y="125" width="10" height="45" rx="3" fill="#1e222d" />
            <rect x="170" y="110" width="10" height="60" rx="3" fill="#1e222d" />
            <rect x="230" y="95" width="10" height="75" rx="3" fill="#1e222d" />
            <rect x="290" y="80" width="10" height="90" rx="3" fill="#1e222d" />
            <rect x="350" y="30" width="10" height="140" rx="3" fill="#3b4252" opacity="0.4" />
            <rect x="410" y="45" width="10" height="125" rx="3" fill="#1e222d" />
            <rect x="470" y="60" width="10" height="110" rx="3" fill="#1e222d" />
            <rect x="530" y="55" width="10" height="115" rx="3" fill="#1e222d" />
            <rect x="590" y="40" width="10" height="130" rx="3" fill="#1e222d" />
            <rect x="650" y="32" width="10" height="138" rx="3" fill="#1e222d" />

            {/* Solid Line Chart (Monochrome silver) */}
            <polyline
              fill="none"
              stroke="#cbd5e1"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              points="10,150 70,142 130,130 190,118 250,95 310,85 360,28 420,44 480,58 540,52 600,38 670,26 690,20"
            />

            {/* Marker for Spike Event */}
            <line
              x1="360"
              y1="180"
              x2="360"
              y2="28"
              stroke="#94a3b8"
              strokeWidth="1.5"
              strokeDasharray="3,3"
            />
            <circle cx="360" cy="28" r="4.5" fill="#13151b" stroke="#ffffff" strokeWidth="2" />
          </svg>

          {/* Timeline X-Axis */}
          <div className="flex justify-between font-mono text-[10px] text-slate-500 pt-2 border-t border-surface-border/50 relative z-10">
            <span>00:00 UTC</span>
            <span>04:00</span>
            <span>08:00</span>
            <span className="text-white font-semibold">12:00 (EVENT SPIKE)</span>
            <span>16:00</span>
            <span>20:00</span>
            <span>CURRENT</span>
          </div>
        </div>
      </div>
    </div>
  );
}
