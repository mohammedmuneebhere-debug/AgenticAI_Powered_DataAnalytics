"use client";

import { Activity } from "lucide-react";

export default function Header() {
  return (
    <header className="glass border-b border-[var(--border)] px-6 py-4">
      <div className="max-w-6xl mx-auto flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold gradient-text">SOCIALIQ</h1>
          <p className="text-sm text-[var(--text-secondary)]">
            From Social Signals to Actionable Intelligence
          </p>
        </div>
        <div className="flex items-center gap-2 text-sm text-[var(--success)]">
          <Activity size={16} />
          <span>Live</span>
        </div>
      </div>
    </header>
  );
}
