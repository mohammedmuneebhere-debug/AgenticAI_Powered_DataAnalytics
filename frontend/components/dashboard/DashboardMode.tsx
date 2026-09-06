"use client";

import React, { useState } from "react";
import { useSocialIQ } from "@/context/SocialIQContext";
import { normalizeDashboardData } from "@/lib/adapter";
import DashboardSearch from "./DashboardSearch";
import TrendingVectorsStrip from "./TrendingVectorsStrip";
import DossierHeader from "./DossierHeader";
import MetricCards from "./MetricCards";
import ExecutiveSynthesis from "./ExecutiveSynthesis";
import TrajectoryModule from "./TrajectoryModule";
import SentimentDriversModule from "./SentimentDriversModule";
import KeyTrendDriversModule from "./KeyTrendDriversModule";
import EmergingNarrativesModule from "./EmergingNarrativesModule";
import SourceContributionModule from "./SourceContributionModule";
import NetworkIntelligenceModule from "./NetworkIntelligenceModule";
import AudienceSegmentsModule from "./AudienceSegmentsModule";
import ProvenanceModule from "./ProvenanceModule";
import DashboardFooter from "./DashboardFooter";

export default function DashboardMode() {
  const { activeTopic, setActiveTopic, analysisCache, runTopicAnalysis, isAnalyzing } =
    useSocialIQ();
  const [loadingTopic, setLoadingTopic] = useState<string | undefined>();

  // Fetch or retrieve normalized data for activeTopic
  const cachedResponse = analysisCache[activeTopic];
  const normalizedData = cachedResponse ? normalizeDashboardData(cachedResponse, activeTopic) : null;

  const handleAnalyze = async (query: string) => {
    setLoadingTopic(query);
    await runTopicAnalysis(query, true);
    setLoadingTopic(undefined);
  };

  const handleSelectTrendingTopic = async (topic: string) => {
    setActiveTopic(topic);
    // On-demand lazy load if not already in cache
    if (!analysisCache[topic]) {
      setLoadingTopic(topic);
      await runTopicAnalysis(topic, false);
      setLoadingTopic(undefined);
    }
  };

  return (
    <div className="flex flex-col w-full gap-5">
      {/* Top Discovery & Search Bar */}
      <DashboardSearch onAnalyze={handleAnalyze} loading={isAnalyzing} />

      {!normalizedData ? (
        <div className="rounded-2xl border border-border-subtle bg-[#13151b] p-10 text-center">
          <span className="material-symbols-outlined text-4xl text-slate-500">query_stats</span>
          <h2 className="mt-3 text-lg font-semibold text-white">No intelligence dossier yet</h2>
          <p className="mx-auto mt-2 max-w-lg text-sm text-on-surface-variant">
            Send a query from Chat Mode or use the search above to generate dashboard insights.
          </p>
        </div>
      ) : (
        <>
        {/* Lightweight 'Trending Now' Strip */}
        <TrendingVectorsStrip onSelectTopic={handleSelectTrendingTopic} loadingTopic={loadingTopic} />
        <DossierHeader data={normalizedData} />
        <MetricCards data={normalizedData} />
        <ExecutiveSynthesis data={normalizedData} />
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Module A: Conversation Volume & Trajectory (8 cols) */}
        <TrajectoryModule data={normalizedData} />

        {/* Module B: Sentiment Drivers (4 cols) */}
        <SentimentDriversModule data={normalizedData} />

        {/* Module C: Key Trend Drivers (7 cols) */}
        <KeyTrendDriversModule data={normalizedData} />

        {/* Module D: Emerging Narratives (5 cols) */}
        <EmergingNarrativesModule data={normalizedData} />

        {/* Module E: Source Contribution Ingestion (6 cols) */}
        <SourceContributionModule data={normalizedData} />

        {/* Module F: Network Intelligence & Key Clusters (6 cols) */}
        <NetworkIntelligenceModule data={normalizedData} />

        {/* Module G: Estimated Audience Segments (6 cols) */}
        <AudienceSegmentsModule data={normalizedData} />

        {/* Module I: Insight Verification & Data Provenance (6 cols) */}
        <ProvenanceModule data={normalizedData} />
        </div>

        <DashboardFooter />
        </>
      )}
    </div>
  );
}
