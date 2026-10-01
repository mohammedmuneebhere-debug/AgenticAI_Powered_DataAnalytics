"use client";

import React, { useState } from "react";
import { useSocialIQ } from "@/context/SocialIQContext";
import { normalizeDashboardData, type DashboardRange } from "@/lib/adapter";
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
import NetworkIntelligenceModule, { NetworkIntelligenceExpanded } from "./NetworkIntelligenceModule";
import AudienceSegmentsModule from "./AudienceSegmentsModule";
import ProvenanceModule from "./ProvenanceModule";
import RelevantPostsModule from "./RelevantPostsModule";
import DashboardFooter from "./DashboardFooter";
import ExpandableCard from "./ExpandableCard";

export default function DashboardMode() {
  const { activeTopic, setActiveTopic, analysisCache, runTopicAnalysis, isAnalyzing, chatMessages } =
    useSocialIQ();
  const [loadingTopic, setLoadingTopic] = useState<string | undefined>();
  const [activeRange, setActiveRange] = useState<DashboardRange>("24H");

  // Fetch or retrieve normalized data for activeTopic
  const latestResponse = [...chatMessages].reverse().find((message) => message.response)?.response;
  const cachedResponse = analysisCache[activeTopic] || latestResponse;
  const normalizedData = cachedResponse ? normalizeDashboardData(cachedResponse, activeTopic, activeRange) : null;

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
        <div className="rounded-2xl border border-border-subtle bg-[var(--bg-surface)] p-10 text-center">
          <span className="material-symbols-outlined text-4xl text-outline">query_stats</span>
          <h2 className="mt-3 text-lg font-semibold text-[var(--text-primary)]">No intelligence dossier yet</h2>
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
        {/* Every module is wrapped in ExpandableCard: hovering a card shows a
            small expand icon top-left; clicking opens it enlarged in a modal.
            The wrapper carries the grid col-span. */}

        {/* Module A: Conversation Volume & Trajectory (8 cols) */}
        <ExpandableCard title="Conversation Trajectory" className="lg:col-span-8">
          <TrajectoryModule data={normalizedData} activeRange={activeRange} onRangeChange={setActiveRange} />
        </ExpandableCard>

        {/* Module B: Sentiment Drivers (4 cols) */}
        <ExpandableCard title="Sentiment Drivers" className="lg:col-span-4">
          <SentimentDriversModule data={normalizedData} />
        </ExpandableCard>

        {/* Module C: Key Trend Drivers (7 cols) */}
        <ExpandableCard title="Key Trend Drivers" className="lg:col-span-7">
          <KeyTrendDriversModule data={normalizedData} />
        </ExpandableCard>

        {/* Module D: Emerging Narratives (5 cols) */}
        <ExpandableCard title="Emerging Narratives" className="lg:col-span-5">
          <EmergingNarrativesModule data={normalizedData} />
        </ExpandableCard>

        {/* Module E: Source Contribution Ingestion (6 cols) */}
        <ExpandableCard title="Source Contribution Ingestion" className="lg:col-span-6">
          <SourceContributionModule data={normalizedData} />
        </ExpandableCard>

        {/* Module F: Network Intelligence & Key Clusters (6 cols) — enlarges to the full clustering graph */}
        <ExpandableCard
          title="Network Intelligence"
          className="lg:col-span-6"
          expandedBody={<NetworkIntelligenceExpanded data={normalizedData} />}
        >
          <NetworkIntelligenceModule data={normalizedData} />
        </ExpandableCard>

        {/* Module G: Estimated Audience Segments (interim: real Google Trends regional interest; real author-demographic segmentation comes later) (6 cols) */}
        <ExpandableCard title="Audience Segments" className="lg:col-span-6">
          <AudienceSegmentsModule data={normalizedData} />
        </ExpandableCard>

        {/* Module H: Most Relevant Posts (6 cols) — fixed-height scrollable card */}
        <ExpandableCard title="Most Relevant Posts" className="lg:col-span-6 self-start">
          <RelevantPostsModule data={normalizedData} />
        </ExpandableCard>

        {/* Module I: Insight Verification & Data Provenance (6 cols) */}
        <ExpandableCard title="Insight Verification & Provenance" className="lg:col-span-6">
          <ProvenanceModule data={normalizedData} />
        </ExpandableCard>
        </div>

        <DashboardFooter />
        </>
      )}
    </div>
  );
}
