export const DOMAIN_COLORS: Record<string, string> = {
  consumer: "var(--domain-consumer)",
  financial: "var(--domain-financial)",
  creator: "var(--domain-creator)",
  general: "var(--domain-general)",
};

export const DOMAIN_ICONS: Record<string, string> = {
  consumer: "☕",
  financial: "📈",
  creator: "📱",
  general: "🔍",
};

export const DEFAULT_AGENTS = [
  "master", "data_acquisition", "data_intelligence", "social_intelligence",
  "domain_analytics", "graph_analysis", "visualization", "insight", "provenance",
];

export const DEFAULT_SOURCES = ["x", "telegram", "instagram", "pinterest", "google_search", "sample"];

export const DEMO_SESSION_ID = "local-demo-showcase";
export const DEMO_SESSION_TITLE = "Demo Showcase (read-only)";
export const DEMO_MESSAGES = [
  {
    role: "user" as const,
    content: "Why is AI Agents trending today, and what are the primary friction points being discussed?",
    timestamp: "10:41:22 UTC",
  },
  {
    role: "assistant" as const,
    content:
      "AI Agents are experiencing significant surge in discussion velocity (+312% over 24h) across technology and developer hubs. The primary catalysts are three concurrent autonomous agent framework releases and enterprise workflow announcements.\n\n### Key observations from ingested signal stream\n\n1. **Developer Adoption:** Significant enthusiasm around autonomous code refactoring and multi-agent coordination frameworks, particularly across GitHub discussions and Reddit tech forums.\n2. **Enterprise Friction:** Increasing debate concerning hallucination risks in autonomous execution loops, API token cost escalation, and security boundaries for tool execution.\n3. **Employment Narratives:** Emerging tension regarding junior engineering role displacement, counterbalanced by discussions on 'AI agent orchestration' as a new high-demand specialization.\n\nWould you like me to inspect the top influence clusters driving this conversation, or isolate the sentiment shift across developer communities vs. general news?",
    timestamp: "10:41:23 UTC",
  },
  {
    role: "user" as const,
    content: "Which developer communities are leading the push, and how does sentiment compare to general news?",
    timestamp: "10:43:08 UTC",
  },
  {
    role: "assistant" as const,
    content:
      "Developer communities (predominantly specialized subreddits and developer Discord/X clusters) represent **58%** of all technical discussions. Sentiment in technical channels remains **68% positive**—anchored in practical tooling improvements.\n\nIn contrast, mainstream news sources reflect a more cautious **42% neutral** / **34% negative** stance, focusing heavily on workplace disruption and governance risks.",
    timestamp: "10:43:10 UTC",
  },
];

export const FALLBACK_AGENTS = DEFAULT_AGENTS.map((id) => ({
  id,
  name: id.replace(/_/g, " "),
  description: "Available SOCIALIQ analysis agent",
  category: "core",
  default_enabled: true,
}));

/** Fallback catalog — used if API is stale/unreachable; must match backend tools_registry.py */
export const FALLBACK_SOURCES = [
  { id: "x", name: "X (Twitter)", description: "Posts, trends, mentions", default_enabled: true, requires_key: "X_BEARER_TOKEN" },
  { id: "telegram", name: "Telegram", description: "Channel & group messages", default_enabled: true, requires_key: "TELEGRAM_BOT_TOKEN" },
  { id: "instagram", name: "Instagram", description: "Reels, posts & captions", default_enabled: true, requires_key: "INSTAGRAM_ACCESS_TOKEN" },
  { id: "pinterest", name: "Pinterest", description: "Pins, trends & saves", default_enabled: true, requires_key: "PINTEREST_ACCESS_TOKEN" },
  { id: "google_search", name: "Google Search", description: "Web & news search results", default_enabled: true, requires_key: "GOOGLE_SEARCH_API_KEY" },
  { id: "reddit", name: "Reddit", description: "Subreddit discussions", default_enabled: false, requires_key: "REDDIT_CLIENT_ID" },
  { id: "news", name: "News API", description: "Headlines & articles", default_enabled: false, requires_key: "NEWS_API_KEY" },
  { id: "sample", name: "Sample Data", description: "Offline demo datasets", default_enabled: true },
];

export const SOURCE_ICONS: Record<string, string> = {
  x: "𝕏",
  telegram: "✈️",
  instagram: "📸",
  pinterest: "📌",
  google_search: "🔍",
  reddit: "🔴",
  news: "📰",
  sample: "💾",
};

export const DEMO_QUERIES = [
  { label: "Coffee product launch", domain: "consumer", query: "Analyze coffee trends and tell me what product I should launch this winter." },
  { label: "BTC volatility", domain: "financial", query: "Why is BTC volatile today and what scenarios should I prepare for?" },
  { label: "Creator strategy", domain: "creator", query: "Find trending Instagram content and create a strategy for the next 7 days." },
];
