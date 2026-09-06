"use client";

import React from "react";
import type { NormalizedDashboardData } from "@/lib/adapter";

interface NetworkIntelligenceModuleProps {
  data: NormalizedDashboardData;
}

export default function NetworkIntelligenceModule({ data }: NetworkIntelligenceModuleProps) {
  const { networkIntelligence } = data;

  return (
    <div className="lg:col-span-6 bg-surface border border-surface-border/60 rounded-2xl flex flex-col overflow-hidden shadow-sm">
      <div className="flex items-center justify-between px-4 py-3 bg-surface-high/60 border-b border-surface-border/50">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-[18px] text-secondary">hub</span>
          <span className="font-mono text-xs uppercase text-slate-200 font-bold tracking-wider">
            Network Intelligence
          </span>
        </div>
        <span className="font-mono text-[10px] text-slate-300">
          Graph Density: {networkIntelligence.graphDensity}
        </span>
      </div>

      <div className="p-4 flex flex-col justify-between flex-1 gap-3">
        {/* Pure Solid SVG Topology Graph (Zero Gradients) */}
        <div className="w-full h-44 bg-surface-lowest border border-surface-border/70 rounded-xl relative flex items-center justify-center overflow-hidden">
          <svg className="w-full h-full" viewBox="0 0 400 160">
            {/* Edges */}
            <line x1="80" y1="80" x2="200" y2="50" stroke="#292e3a" strokeWidth="1.5" />
            <line x1="80" y1="80" x2="210" y2="120" stroke="#292e3a" strokeWidth="1.5" />
            <line x1="200" y1="50" x2="320" y2="80" stroke="#292e3a" strokeWidth="1.5" />
            <line x1="210" y1="120" x2="320" y2="80" stroke="#292e3a" strokeWidth="1.5" />
            <line
              x1="200"
              y1="50"
              x2="210"
              y2="120"
              stroke="#292e3a"
              strokeWidth="1"
              strokeDasharray="2,2"
            />

            {/* Node 1: Dev Core */}
            <circle cx="80" cy="80" r="30" fill="#1a1d24" stroke="#ffffff" strokeWidth="2" />
            <text x="80" y="77" fill="#ffffff" fontSize="9" fontWeight="700" textAnchor="middle" fontFamily="Plus Jakarta Sans">
              DEV CORE
            </text>
            <text x="80" y="90" fill="#94a3b8" fontSize="8" textAnchor="middle" fontFamily="JetBrains Mono">
              54% Inf
            </text>

            {/* Node 2: Enterprise */}
            <circle cx="200" cy="50" r="26" fill="#13151b" stroke="#34D399" strokeWidth="1.5" />
            <text x="200" y="47" fill="#34D399" fontSize="8.5" fontWeight="700" textAnchor="middle" fontFamily="Plus Jakarta Sans">
              ENTERPRISE
            </text>
            <text x="200" y="59" fill="#64748B" fontSize="7.5" textAnchor="middle" fontFamily="JetBrains Mono">
              24% Inf
            </text>

            {/* Node 3: Tech VC */}
            <circle cx="210" cy="120" r="25" fill="#13151b" stroke="#FBBF24" strokeWidth="1.5" />
            <text x="210" y="117" fill="#FBBF24" fontSize="8.5" fontWeight="700" textAnchor="middle" fontFamily="Plus Jakarta Sans">
              TECH VC
            </text>
            <text x="210" y="129" fill="#64748B" fontSize="7.5" textAnchor="middle" fontFamily="JetBrains Mono">
              14% Inf
            </text>

            {/* Node 4: Media */}
            <circle cx="320" cy="80" r="25" fill="#13151b" stroke="#64748B" strokeWidth="1.5" />
            <text x="320" y="77" fill="#CBD5E1" fontSize="8.5" fontWeight="700" textAnchor="middle" fontFamily="Plus Jakarta Sans">
              MEDIA
            </text>
            <text x="320" y="89" fill="#64748B" fontSize="7.5" textAnchor="middle" fontFamily="JetBrains Mono">
              8% Inf
            </text>
          </svg>
        </div>

        {/* Quick Stats Strip */}
        <div className="grid grid-cols-3 gap-2">
          <div className="bg-surface-lowest p-2.5 border border-surface-border/70 rounded-xl">
            <span className="font-mono text-[9px] uppercase text-slate-500 block">Top Community</span>
            <span className="font-sans text-xs text-white font-semibold truncate block">
              {networkIntelligence.topCommunity}
            </span>
          </div>

          <div className="bg-surface-lowest p-2.5 border border-surface-border/70 rounded-xl">
            <span className="font-mono text-[9px] uppercase text-slate-500 block">Fastest Growing</span>
            <span className="font-sans text-xs text-secondary font-semibold truncate block">
              {networkIntelligence.fastestGrowing}
            </span>
          </div>

          <div className="bg-surface-lowest p-2.5 border border-surface-border/70 rounded-xl">
            <span className="font-mono text-[9px] uppercase text-slate-500 block">Top Influencer</span>
            <span className="font-sans text-xs text-tertiary font-semibold truncate block">
              {networkIntelligence.topInfluencer}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
