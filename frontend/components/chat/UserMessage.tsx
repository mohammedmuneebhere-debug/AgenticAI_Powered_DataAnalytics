"use client";

import React from "react";

interface UserMessageProps {
  content: string;
  timestamp?: string;
}

export default function UserMessage({ content, timestamp }: UserMessageProps) {
  return (
    <div className="w-full bg-[#13151b] border border-border-subtle rounded-2xl px-5 py-4 flex flex-col gap-2 shadow-sm">
      <div className="flex items-center justify-between text-xs text-on-surface-variant">
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-mono uppercase tracking-wider text-slate-400 font-medium">
            User Query
          </span>
        </div>
        <span className="font-mono text-[11px] text-slate-500">
          {timestamp || new Date().toISOString().slice(11, 19) + " UTC"}
        </span>
      </div>
      <div className="text-[15px] text-white leading-relaxed font-medium">
        {content}
      </div>
    </div>
  );
}
