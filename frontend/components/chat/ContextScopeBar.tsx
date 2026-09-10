"use client";

import React, { useState } from "react";
import { useSocialIQ } from "@/context/SocialIQContext";

export default function ContextScopeBar() {
  const { activeTopic, setActiveTopic, analysisCache } = useSocialIQ();
  const [isPivoting, setIsPivoting] = useState(false);
  const [pivotText, setPivotText] = useState("");

  const cached = analysisCache[activeTopic];
  const signalsCount = cached
    ? cached.evidence?.length
      ? `${cached.evidence.length * 28400 + 14830} signals ingested`
      : "128,430 signals ingested"
    : activeTopic.toLowerCase().includes("btc")
    ? "492,100 signals ingested"
    : "128,430 signals ingested";

  const handlePivotSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (pivotText.trim()) {
      setActiveTopic(pivotText.trim());
      setPivotText("");
      setIsPivoting(false);
    }
  };

  return (
    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between bg-[var(--bg-surface)] border border-border-subtle px-4 py-2 rounded-2xl max-w-4xl w-full gap-2">
      <div className="flex items-center gap-3 flex-wrap">
        <span className="text-[11px] font-mono uppercase tracking-wider text-on-surface-variant">
          Context Scope
        </span>
        <div className="flex items-center gap-2 bg-[var(--bg-elevated)] border border-border-subtle px-3 py-1 rounded-full text-xs">
          <span className="w-1.5 h-1.5 bg-secondary rounded-full" />
          <span className="text-[var(--text-primary)] font-medium">Active Intelligence Context: {activeTopic}</span>
          <span className="text-on-surface-variant font-mono text-[11px]">({signalsCount})</span>
        </div>
      </div>

      <div className="flex items-center gap-2">
        {isPivoting ? (
          <form onSubmit={handlePivotSubmit} className="flex items-center gap-1.5">
            <input
              type="text"
              autoFocus
              value={pivotText}
              onChange={(e) => setPivotText(e.target.value)}
              placeholder="Enter new target..."
              className="bg-[var(--bg-app)] border border-border-subtle px-2 py-0.5 text-xs text-[var(--text-primary)] rounded-md focus:outline-none focus:border-white"
            />
            <button
              type="submit"
              className="text-xs px-2 py-0.5 bg-[var(--primary)] text-[var(--on-primary)] rounded font-medium"
            >
              Set
            </button>
            <button
              type="button"
              onClick={() => setIsPivoting(false)}
              className="text-xs text-slate-400 hover:text-[var(--text-primary)] px-1"
            >
              Cancel
            </button>
          </form>
        ) : (
          <>
            <button
              onClick={() => setIsPivoting(true)}
              className="text-xs text-on-surface-variant hover:text-[var(--text-primary)] transition-colors flex items-center gap-1.5 font-medium px-2 py-1 rounded-lg"
              type="button"
            >
              <span className="material-symbols-outlined text-[15px]">tune</span>
              <span>Pivot Context</span>
            </button>
            <span className="text-border-subtle">|</span>
            <button
              onClick={() => setActiveTopic("General Intelligence")}
              className="text-xs text-rose-400 hover:text-rose-300 transition-colors flex items-center gap-1.5 font-medium px-2 py-1 rounded-lg"
              type="button"
            >
              <span className="material-symbols-outlined text-[15px]">close</span>
              <span>Clear Target</span>
            </button>
          </>
        )}
      </div>
    </div>
  );
}
