"use client";

import React from "react";
import type { NormalizedDashboardData } from "@/lib/adapter";

interface RelevantPostsModuleProps {
  data: NormalizedDashboardData;
}

/**
 * Most relevant X posts for the active query, ranked by engagement and
 * query-term overlap (from response.top_posts).
 */
export default function RelevantPostsModule({ data }: RelevantPostsModuleProps) {
  const { relevantPosts } = data;

  return (
    <div className="lg:col-span-6 bg-surface border border-surface-border/60 rounded-2xl flex flex-col overflow-hidden shadow-sm">
      <div className="flex items-center justify-between px-4 py-3 bg-surface-high/60 border-b border-surface-border/50">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-[18px] text-secondary">forum</span>
          <span className="font-mono text-xs uppercase text-on-surface font-bold tracking-wider">
            Most Relevant Posts
          </span>
        </div>
        <span className="font-mono text-[10px] text-tertiary uppercase tracking-wider">
          X / Twitter
        </span>
      </div>

      <div className="p-4 flex flex-col gap-3 flex-1">
        {relevantPosts.length ? (
          relevantPosts.map((post) => (
            <div
              key={`${post.rank}-${post.author}`}
              className="rounded-xl border border-surface-border/70 bg-surface-lowest p-3 flex flex-col gap-1.5"
            >
              <div className="flex items-center justify-between gap-2">
                <span className="font-mono text-[11px] font-bold text-on-surface truncate">
                  @{post.author.replace(/^@/, "")}
                </span>
                <span className="flex items-center gap-1 font-mono text-[10px] text-on-surface-variant shrink-0">
                  <span className="material-symbols-outlined text-[13px] text-secondary">favorite</span>
                  {post.engagementTotal.toLocaleString()}
                </span>
              </div>
              <p className="font-sans text-xs text-on-surface-variant leading-relaxed line-clamp-3">
                {post.text}
              </p>
              {post.url && (
                <a
                  href={post.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-mono text-[10px] text-secondary hover:underline flex items-center gap-1 w-fit"
                >
                  View on X
                  <span className="material-symbols-outlined text-[12px]">open_in_new</span>
                </a>
              )}
            </div>
          ))
        ) : (
          <div className="flex flex-col items-center justify-center py-10 gap-2">
            <span className="material-symbols-outlined text-3xl text-outline">speaker_notes_off</span>
            <p className="text-sm font-medium text-on-surface">No relevant posts found</p>
            <p className="text-xs text-on-surface-variant max-w-xs text-center">
              No X posts were returned for this query. Enable the X Scraper (Apify) connector
              and re-run the analysis.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
