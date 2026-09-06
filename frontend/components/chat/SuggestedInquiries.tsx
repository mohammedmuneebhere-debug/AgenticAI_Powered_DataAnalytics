"use client";

import React from "react";
import { useSocialIQ } from "@/context/SocialIQContext";

interface SuggestedInquiriesProps {
  onSelectQuery: (query: string) => void;
}

export default function SuggestedInquiries({ onSelectQuery }: SuggestedInquiriesProps) {
  const { activeTopic } = useSocialIQ();

  const suggestions = [
    `Map influencer network for ${activeTopic}`,
    `Analyze enterprise security friction`,
    `Compare sentiment: Developers vs Media`,
  ];

  return (
    <div className="flex flex-col gap-2.5 pt-2 pl-0 sm:pl-8">
      <span className="text-[11px] font-mono uppercase text-slate-500 font-semibold tracking-wider">
        Suggested Intelligence Inquiries:
      </span>
      <div className="flex flex-wrap items-center gap-2">
        {suggestions.map((query, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => onSelectQuery(query)}
            className="group flex items-center gap-2 px-3.5 py-1.5 bg-[#13151b] border border-border-subtle hover:border-white/40 text-on-surface hover:text-white rounded-full text-xs transition-all shadow-sm text-left"
          >
            <span className="font-mono text-slate-500 group-hover:text-white text-xs font-semibold">
              &gt;
            </span>
            <span className="group-hover:text-white transition-colors">{query}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
