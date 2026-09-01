"""Registry of available agents, connectors, and data sources."""

from backend.models.schemas import AgentTool, DataSource

AGENTS: list[AgentTool] = [
    AgentTool(id="master", name="Master Planner", description="Intent detection & workflow orchestration", category="core", default_enabled=True),
    AgentTool(id="data_acquisition", name="Data Acquisition", description="Fetch from X, Telegram, Instagram, Pinterest & Google", category="data", default_enabled=True),
    AgentTool(id="data_intelligence", name="Data Intelligence", description="Clean, dedupe, PII mask, normalize", category="data", default_enabled=True),
    AgentTool(id="social_intelligence", name="Social Intelligence", description="Sentiment, emotion, topics, trends", category="analytics", default_enabled=True),
    AgentTool(id="domain_analytics", name="Domain Analytics", description="Consumer, financial, creator insights", category="analytics", default_enabled=True),
    AgentTool(id="graph_analysis", name="Graph Analysis", description="Influence networks & propagation", category="analytics", default_enabled=True),
    AgentTool(id="visualization", name="Visualization", description="Charts, graphs & infographics", category="output", default_enabled=True),
    AgentTool(id="insight", name="Insight LLM", description="Evidence-backed recommendations", category="output", default_enabled=True),
    AgentTool(id="provenance", name="Provenance", description="Blockchain insight verification", category="security", default_enabled=True),
]

SOURCES: list[DataSource] = [
    DataSource(id="x", name="X (Twitter)", description="Posts, trends, mentions", default_enabled=True, requires_key="X_BEARER_TOKEN"),
    DataSource(id="telegram", name="Telegram", description="Channel & group messages", default_enabled=True, requires_key="TELEGRAM_BOT_TOKEN"),
    DataSource(id="instagram", name="Instagram", description="Reels, posts & captions", default_enabled=True, requires_key="INSTAGRAM_ACCESS_TOKEN"),
    DataSource(id="pinterest", name="Pinterest", description="Pins, trends & saves", default_enabled=True, requires_key="PINTEREST_ACCESS_TOKEN"),
    DataSource(id="google_search", name="Google Search", description="Web & news search results", default_enabled=True, requires_key="GOOGLE_SEARCH_API_KEY"),
    DataSource(id="reddit", name="Reddit", description="Subreddit discussions", default_enabled=False, requires_key="REDDIT_CLIENT_ID"),
    DataSource(id="news", name="News API", description="Headlines & articles", default_enabled=False, requires_key="NEWS_API_KEY"),
    DataSource(id="sample", name="Sample Data", description="Offline demo datasets", default_enabled=True),
]


def get_tools_catalog() -> dict:
    return {"agents": AGENTS, "sources": SOURCES}
