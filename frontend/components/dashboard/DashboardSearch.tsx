"use client";

import React, { useState } from "react";
import { useSocialIQ } from "@/context/SocialIQContext";

interface DashboardSearchProps {
  onAnalyze: (query: string) => void;
  loading: boolean;
}

export default function DashboardSearch({ onAnalyze, loading }: DashboardSearchProps) {
  const { activeTopic, setActiveTopic, toolConfig } = useSocialIQ();
  const [searchValue, setSearchValue] = useState(activeTopic);
  const [showSourcesDropdown, setShowSourcesDropdown] = useState(false);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchValue.trim()) {
      setActiveTopic(searchValue.trim());
      onAnalyze(searchValue.trim());
    }
  };

  const handleClear = () => {
    setSearchValue("");
  };

  return (
    <div className="bg-surface rounded-2xl p-3 border border-surface-border/60 shadow-sm">
      <form onSubmit={handleSearchSubmit} className="flex flex-wrap items-center gap-2.5">
        <div className="flex-1 min-w-[280px] flex items-center bg-surface-lowest border border-surface-border/80 px-4 py-2 rounded-xl focus-within:border-white/60 transition-colors">
          <span className="material-symbols-outlined text-on-surface text-[18px] mr-2">search</span>
          <span className="font-mono text-xs text-on-surface-variant mr-2 select-none">&gt;</span>
          <input
            type="text"
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            placeholder="Search topic, entity, ticker or vector query..."
            className="bg-transparent text-[var(--text-primary)] font-sans text-sm w-full focus:outline-none placeholder:text-outline"
          />
          {searchValue && (
            <button
              type="button"
              onClick={handleClear}
              className="text-outline hover:text-on-surface ml-2 flex items-center transition-colors"
            >
              <span className="material-symbols-outlined text-[16px]">cancel</span>
            </button>
          )}
        </div>

        {/* Source selector */}
        <div className="relative">
          <button
            type="button"
            onClick={() => setShowSourcesDropdown((p) => !p)}
            className="flex items-center gap-2 bg-surface-high hover:bg-surface-highest border border-surface-border px-3.5 py-2 rounded-xl transition-colors font-sans text-xs font-medium text-on-surface"
          >
            <span className="material-symbols-outlined text-[16px] text-secondary">tune</span>
            <span>All Sources ({toolConfig.enabled_sources?.length || 0} active)</span>
            <span className="material-symbols-outlined text-[16px] text-on-surface-variant">expand_more</span>
          </button>

          {showSourcesDropdown && (
            <div className="absolute top-full mt-1.5 right-0 w-52 bg-surface-high border border-surface-border rounded-xl p-2 shadow-xl z-30 space-y-1 text-xs">
              <div className="px-2 py-1 font-mono text-[10px] text-on-surface-variant uppercase tracking-wider">
                Active Ingestion Feeds
              </div>
              <div className="flex items-center justify-between px-2 py-1.5 hover:bg-surface-highest rounded-lg text-on-surface">
                <span>X (Twitter) Firehose</span>
                <span className="text-[10px] font-mono text-secondary">LIVE</span>
              </div>
              <div className="flex items-center justify-between px-2 py-1.5 hover:bg-surface-highest rounded-lg text-on-surface">
                <span>Reddit Discussions</span>
                <span className="text-[10px] font-mono text-secondary">LIVE</span>
              </div>
              <div className="flex items-center justify-between px-2 py-1.5 hover:bg-surface-highest rounded-lg text-on-surface">
                <span>Google Search Pulse</span>
                <span className="text-[10px] font-mono text-secondary">LIVE</span>
              </div>
              <div className="flex items-center justify-between px-2 py-1.5 hover:bg-surface-highest rounded-lg text-on-surface">
                <span>Telegram Channels</span>
                <span className="text-[10px] font-mono text-secondary">LIVE</span>
              </div>
            </div>
          )}
        </div>

        {/* Analyze button */}
        <button
          type="submit"
          disabled={loading || !searchValue.trim()}
          className="flex items-center gap-1.5 bg-[var(--primary)] hover:bg-[var(--primary-hover)] disabled:opacity-50 text-[var(--on-primary)] px-4 py-2 rounded-xl font-sans text-xs font-bold transition-colors shrink-0"
        >
          <span className={`material-symbols-outlined text-[16px] ${loading ? "animate-spin" : ""}`}>
            {loading ? "progress_activity" : "bolt"}
          </span>
          <span>{loading ? "Analyzing..." : "Analyze"}</span>
        </button>
      </form>

      <div className="flex items-center justify-between px-2 pt-2.5 flex-wrap gap-1">
        <span className="font-sans text-xs text-on-surface-variant">
          Search any topic, brand, person, market or trend, or select from Trending Now.
        </span>
        <span className="font-mono text-[10px] text-on-surface tracking-wider uppercase">
          Live query ingestion
        </span>
      </div>
    </div>
  );
}
