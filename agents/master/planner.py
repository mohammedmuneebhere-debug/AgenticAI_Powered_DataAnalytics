"""Master AI Agent — intent detection, workflow planning, and orchestration."""

from dataclasses import dataclass, field
from typing import Any, Optional
import re

from agents.data_acquisition.agent import DataAcquisitionAgent
from agents.data_intelligence.agent import DataIntelligenceAgent
from agents.social_intelligence.agent import SocialIntelligenceAgent
from agents.domain.agent import DomainAnalyticsAgent
from agents.visualization.agent import VisualizationAgent
from agents.insight.agent import InsightAgent
from ml.correlation import EvidenceCorrelationEngine


DOMAIN_LABELS = {
    "consumer": "Consumer Intelligence",
    "financial": "Market Intelligence",
    "creator": "Creator Intelligence",
    "general": "General Social Intelligence",
}

INTENT_PATTERNS = {
    "strategy": [r"strategy", r"launch", r"product", r"content plan", r"calendar", r"should i", r"recommend"],
    "market": [r"btc", r"bitcoin", r"volatile", r"volatility", r"crypto", r"stock", r"trading", r"price"],
    "influence": [r"who is driving", r"influencer", r"spreading", r"network", r"propagation"],
    "demographics": [r"young", r"audience", r"demographic", r"consumer", r"who is"],
    "sentiment": [r"sentiment", r"feel", r"opinion", r"mood", r"reaction"],
    "trend": [r"trend", r"trending", r"popular", r"viral", r"what's hot"],
}

# (pattern, weight) — score domains independently per query
DOMAIN_SIGNALS: dict[str, list[tuple[str, int]]] = {
    "financial": [
        (r"\b(btc|bitcoin|ethereum|crypto|eth)\b", 5),
        (r"\b(volatil(e|ity)|market|trading|stock|etf)\b", 3),
        (r"\bprice\b", 2),
        (r"\b(scenario|bull|bear|correction)\b", 2),
    ],
    "consumer": [
        (r"\bcoffee\b", 5),
        (r"\b(product|launch|brand|retail|winter|season)\b", 3),
        (r"\b(consumer|demand|purchase|buy)\b", 2),
    ],
    "creator": [
        (r"\binstagram\b", 5),
        (r"\b(content|reel|carousel|posting|creator|influencer)\b", 3),
        (r"\b(tiktok|youtube|followers|engagement)\b", 2),
    ],
}

ENTITY_PATTERNS = {
    "coffee": r"\bcoffee\b",
    "btc": r"\b(btc|bitcoin)\b",
    "instagram": r"\binstagram\b",
    "crypto": r"\b(crypto|ethereum|eth)\b",
}


@dataclass
class QueryPlan:
    intent: str
    entities: list[str] = field(default_factory=list)
    domain: str = "general"
    domain_label: str = "General Social Intelligence"
    time_range: str = "recent"
    platforms: list[str] = field(default_factory=lambda: ["x", "telegram", "instagram", "pinterest", "google_search", "news"])
    workflow: list[str] = field(default_factory=list)
    required_capabilities: list[str] = field(default_factory=list)
    agents_used: list[str] = field(default_factory=list)
    sources_used: list[str] = field(default_factory=list)


class MasterAgent:
    """Entry point: parses intent, selects agents, runs the pipeline."""

    ALL_AGENTS = [
        "master", "data_acquisition", "data_intelligence", "social_intelligence",
        "domain_analytics", "graph_analysis", "visualization", "insight", "provenance",
    ]

    def __init__(self):
        self.data_agent = DataAcquisitionAgent()
        self.intelligence_agent = DataIntelligenceAgent()
        self.social_agent = SocialIntelligenceAgent()
        self.domain_agent = DomainAnalyticsAgent()
        self.viz_agent = VisualizationAgent()
        self.insight_agent = InsightAgent()
        self.correlation_engine = EvidenceCorrelationEngine()

    def parse_query(self, query: str) -> QueryPlan:
        q = query.lower()

        priority_order = ["strategy", "market", "influence", "demographics", "sentiment", "trend"]
        intent = "general"
        for name in priority_order:
            patterns = INTENT_PATTERNS.get(name, [])
            if any(re.search(p, q) for p in patterns):
                intent = name
                break

        domain = self._detect_domain(q)
        entities = self._extract_entities(q, domain)
        workflow = self._select_workflow(intent, domain)

        return QueryPlan(
            intent=intent,
            entities=entities,
            domain=domain,
            domain_label=DOMAIN_LABELS.get(domain, DOMAIN_LABELS["general"]),
            workflow=workflow,
            required_capabilities=workflow,
        )

    def _detect_domain(self, q: str) -> str:
        scores: dict[str, int] = {d: 0 for d in DOMAIN_SIGNALS}
        for domain, signals in DOMAIN_SIGNALS.items():
            for pattern, weight in signals:
                if re.search(pattern, q):
                    scores[domain] += weight

        best = max(scores, key=scores.get)
        if scores[best] == 0:
            return "general"
        # Require minimum score to avoid false positives
        if scores[best] < 2:
            return "general"
        return best

    def _extract_entities(self, q: str, domain: str) -> list[str]:
        found = [name for name, pat in ENTITY_PATTERNS.items() if re.search(pat, q)]
        if found:
            return found
        domain_defaults = {"consumer": ["coffee"], "financial": ["btc"], "creator": ["instagram"]}
        return domain_defaults.get(domain, ["general"])

    def _select_workflow(self, intent: str, domain: str) -> list[str]:
        workflows = {
            ("strategy", "consumer"): ["data", "trends", "demographics", "domain", "visualization", "llm"],
            ("strategy", "creator"): ["data", "trends", "audience", "engagement", "visualization", "llm"],
            ("market", "financial"): ["data", "market", "sentiment", "trends", "correlation", "llm"],
            ("trend", "consumer"): ["data", "trends", "sentiment", "demographics", "correlation", "llm"],
            ("trend", "financial"): ["data", "trends", "sentiment", "correlation", "llm"],
            ("trend", "creator"): ["data", "trends", "engagement", "visualization", "llm"],
            ("demographics", "consumer"): ["data", "trends", "demographics", "sentiment", "correlation", "llm"],
            ("influence", "general"): ["data", "trends", "graph", "propagation", "llm"],
            ("sentiment", "financial"): ["data", "sentiment", "temporal", "correlation", "llm"],
            ("sentiment", "general"): ["data", "sentiment", "temporal", "llm"],
        }
        return workflows.get((intent, domain), ["data", "trends", "sentiment", "correlation", "llm"])

    def _apply_tool_config(self, plan: QueryPlan, tools_config: Optional[dict]) -> QueryPlan:
        if not tools_config:
            plan.agents_used = self.ALL_AGENTS.copy()
            plan.sources_used = plan.platforms + ["sample"]
            return plan

        mode = tools_config.get("mode", "auto")
        enabled_agents = tools_config.get("enabled_agents")
        enabled_sources = tools_config.get("enabled_sources")

        if mode == "manual" and enabled_agents:
            plan.agents_used = enabled_agents
            if "social_intelligence" not in enabled_agents:
                plan.required_capabilities = [c for c in plan.required_capabilities if c not in ("sentiment", "trends", "graph")]
            if "domain_analytics" not in enabled_agents:
                plan.required_capabilities = [c for c in plan.required_capabilities if c != "domain"]
            if "graph_analysis" not in enabled_agents:
                plan.required_capabilities = [c for c in plan.required_capabilities if c not in ("graph", "propagation")]
            if "visualization" not in enabled_agents:
                plan.required_capabilities = [c for c in plan.required_capabilities if c != "visualization"]
        else:
            plan.agents_used = self.ALL_AGENTS.copy()

        if enabled_sources:
            plan.platforms = [s for s in enabled_sources if s != "sample"]
            plan.sources_used = enabled_sources
        else:
            plan.sources_used = plan.platforms + ["sample"]

        return plan

    async def plan_and_execute(self, query: str, tools_config: Optional[dict] = None) -> dict[str, Any]:
        plan = self.parse_query(query)
        plan = self._apply_tool_config(plan, tools_config)

        raw_data = await self.data_agent.acquire(
            query=query,
            entities=plan.entities,
            domain=plan.domain,
            platforms=plan.platforms,
            time_range=plan.time_range,
        )
        plan.sources_used = raw_data.get("platforms", plan.sources_used)

        cleaned = await self.intelligence_agent.process(raw_data)
        news_articles = self._top_news_articles(
            cleaned.get("records", []),
            raw_data.get("live_sources", []),
        )

        social_analytics = {}
        if "data_acquisition" in plan.agents_used or "social_intelligence" in plan.agents_used:
            social_analytics = await self.social_agent.analyze(cleaned, capabilities=plan.required_capabilities)

        domain_analytics = {}
        run_domain = (
            plan.domain != "general"
            and ("domain_analytics" in plan.agents_used or "domain" in plan.workflow)
        )
        if run_domain:
            domain_analytics = await self.domain_agent.analyze(cleaned, domain=plan.domain, query=query)
            domain_analytics["_active_domain"] = plan.domain

        evidence = self.correlation_engine.correlate(
            social_analytics=social_analytics,
            domain_analytics=domain_analytics,
            query=query,
        )

        visualizations = []
        if "visualization" in plan.agents_used:
            visualizations = await self.viz_agent.generate(social_analytics, domain_analytics, plan.intent)

        response = await self.insight_agent.generate(
            query=query,
            evidence=evidence,
            analytics={**social_analytics, **domain_analytics},
            intent=plan.intent,
            domain=plan.domain,
            domain_label=plan.domain_label,
        )
        response_text = self._append_news_articles(response["text"], news_articles)

        return {
            "response": response_text,
            "intent": plan.intent,
            "domain": plan.domain,
            "domain_label": plan.domain_label,
            "entities": plan.entities,
            "evidence": evidence,
            "visualizations": visualizations,
            "confidence": response.get("confidence", 0.75),
            "workflow": plan.workflow,
            "agents_used": plan.agents_used,
            "sources_used": plan.sources_used,
            "news_articles": news_articles,
            "dataset_snapshot": cleaned.get("snapshot", {}),
            "model_version": response.get("model_version", "socialiq-0.1"),
        }

    def _top_news_articles(
        self, records: list[dict[str, Any]], live_sources: list[str]
    ) -> list[dict[str, Any]]:
        """Return only the top three articles actually retrieved from NewsAPI."""
        if "news" not in live_sources:
            return []

        articles = []
        for record in records:
            if record.get("platform") != "news" or not record.get("url"):
                continue
            articles.append({
                "title": record.get("title") or record.get("text", "News article"),
                "description": record.get("description", ""),
                "source": record.get("source") or record.get("author", "news"),
                "published_at": record.get("published_at") or record.get("timestamp"),
                "url": record["url"],
            })
        return articles[:3]

    def _append_news_articles(self, response: str, articles: list[dict[str, Any]]) -> str:
        if not articles:
            return response

        lines = ["**Top 3 relevant news from NewsAPI:**"]
        for index, article in enumerate(articles, start=1):
            title = article["title"].replace("[", "\\[").replace("]", "\\]")
            lines.append(f"{index}. [{title}]({article['url']}) — {article['source']}")
            if article["description"]:
                lines.append(f"   {article['description']}")
        return f"{response.rstrip()}\n\n" + "\n".join(lines)
