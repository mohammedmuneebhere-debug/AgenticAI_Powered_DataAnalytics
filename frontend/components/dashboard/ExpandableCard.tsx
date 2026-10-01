"use client";

import React, { useCallback, useEffect } from "react";

interface ExpandableCardProps {
  /** Card title, used for the modal header and aria labels. */
  title: string;
  children: React.ReactNode;
  /**
   * Optional richer body for the enlarged view (defaults to the same children
   * rendered at full width).
   */
  expandedBody?: React.ReactNode;
  /** Layout classes for the card wrapper (e.g. grid column spans). */
  className?: string;
}

/**
 * Wraps a dashboard module so that hovering reveals a small expand icon in
 * the card's top-left corner; clicking opens the same card enlarged in a
 * modal overlay (Escape or backdrop click closes).
 */
export default function ExpandableCard({ title, children, expandedBody, className }: ExpandableCardProps) {
  const [expanded, setExpanded] = React.useState(false);

  const close = useCallback(() => setExpanded(false), []);

  useEffect(() => {
    if (!expanded) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") close();
    };
    document.addEventListener("keydown", onKey);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = previousOverflow;
    };
  }, [expanded, close]);

  return (
    <>
      <div className={`relative group h-full ${className ?? ""}`}>
        <button
          type="button"
          onClick={() => setExpanded(true)}
          aria-label={`Expand ${title}`}
          title={`Expand ${title}`}
          className="absolute top-1.5 left-1.5 z-10 opacity-0 group-hover:opacity-100 transition-opacity duration-150
                     flex items-center justify-center w-6 h-6 rounded-lg
                     bg-surface-high/95 border border-surface-border/70 text-on-surface-variant
                     hover:text-secondary hover:border-secondary/50 shadow-sm"
        >
          <span className="material-symbols-outlined text-[14px]">open_in_full</span>
        </button>
        {children}
      </div>

      {expanded && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 md:p-8"
          role="dialog"
          aria-modal="true"
          aria-label={`${title} (enlarged view)`}
        >
          <button
            type="button"
            aria-label="Close enlarged view"
            onClick={close}
            className="absolute inset-0 bg-black/70 backdrop-blur-sm cursor-default"
          />
          <div className="relative z-10 w-full max-w-5xl max-h-[90vh] overflow-auto bg-surface border border-surface-border rounded-2xl shadow-2xl">
            <div className="sticky top-0 z-10 flex items-center justify-between px-5 py-3 bg-surface-high/90 backdrop-blur border-b border-surface-border/60">
              <span className="font-mono text-xs uppercase text-on-surface font-bold tracking-wider">
                {title}
              </span>
              <button
                type="button"
                onClick={close}
                className="flex items-center gap-1 font-mono text-[11px] uppercase tracking-wider text-on-surface-variant hover:text-secondary transition-colors"
              >
                Close
                <span className="material-symbols-outlined text-[16px]">close</span>
              </button>
            </div>
            <div className="p-5">{expandedBody ?? children}</div>
          </div>
        </div>
      )}
    </>
  );
}
