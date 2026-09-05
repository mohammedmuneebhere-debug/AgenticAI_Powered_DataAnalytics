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

export const DEFAULT_SOURCES = ["x", "telegram", "instagram", "pinterest", "google_search", "news", "sample"];

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
