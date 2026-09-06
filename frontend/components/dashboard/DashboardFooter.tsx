"use client";

import React from "react";

export default function DashboardFooter() {
  return (
    <div className="flex flex-wrap items-center justify-between p-3.5 bg-surface border border-surface-border/60 rounded-2xl font-mono text-[11px] text-slate-400 gap-2 shadow-sm">
      <div className="flex items-center gap-3 flex-wrap">
        <span className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-secondary" />
          <span>
            STREAM STATUS: <strong className="text-slate-200">SYNCHRONIZED</strong>
          </span>
        </span>
        <span className="text-surface-border hidden sm:inline">|</span>
        <span>
          INDEX REFRESH: <strong className="text-slate-200">120s</strong>
        </span>
        <span className="text-surface-border hidden sm:inline">|</span>
        <span>
          ENCRYPTION: <strong className="text-slate-200">TLS 1.3 / AES-256-GCM</strong>
        </span>
      </div>

      <div>
        <span>SOCIALIQ REALTIME TOPIC INTELLIGENCE ENGINE v4.2</span>
      </div>
    </div>
  );
}
