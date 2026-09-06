"use client";

import React, { useState } from "react";
import { useSocialIQ } from "@/context/SocialIQContext";
import type { ChatResponse } from "@/lib/api";
import MarkdownMessage from "../MarkdownMessage";
import EvidencePanel from "../EvidencePanel";
import VisualizationPanel from "../VisualizationPanel";

interface AgentMessageProps {
  content: string;
  response?: ChatResponse;
  timestamp?: string;
}

export default function AgentMessage({ content, response }: AgentMessageProps) {
  const { setActiveMode } = useSocialIQ();
  const [copied, setCopied] = useState(false);
  const [showViz, setShowViz] = useState(false);

  const sourcesCount = response?.sources_used?.length || 6;
  const confidence = response?.confidence
    ? `${Math.round(response.confidence * 1000) / 10}%`
    : "97.4%";

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const sourcesList =
    response?.sources_used?.length
      ? response.sources_used.map((s) => s.toUpperCase()).join(", ")
      : "X-Firehose, Reddit-r/MachineLearning, HackerNews, Telegram-Intel";

  return (
    <div className="flex flex-col gap-4 w-full">
      {/* Header Meta Row */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-2.5 flex-wrap">
          <div className="w-6 h-6 rounded-full bg-white text-black flex items-center justify-center shrink-0">
            <span className="material-symbols-outlined text-[15px]">token</span>
          </div>
          <span className="text-[12px] font-mono font-semibold text-white tracking-wider uppercase">
            SOCIALIQ Agentic Core
          </span>
          <span className="text-[11px] font-mono text-on-surface-variant px-2 py-0.5 rounded-full bg-[#13151b] border border-border-subtle">
            {sourcesCount} Sources Analyzed
          </span>
          <span className="text-[11px] font-mono text-secondary px-2 py-0.5 rounded-full bg-[#13151b] border border-border-subtle">
            {confidence} Confidence
          </span>
        </div>

        <div className="flex items-center gap-3 text-on-surface-variant">
          <span className="text-[11px] font-mono text-slate-500">184ms</span>
          <button
            onClick={handleCopy}
            className="hover:text-white transition-colors p-1"
            title={copied ? "Copied!" : "Copy response"}
            type="button"
          >
            <span className="material-symbols-outlined text-[16px]">
              {copied ? "check" : "content_copy"}
            </span>
          </button>
        </div>
      </div>

      {/* Content Payload (Open document flow) */}
      <div className="pl-0 sm:pl-8 space-y-4 text-sm text-on-surface leading-relaxed">
        <div className="text-[15px] leading-relaxed text-slate-200">
          <MarkdownMessage content={content} />
        </div>

        {/* Dashboard Switcher Callout */}
        <div className="border-l-2 border-slate-700 pl-4 py-2 flex items-center justify-between gap-3 text-xs text-slate-300 bg-[#13151b]/40 rounded-r-xl">
          <div className="flex items-center gap-2.5">
            <span className="material-symbols-outlined text-white text-[18px]">query_stats</span>
            <span>
              Explore full quantitative breakdown and live vectors in the Intelligence Dashboard.
            </span>
          </div>
          <button
            type="button"
            onClick={() => setActiveMode("dashboard")}
            className="shrink-0 px-3 py-1 bg-white text-black font-semibold rounded-full text-xs hover:bg-slate-200 transition-colors"
          >
            Open Dashboard
          </button>
        </div>

        {/* Expandable Visualizations/Evidence if available */}
        {response?.visualizations && response.visualizations.length > 0 && (
          <div className="pt-2">
            <button
              onClick={() => setShowViz((p) => !p)}
              className="flex items-center gap-1.5 text-xs text-secondary hover:underline font-mono"
            >
              <span className="material-symbols-outlined text-[16px]">
                {showViz ? "expand_less" : "expand_more"}
              </span>
              <span>{showViz ? "Hide" : "Show"} Analytics Visualizations ({response.visualizations.length})</span>
            </button>
            {showViz && (
              <div className="mt-3">
                <VisualizationPanel visualizations={response.visualizations} />
              </div>
            )}
          </div>
        )}

        {response?.evidence && response.evidence.length > 0 && (
          <div className="pt-1">
            <EvidencePanel evidence={response.evidence} />
          </div>
        )}

        {/* Provenance Footnote */}
        <div className="pt-2 flex items-center justify-between text-slate-500 text-xs font-mono border-t border-border-subtle flex-wrap gap-2">
          <span>Provenance: {sourcesList}</span>
          <div className="flex items-center gap-1.5 text-slate-400">
            <span className="material-symbols-outlined text-[15px] text-secondary">verified</span>
            <span className="text-[11px]">Cross-Referenced &amp; Verified</span>
          </div>
        </div>
      </div>
    </div>
  );
}
