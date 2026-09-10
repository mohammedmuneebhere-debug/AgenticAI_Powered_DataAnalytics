"use client";

import React from "react";
import type { NormalizedDashboardData } from "@/lib/adapter";

interface SentimentDriversModuleProps {
  data: NormalizedDashboardData;
}

export default function SentimentDriversModule({ data }: SentimentDriversModuleProps) {
  const { sentimentDrivers } = data;
  const { polarity, emotions } = sentimentDrivers;

  return (
    <div className="lg:col-span-4 bg-surface border border-surface-border/60 rounded-2xl flex flex-col overflow-hidden shadow-sm">
      <div className="flex items-center justify-between px-4 py-3 bg-surface-high/60 border-b border-surface-border/50">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-[18px] text-secondary">mood</span>
          <span className="font-mono text-xs uppercase text-slate-200 font-bold tracking-wider">
            Sentiment Drivers
          </span>
        </div>
        <span className="font-mono text-[10px] uppercase bg-secondary-container/30 text-secondary border border-secondary/30 px-2.5 py-0.5 rounded-full font-bold">
          {sentimentDrivers.netScore}
        </span>
      </div>

      <div className="p-4 flex-1 flex flex-col justify-between gap-4">
        {/* Segmented Solid Bar */}
        <div>
          <div className="flex justify-between items-center mb-2">
            <span className="font-mono text-[10px] uppercase text-slate-400">Polarity Distribution</span>
            <span className="font-mono text-xs text-slate-300 font-semibold">{sentimentDrivers.signalsCount}</span>
          </div>

          <div className="w-full h-3 flex rounded-full overflow-hidden bg-surface-lowest border border-surface-border">
            <div className="bg-secondary" style={{ width: `${polarity.positive}%` }} />
            <div className="bg-slate-500" style={{ width: `${polarity.neutral}%` }} />
            <div className="bg-error" style={{ width: `${polarity.negative}%` }} />
          </div>

          <div className="flex items-center justify-between mt-2 font-mono text-[11px] flex-wrap gap-1">
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-secondary" />
              <span className="text-slate-300">Positive ({polarity.positive}%)</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-slate-500" />
              <span className="text-slate-400">Neutral ({polarity.neutral}%)</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-error" />
              <span className="text-error">Negative ({polarity.negative}%)</span>
            </div>
          </div>
        </div>

        {/* Dominant Emotional Signatures */}
        <div className="flex flex-col gap-2">
          <span className="font-mono text-[10px] uppercase text-slate-400 tracking-wider">
            Dominant Emotional Signatures
          </span>

          <div className="flex flex-col gap-1.5">
            {emotions.map((emo, idx) => {
              let barColor = "bg-secondary";
              let iconColor = "text-secondary";
              if (emo.color === "slate") {
                barColor = "bg-slate-300";
                iconColor = "text-slate-300";
              } else if (emo.color === "tertiary") {
                barColor = "bg-tertiary";
                iconColor = "text-tertiary";
              } else if (emo.color === "error") {
                barColor = "bg-error";
                iconColor = "text-error";
              }

              return (
                <div
                  key={idx}
                  className="flex items-center justify-between p-2.5 bg-surface-lowest border border-surface-border/70 rounded-xl"
                >
                  <span className="font-sans text-xs text-slate-200 flex items-center gap-2">
                    <span className={`material-symbols-outlined text-[16px] ${iconColor}`}>
                      {emo.icon}
                    </span>
                    <span>{emo.label}</span>
                  </span>

                  <div className="flex items-center gap-3">
                    <div className="w-20 h-1.5 bg-surface-highest rounded-full overflow-hidden">
                      <div className={`h-1.5 rounded-full ${barColor}`} style={{ width: `${emo.percentage}%` }} />
                    </div>
                    <span className="font-mono text-xs text-[var(--text-primary)] font-semibold w-8 text-right">
                      {emo.percentage}%
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
