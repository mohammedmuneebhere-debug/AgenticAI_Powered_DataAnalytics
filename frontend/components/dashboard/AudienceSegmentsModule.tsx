"use client";

// Real audience segmentation (Phase 2): when author metadata flowed through
// the pipeline, analytics.demographics carries follower-tier segments derived
// from actual author profiles (Apify author fields + NER over bios). Without
// metadata the module keeps the interim Google Trends regional-interest view.

import React from "react";
import type { NormalizedDashboardData } from "@/lib/adapter";
import InterestByRegion from "./InterestByRegion";

interface AudienceSegmentsModuleProps {
  data: NormalizedDashboardData;
}

export default function AudienceSegmentsModule({ data }: AudienceSegmentsModuleProps) {
  const { googleTrends, audienceSegments, audienceMeta } = data;
  const hasRealSegments = audienceSegments.length > 0;
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
            {hasRealSegments ? "Audience Segments" : "Estimated Audience Segments"}
          </span>
        </div>
        <span className="font-mono text-[10px] text-tertiary uppercase tracking-wider">
          {hasRealSegments ? `From ${audienceMeta.authorsWithMetadata} authors` : "Audience Signals"}
        </span>
      </div>

      <div className="p-4 flex flex-col justify-between flex-1 gap-3">
        {hasRealSegments ? (
          <>
            <div className="flex flex-col gap-2.5">
              {audienceSegments.map((segment) => (
                <div key={segment.label} className="flex flex-col gap-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-on-surface font-medium">{segment.label}</span>
                    <span className="font-mono text-on-surface-variant">{segment.percentage.toFixed(1)}%</span>
                  </div>
                  <div className="h-1.5 rounded-full bg-surface-lowest overflow-hidden">
                    <div
                      className={`h-full rounded-full ${segment.barColor}`}
                      style={{ width: `${Math.min(100, segment.percentage)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>

            {(audienceMeta.topLocations.length > 0 || audienceMeta.verifiedSharePct > 0) && (
              <div className="flex flex-wrap gap-1.5">
                {audienceMeta.verifiedSharePct > 0 && (
                  <span className="px-2 py-0.5 rounded-full bg-surface-high border border-surface-border/60 text-[10px] font-mono text-on-surface-variant">
                    {audienceMeta.verifiedSharePct.toFixed(0)}% verified
                  </span>
                )}
                {audienceMeta.topLocations.slice(0, 3).map((loc) => (
                  <span
                    key={loc.location}
                    className="px-2 py-0.5 rounded-full bg-surface-high border border-surface-border/60 text-[10px] font-mono text-on-surface-variant"
                  >
                    {loc.location} · {loc.authors}
                  </span>
                ))}
              </div>
            )}

            <div className="p-2.5 bg-surface-lowest border border-surface-border/70 rounded-xl flex items-center gap-2">
              <span className="material-symbols-outlined text-outline text-[16px] shrink-0">info</span>
              <span className="font-sans text-[11px] text-on-surface-variant leading-tight">
                {audienceMeta.disclaimer ||
                  "Segments are probabilistic aggregates from public profile signals, not verified individual attributes."}
              </span>
            </div>
          </>
        ) : hasTrendsData ? (
          <>
            <InterestByRegion
              regions={googleTrends.regions}
              relatedTopics={googleTrends.relatedTopics}
              relatedQueries={googleTrends.relatedQueries}
            />
            <div className="p-2.5 bg-surface-lowest border border-surface-border/70 rounded-xl flex items-center gap-2">
              <span className="material-symbols-outlined text-outline text-[16px] shrink-0">info</span>
              <span className="font-sans text-[11px] text-on-surface-variant leading-tight">
                Interim audience signal: regional search interest (Google Trends), shown until real
                author metadata is available for this query. Values are 0-100 interest scores, not
                search volume.
              </span>
            </div>
          </>
        ) : (
          <div className="flex flex-col items-center justify-center py-10 gap-2">
            <span className="material-symbols-outlined text-3xl text-outline">public_off</span>
            <p className="text-sm font-medium text-on-surface">No audience data</p>
            <p className="text-xs text-on-surface-variant max-w-xs text-center">
              No author metadata or regional trend data was returned for this query. Try a broader
              topic or check the source connections.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
