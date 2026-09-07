import type { ChatResponse } from "./api";

export interface DashboardMetric { title: string; value: string; subValue?: string; note: string; badge?: string; badgeType?: "positive" | "warning" | "error" | "neutral"; }
export interface TrajectoryPoint { time: string; volume: number; lineValue: number; }
export interface TrendDriverItem { rank: string; title: string; source: string; growth: string; strength: "High Strength" | "Med Strength" | "Low Strength"; }
export interface NarrativeItem { title: string; subtitle: string; growth: string; color: string; }
export interface SourceContributionItem { name: string; signals: string; percentage: number; dotColor: string; }
export interface AudienceSegmentItem { label: string; percentage: number; barColor: string; }
export interface GoogleTrendsRegion { location: string; geo?: string; value: number; coordinates?: { latitude?: number; longitude?: number; lat?: number; lng?: number; }; }
export interface GoogleTrendsRelatedItem { label: string; category: "top" | "rising" | string; value: number; valueLabel?: string; type?: string; url?: string; }

export interface NormalizedDashboardData {
  topic: string; lastUpdated: string; signalsAnalyzed: string; activeSourcesCount: number; totalSourcesCount: number;
  metrics: { totalMentions: DashboardMetric; engagementVolume: DashboardMetric; sentimentScore: DashboardMetric; trendVelocity: DashboardMetric; activeSources: DashboardMetric; };
  executiveSynthesis: { title: string; confidence: number; sourcesCount: number; signalsCount: number; text: string; primaryVectors: string[]; };
  trajectory: { peakVolume: string; meanVelocity: string; spikeEvent: string; points: TrajectoryPoint[]; };
  sentimentDrivers: { netScore: string; signalsCount: string; polarity: { positive: number; neutral: number; negative: number; }; emotions: Array<{ label: string; percentage: number; icon: string; color: "secondary" | "slate" | "tertiary" | "error"; }>; };
  trendDrivers: TrendDriverItem[]; narratives: NarrativeItem[]; sourceContribution: SourceContributionItem[];
  networkIntelligence: { graphDensity: string; topCommunity: string; fastestGrowing: string; topInfluencer: string; nodes: Array<{ id: string; label: string; inf: string; border: string; text: string }>; };
  audienceSegments: AudienceSegmentItem[];
  googleTrends: { regions: GoogleTrendsRegion[]; relatedTopics: GoogleTrendsRelatedItem[]; relatedQueries: GoogleTrendsRelatedItem[]; };
  provenance: { datasetSnapshot: string; timestamp: string; pipeline: string; blockchainAnchoring: string; insightHash?: string; datasetHash?: string; };
}

const colors = ["bg-white", "bg-secondary", "bg-tertiary", "bg-slate-500", "bg-[#292e3a]"];
const sourceNames: Record<string, string> = { x: "X", telegram: "Telegram", instagram: "Instagram", pinterest: "Pinterest", google_search: "Google Search", google_trends: "Google Trends", news: "News API", reddit: "Reddit", sample: "Sample Data" };

export type DashboardRange = "1H" | "24H" | "7D" | "30D";

export function normalizeDashboardData(response: ChatResponse, topic: string, range: DashboardRange = "24H"): NormalizedDashboardData {
  const analytics = response.analytics || {};
  const sentiment = asRecord(analytics.sentiment);
  const distribution = asRecord(sentiment.distribution);
  const allRecords = numberValue(analytics.record_count);
  const score = numberValue(sentiment.average_score, 0.5);
  const counts = { positive: numberValue(distribution.positive), neutral: numberValue(distribution.neutral), negative: numberValue(distribution.negative) };
  const total = Math.max(1, counts.positive + counts.neutral + counts.negative);
  const polarity = { positive: percent(counts.positive, total), neutral: percent(counts.neutral, total), negative: percent(counts.negative, total) };
  const trends = listRecords(asRecord(analytics.trends).top_trends);
  const googleTrendsAnalytics = asRecord(analytics.google_trends);
  const googleTrends = {
    regions: listRecords(googleTrendsAnalytics.interest_by_region).map((region) => ({
      location: String(region.location || region.geo || "Unknown region"),
      geo: region.geo ? String(region.geo) : undefined,
      value: numberValue(region.value),
      coordinates: asRecord(region.coordinates) as GoogleTrendsRegion["coordinates"],
    })),
    relatedTopics: listRecords(googleTrendsAnalytics.related_topics).map(toRelatedTrend),
    relatedQueries: listRecords(googleTrendsAnalytics.related_queries).map(toRelatedTrend),
  };
  const rangeDays = { "1H": 1, "24H": 1, "7D": 7, "30D": 30 }[range];
  const cutoff = Date.now() - rangeDays * 24 * 60 * 60 * 1000;
  const temporal = listRecords(asRecord(analytics.temporal).timeline).filter((point) => {
    const timestamp = Date.parse(String(point.period || ""));
    return Number.isNaN(timestamp) || timestamp >= cutoff;
  });
  const records = temporal.length ? temporal.reduce((sum, point) => sum + numberValue(point.signal_count), 0) : 0;
  const scopedFactor = allRecords ? records / allRecords : 0;
  const scopedScore = temporal.length
    ? temporal.reduce((sum, point) => sum + numberValue(point.sentiment_score, score) * numberValue(point.signal_count), 0) / Math.max(1, records)
    : 0.5;
  const scopedCounts = temporal.reduce((result, point) => {
    const distribution = asRecord(point.distribution);
    result.positive += numberValue(distribution.positive);
    result.neutral += numberValue(distribution.neutral);
    result.negative += numberValue(distribution.negative);
    return result;
  }, { positive: 0, neutral: 0, negative: 0 });
  const scopedTotal = Math.max(1, scopedCounts.positive + scopedCounts.neutral + scopedCounts.negative);
  const scopedPolarity = { positive: percent(scopedCounts.positive, scopedTotal), neutral: percent(scopedCounts.neutral, scopedTotal), negative: percent(scopedCounts.negative, scopedTotal) };
  const sources = response.sources_used?.length ? response.sources_used : ["sample"];
  const topVelocity = trends.length ? numberValue(trends[0].velocity) : 0;
  const trendDrivers = trends.map((trend, index) => ({ rank: String(index + 1).padStart(2, "0"), title: String(trend.topic || "Signal"), source: `${range} signal stream`, growth: `${(numberValue(trend.velocity) * scopedFactor).toFixed(2)} velocity`, strength: index === 0 ? "High Strength" : index < 3 ? "Med Strength" : "Low Strength" } as TrendDriverItem));
  const points = temporal.map((point, index) => ({ time: String(point.period || `Signal ${index + 1}`), volume: Math.max(0, numberValue(point.signal_count, records / Math.max(1, temporal.length))), lineValue: Math.round(numberValue(point.sentiment_score, score) * 100) }));
  const emotionDistribution = asRecord(analytics.emotion).distribution;
  const emotions = Object.entries(asRecord(emotionDistribution)).filter(([, value]) => numberValue(value) > 0).map(([label, value], index) => ({ label: label.replace(/\b\w/g, (char) => char.toUpperCase()), percentage: percent(numberValue(value), Math.max(1, records)), icon: index === 0 ? "mood" : "psychology", color: (index % 3 === 0 ? "secondary" : index % 3 === 1 ? "slate" : "tertiary") as "secondary" | "slate" | "tertiary" }));
  const segments = listRecords(asRecord(analytics.demographics).segments).map((segment, index) => ({ label: String(segment.label || "Audience"), percentage: numberValue(segment.percentage), barColor: colors[index % colors.length] }));
  const network = asRecord(analytics.network);
  const nodes = listRecords(network.nodes).map((node, index) => ({ id: String(node.id || index), label: String(node.label || node.id || "Node"), inf: `${numberValue(node.size)} impact`, border: colors[index % colors.length].replace("bg-", "border-"), text: "text-white" }));
  const sourceContribution = sources.map((source, index) => ({ name: sourceNames[source] || source, signals: `${Math.round(records / sources.length)} signals`, percentage: Math.round(100 / sources.length), dotColor: colors[index % colors.length] }));
  const primaryVectors = trends.slice(0, 5).map((trend) => `#${String(trend.topic || "signal").replace(/\s+/g, "-").toLowerCase()}`);
  const prov = response.provenance;
  const avgVelocity = trends.length ? trends.reduce((sum, trend) => sum + numberValue(trend.velocity), 0) / trends.length : 0;

  return {
    topic, lastUpdated: `Updated ${new Date().toLocaleTimeString()}`, signalsAnalyzed: `${records.toLocaleString()} signals analyzed`, activeSourcesCount: sources.length, totalSourcesCount: sources.length,
    metrics: {
      totalMentions: metric("Total Mentions", records.toLocaleString(), "Live records", "Current query context"),
      engagementVolume: metric("Engagement Volume", records.toLocaleString(), "Observed", "Returned signal set"),
      sentimentScore: metric("Sentiment Score", `${scopedScore >= 0.5 ? "+" : ""}${Math.round((scopedScore - 0.5) * 200)}`, sentimentLabel(scopedScore), `Computed from ${range} records`),
      trendVelocity: metric("Trend Velocity", topVelocity.toFixed(2), "Velocity", "Top generated trend", topVelocity > 1 ? "High Accel" : "Emerging", "warning"),
      activeSources: metric("Active Sources", `${sources.length}/${sources.length}`, "Connected", "Sources returned"),
    },
    executiveSynthesis: { title: "SOCIALIQ Intelligence Executive Synthesis", confidence: Math.round(response.confidence * 100), sourcesCount: sources.length, signalsCount: records, text: cleanText(response.message), primaryVectors },
    trajectory: { peakVolume: `${Math.max(...points.map((point) => point.volume), 0).toLocaleString()} / period`, meanVelocity: `${avgVelocity.toFixed(2)} avg`, spikeEvent: points.length ? `Latest period: ${points[points.length - 1].time}` : "No temporal spike detected", points },
    sentimentDrivers: { netScore: `${Math.round((scopedScore - 0.5) * 200)} NET`, signalsCount: `${records.toLocaleString()} Signals`, polarity: scopedPolarity, emotions },
    trendDrivers, narratives: trends.map((trend, index) => ({ title: String(trend.topic || "Signal"), subtitle: `${numberValue(trend.mentions)} mentions in returned context`, growth: `${Math.round(numberValue(trend.confidence) * 100)}% confidence`, color: colors[index % colors.length] })),
    sourceContribution, networkIntelligence: { graphDensity: nodes.length ? `${nodes.length} nodes` : "No graph data", topCommunity: String(network.community_count || "No community data"), fastestGrowing: trendDrivers[0]?.title || "No trend data", topInfluencer: nodes[0]?.label || "No influencer data", nodes },
    audienceSegments: segments, googleTrends, provenance: { datasetSnapshot: prov?.dataset_hash ? `#DS-${prov.dataset_hash.slice(0, 12)}` : "Dataset hash unavailable", timestamp: prov?.timestamp || new Date().toISOString(), pipeline: prov?.model_version || "Generated analytics", blockchainAnchoring: prov?.blockchain_tx_id ? `Confirmed Tx #${prov.blockchain_tx_id.slice(0, 8)}` : "Local provenance", insightHash: prov?.insight_hash, datasetHash: prov?.dataset_hash },
  };
}

function metric(title: string, value: string, subValue: string, note: string, badge?: string, badgeType: DashboardMetric["badgeType"] = "neutral"): DashboardMetric { return { title, value, subValue, note, badge, badgeType }; }
function asRecord(value: unknown): Record<string, any> { return value && typeof value === "object" && !Array.isArray(value) ? value as Record<string, any> : {}; }
function listRecords(value: unknown): Record<string, any>[] { return Array.isArray(value) ? value.filter((item): item is Record<string, any> => !!item && typeof item === "object") : []; }
function numberValue(value: unknown, fallback = 0): number { const parsed = Number(value); return Number.isFinite(parsed) ? parsed : fallback; }
function percent(value: number, total: number): number { return Math.round((value / total) * 100); }
function sentimentLabel(score: number): string { return score > 0.55 ? "Positive" : score < 0.45 ? "Negative" : "Neutral"; }
function cleanText(value: string): string { return value.replace(/^#+\s+/gm, "").replace(/\*\*/g, "").trim(); }
function toRelatedTrend(item: Record<string, any>): GoogleTrendsRelatedItem {
  return {
    label: String(item.label || "Related signal"),
    category: String(item.category || "top"),
    value: numberValue(item.value),
    valueLabel: item.value_label ? String(item.value_label) : undefined,
    type: item.type ? String(item.type) : undefined,
    url: item.url ? String(item.url) : undefined,
  };
}
