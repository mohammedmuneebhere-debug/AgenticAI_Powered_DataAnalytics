"use client";

import React from "react";
import { useSocialIQ } from "@/context/SocialIQContext";

interface TrendingTopic {
  rank: string;
  topic: string;
  icons: string[];
}

interface TrendingVectorsStripProps {
  onSelectTopic: (topic: string) => void;
  loadingTopic?: string;
}

export default function TrendingVectorsStrip({
  onSelectTopic,
  loadingTopic,
}: TrendingVectorsStripProps) {
  const { activeTopic, analysisCache, chatMessages } = useSocialIQ();
  const response = analysisCache[activeTopic] || [...chatMessages].reverse().find((message) => message.response)?.response;
  const trends = Array.isArray(response?.analytics?.trends && (response.analytics.trends as Record<string, unknown>).top_trends)
    ? ((response?.analytics?.trends as Record<string, unknown>).top_trends as Array<Record<string, unknown>>)
    : [];
  const trendingTopics: TrendingTopic[] = trends.slice(0, 5).map((trend, index) => ({
    rank: String(index + 1).padStart(2, "0"),
    topic: String(trend.topic || "Signal"),
    icons: [],
  }));

  return (
    <div className="flex flex-col bg-surface rounded-2xl border border-surface-border/60 overflow-hidden shadow-sm">
      {/* Sub-strip Header */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-surface-high/60 border-b border-surface-border/50">
        <div className="flex items-center gap-3">
          <button
            type="button"
            className="flex items-center gap-1.5 font-sans text-xs text-slate-400 hover:text-slate-200 transition-colors"
          >
            <span className="material-symbols-outlined text-[15px]">arrow_back</span>
            <span>Back to Trending Feed</span>
          </button>
          <div className="h-3 w-px bg-surface-border" />
          <span className="font-mono text-[11px] uppercase tracking-wider text-slate-300 font-semibold">
            Top 5 Trending Vectors
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 bg-secondary rounded-full" />
          <span className="font-mono text-[10px] text-secondary font-medium tracking-wider uppercase">
            Velocity Peak
          </span>
        </div>
      </div>

      {/* Horizontal Discovery Cells */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 divide-y md:divide-y-0 md:divide-x divide-surface-border/60 bg-surface-low">
        {trendingTopics.map((item) => {
          const isActive =
            activeTopic.toLowerCase().trim() === item.topic.toLowerCase().trim();
          const isLoading = loadingTopic === item.topic;

          return (
            <div
              key={item.rank}
              onClick={() => onSelectTopic(item.topic)}
              className={`flex items-center justify-between p-3 transition-colors cursor-pointer ${
                isActive ? "bg-surface-high" : "hover:bg-surface-high/50"
              }`}
            >
              <div className="flex items-center gap-2 min-w-0">
                <span
                  className={`font-mono text-[11px] font-bold ${
                    isActive ? "text-white" : "text-slate-500"
                  }`}
                >
                  {item.rank}
                </span>
                <span
                  className={`font-sans text-xs font-semibold truncate ${
                    isActive ? "text-white" : "text-slate-300 font-medium"
                  }`}
                >
                  {item.topic}
                </span>
                <span className="font-mono text-xs text-secondary font-bold">↗</span>
              </div>

              <div className="flex items-center gap-1.5 shrink-0">
                {isLoading ? (
                  <span className="material-symbols-outlined text-secondary text-[14px] animate-spin">
                    progress_activity
                  </span>
                ) : isActive ? (
                  <>
                    <span className="font-mono text-[9px] uppercase bg-white text-slate-950 px-2 py-0.5 rounded-full font-bold">
                      ACTIVE
                    </span>
                    <span className="material-symbols-outlined text-[14px] text-white">
                      arrow_forward
                    </span>
                  </>
                ) : (
                  <div className="flex items-center gap-1 text-slate-500">
                    {item.icons.map((ic, i) => (
                      <span key={i} className="material-symbols-outlined text-[14px]">
                        {ic}
                      </span>
                    ))}
                    <span className="material-symbols-outlined text-[14px] hover:text-slate-300">
                      chevron_right
                    </span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
