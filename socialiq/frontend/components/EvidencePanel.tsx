"use client";

import type { EvidenceItem } from "@/lib/api";

interface Props {
  evidence: EvidenceItem[];
}

export default function EvidencePanel({ evidence }: Props) {
  if (!evidence.length) return null;

  return (
    <details className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)]">
      <summary className="px-4 py-2.5 text-xs font-medium text-[var(--text-secondary)] cursor-pointer hover:text-[var(--text-primary)]">
        Evidence ({evidence.length} signals)
      </summary>
      <div className="px-4 pb-3 grid grid-cols-1 sm:grid-cols-2 gap-2">
        {evidence.map((e, i) => (
          <div key={i} className="text-xs bg-[var(--bg-elevated)] rounded-lg p-2.5">
            <div className="flex justify-between items-center mb-1">
              <span className="text-[var(--accent)] capitalize">{e.type}</span>
              <span className="text-[var(--text-muted)]">{Math.round(e.confidence * 100)}%</span>
            </div>
            <p className="font-medium text-[var(--text-primary)]">{e.label}</p>
            <p className="text-[var(--text-secondary)]">{String(e.value)}</p>
          </div>
        ))}
      </div>
    </details>
  );
}
