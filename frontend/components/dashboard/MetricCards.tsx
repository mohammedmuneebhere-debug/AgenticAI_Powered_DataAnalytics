"use client";

import React from "react";
import type { NormalizedDashboardData } from "@/lib/adapter";

interface MetricCardsProps {
  data: NormalizedDashboardData;
}

export default function MetricCards({ data }: MetricCardsProps) {
  const { metrics } = data;

  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
      {/* 1. Total Mentions */}
      <div className="bg-surface p-4 border border-surface-border/60 rounded-xl flex flex-col justify-between shadow-sm">
        <span className="font-mono text-[10px] uppercase text-slate-400 tracking-wider">
          {metrics.totalMentions.title}
        </span>
        <div className="flex items-baseline gap-2 mt-2">
          <span className="text-2xl font-bold text-[var(--text-primary)] tracking-tight">
            {metrics.totalMentions.value}
          </span>
          {metrics.totalMentions.subValue && (
            <span className="font-mono text-xs text-secondary font-bold">
              {metrics.totalMentions.subValue}
            </span>
          )}
        </div>
        <span className="font-sans text-[11px] text-slate-500 mt-1">
          {metrics.totalMentions.note}
        </span>
      </div>

      {/* 2. Engagement Volume */}
      <div className="bg-surface p-4 border border-surface-border/60 rounded-xl flex flex-col justify-between shadow-sm">
        <span className="font-mono text-[10px] uppercase text-slate-400 tracking-wider">
          {metrics.engagementVolume.title}
        </span>
        <div className="flex items-baseline gap-2 mt-2">
          <span className="text-2xl font-bold text-[var(--text-primary)] tracking-tight">
            {metrics.engagementVolume.value}
          </span>
          <span className="font-mono text-xs text-slate-400 font-medium">
            {metrics.engagementVolume.subValue}
          </span>
        </div>
        <span className="font-sans text-[11px] text-slate-500 mt-1">
          {metrics.engagementVolume.note}
        </span>
      </div>

      {/* 3. Sentiment Score */}
      <div className="bg-surface p-4 border border-surface-border/60 rounded-xl flex flex-col justify-between shadow-sm">
        <span className="font-mono text-[10px] uppercase text-slate-400 tracking-wider">
          {metrics.sentimentScore.title}
        </span>
        <div className="flex items-center gap-2 mt-2">
          <span className="text-2xl font-bold text-secondary tracking-tight">
            {metrics.sentimentScore.value}
          </span>
          {metrics.sentimentScore.badge && (
            <span className="font-mono text-[9px] uppercase bg-secondary-container/30 text-secondary border border-secondary/30 px-2 py-0.5 rounded-full font-bold">
              {metrics.sentimentScore.badge}
            </span>
          )}
        </div>
        <span className="font-sans text-[11px] text-slate-500 mt-1">
          {metrics.sentimentScore.note}
        </span>
      </div>

      {/* 4. Trend Velocity */}
      <div className="bg-surface p-4 border border-surface-border/60 rounded-xl flex flex-col justify-between shadow-sm">
        <span className="font-mono text-[10px] uppercase text-slate-400 tracking-wider">
          {metrics.trendVelocity.title}
        </span>
        <div className="flex items-baseline gap-2 mt-2">
          <span className="text-2xl font-bold text-[var(--text-primary)] tracking-tight">
            {metrics.trendVelocity.value.split("/")[0]}
            <span className="text-sm font-normal text-slate-500">/100</span>
          </span>
          {metrics.trendVelocity.badge && (
            <span className="font-mono text-[9px] uppercase bg-tertiary-container/40 text-tertiary border border-tertiary/30 px-2 py-0.5 rounded-full font-bold">
              {metrics.trendVelocity.badge}
            </span>
          )}
        </div>
        <span className="font-sans text-[11px] text-slate-500 mt-1">
          {metrics.trendVelocity.note}
        </span>
      </div>

      {/* 5. Active Sources */}
      <div className="bg-surface p-4 border border-surface-border/60 rounded-xl flex flex-col justify-between shadow-sm">
        <span className="font-mono text-[10px] uppercase text-slate-400 tracking-wider">
          {metrics.activeSources.title}
        </span>
        <div className="flex items-baseline gap-2 mt-2">
          <span className="text-2xl font-bold text-[var(--text-primary)] tracking-tight">
            {metrics.activeSources.value.split("/")[0]}
            <span className="text-sm font-normal text-slate-500">/{metrics.activeSources.value.split("/")[1] || "8"}</span>
          </span>
          <span className="font-mono text-xs text-secondary font-medium">
            {metrics.activeSources.subValue}
          </span>
        </div>
        <span className="font-sans text-[11px] text-slate-500 mt-1">
          {metrics.activeSources.note}
        </span>
      </div>
    </div>
  );
}
