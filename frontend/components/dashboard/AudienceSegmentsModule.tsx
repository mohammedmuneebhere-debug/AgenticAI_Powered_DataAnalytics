"use client";

// FUTURE: implement real audience segmentation here once author-demographic
// extraction exists (Apify author metadata: followers, verified, bio,
// location — see ml/demographics/segmenter.py, currently dormant). Until
// then this module shows regional search interest (Google Trends) as the
// interim audience signal — real data, no invented demographics.

import React from "react";
import type { NormalizedDashboardData } from "@/lib/adapter";
import InterestByRegion from "./InterestByRegion";

interface AudienceSegmentsModuleProps {
  data: NormalizedDashboardData;
}

export default function AudienceSegmentsModule({ data }: AudienceSegmentsModuleProps) {
  const { googleTrends } = data;
  const hasTrendsData =
    googleTrends.regions.length > 0 ||
    googleTrends.relatedTopics.length > 0 ||
    googleTrends.relatedQueries.length > 0;

  return (
    <div className="lg:col-span-6 bg-surface border border-surface-border/60 rounded-2xl flex flex-col overflow-hidden shadow-sm">
      <div className="flex items-center justify-between px-4 py-3 bg-surface-high/60 border-b border-surface-border/50">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-[18px] text-tertiary">groups</span>
          <span className="font-mono text-xs uppercase text-on-surface font-bold tracking-wider">
            Estimated Audience Segments
          </span>
        </div>
        <span className="font-mono text-[10px] text-tertiary uppercase tracking-wider">
          Audience Signals
        </span>
      </div>

      <div className="p-4 flex flex-col justify-between flex-1 gap-3">
        {hasTrendsData ? (
          <InterestByRegion
            regions={googleTrends.regions}
            relatedTopics={googleTrends.relatedTopics}
            relatedQueries={googleTrends.relatedQueries}
          />
        ) : (
          <div className="flex flex-col items-center justify-center py-10 gap-2">
            <span className="material-symbols-outlined text-3xl text-outline">public_off</span>
            <p className="text-sm font-medium text-on-surface">No regional trend data</p>
            <p className="text-xs text-on-surface-variant max-w-xs text-center">
              Google Trends returned no interest data for this query. Try a broader topic or
              check the SerpAPI connection.
            </p>
          </div>
        )}

        <div className="p-2.5 bg-surface-lowest border border-surface-border/70 rounded-xl flex items-center gap-2">
          <span className="material-symbols-outlined text-outline text-[16px] shrink-0">info</span>
          <span className="font-sans text-[11px] text-on-surface-variant leading-tight">
            Interim audience signal: regional search interest (Google Trends), shown until real
            author-demographic segmentation is implemented. Values are 0-100 interest scores, not
            search volume.
          </span>
        </div>
      </div>
    </div>
  );
}
