"use client";

import React from "react";
import type { NormalizedDashboardData } from "@/lib/adapter";

interface NetworkIntelligenceModuleProps {
  data: NormalizedDashboardData;
}

export default function NetworkIntelligenceModule({ data }: NetworkIntelligenceModuleProps) {
  const { networkIntelligence } = data;
  const positions = networkIntelligence.nodes.map((node, index) => ({
    node,
    x: networkIntelligence.nodes.length === 1 ? 200 : 55 + (index / Math.max(1, networkIntelligence.nodes.length - 1)) * 290,
    y: index % 2 === 0 ? 55 : 110,
  }));

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
            {positions.slice(1).map((position, index) => (
              <line key={`edge-${index}`} x1={positions[0].x} y1={positions[0].y} x2={position.x} y2={position.y} stroke="#292e3a" strokeWidth="1.5" />
            ))}
            {positions.map(({ node, x, y }, index) => (
              <g key={node.id}>
                <circle cx={x} cy={y} r={index === 0 ? 30 : 25} fill={index === 0 ? "#1a1d24" : "#13151b"} stroke={index === 0 ? "#ffffff" : ["#34D399", "#FBBF24", "#64748B"][index % 3]} strokeWidth={index === 0 ? 2 : 1.5} />
                <text x={x} y={y - 3} fill="#ffffff" fontSize="8" fontWeight="700" textAnchor="middle">{node.label.slice(0, 16).toUpperCase()}</text>
                <text x={x} y={y + 10} fill="#94a3b8" fontSize="7" textAnchor="middle">{node.inf}</text>
              </g>
            ))}
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
