"use client";

import React from "react";
import type { NormalizedDashboardData } from "@/lib/adapter";
import InterestByRegion from "./InterestByRegion";

interface AudienceSegmentsModuleProps {
  data: NormalizedDashboardData;
}

export default function AudienceSegmentsModule({ data }: AudienceSegmentsModuleProps) {
  const { audienceSegments } = data;

  return (
    <div className="lg:col-span-6 bg-surface border border-surface-border/60 rounded-2xl flex flex-col overflow-hidden shadow-sm">
      <div className="flex items-center justify-between px-4 py-3 bg-surface-high/60 border-b border-surface-border/50">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-[18px] text-tertiary">groups</span>
          <span className="font-mono text-xs uppercase text-slate-200 font-bold tracking-wider">
            Estimated Audience Segments
          </span>
        </div>
        <span className="font-mono text-[10px] text-tertiary uppercase tracking-wider">
          Demographic Inference
        </span>
      </div>

      <div className="p-4 flex flex-col justify-between flex-1 gap-3">
        <div className="space-y-2.5">
          {audienceSegments.map((segment, idx) => (
            <div key={idx}>
              <div className="flex justify-between font-sans text-xs mb-1.5">
                <span className="text-slate-200 font-medium">{segment.label}</span>
                <span className="font-mono text-xs text-white font-bold">{segment.percentage}%</span>
              </div>
              <div className="w-full h-1.5 bg-surface-highest rounded-full overflow-hidden">
                <div
                  className={`h-1.5 rounded-full ${segment.barColor}`}
                  style={{ width: `${segment.percentage}%` }}
                />
              </div>
            </div>
          ))}
        </div>

        <InterestByRegion
          regions={data.googleTrends.regions}
          relatedTopics={data.googleTrends.relatedTopics}
          relatedQueries={data.googleTrends.relatedQueries}
        />

        <div className="p-2.5 bg-surface-lowest border border-surface-border/70 rounded-xl flex items-center gap-2">
          <span className="material-symbols-outlined text-slate-500 text-[16px] shrink-0">info</span>
          <span className="font-sans text-[11px] text-slate-400 leading-tight">
            AI-inferred aggregate audience estimates calculated from syntax and engagement telemetry.
          </span>
        </div>
      </div>
    </div>
  );
}
