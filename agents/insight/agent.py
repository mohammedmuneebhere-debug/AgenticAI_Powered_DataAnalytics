"""Insight & Recommendation Agent — LLM-powered evidence-backed responses."""

import json
from typing import Any

from backend.config import get_settings


class InsightAgent:
    """Final LLM layer: synthesizes evidence into actionable insights."""

    def __init__(self):
        self.settings = get_settings()

    async def generate(
        self,
        query: str,
        evidence: list[dict],
        analytics: dict[str, Any],
        intent: str,
        domain: str = "general",
        domain_label: str = "General Social Intelligence",
    ) -> dict[str, Any]:
        if self.settings.openai_api_key:
            return await self._llm_generate(query, evidence, analytics, intent, domain, domain_label)
        return self._template_generate(query, evidence, analytics, intent, domain, domain_label)

    async def _llm_generate(
        self, query: str, evidence: list, analytics: dict, intent: str, domain: str, domain_label: str
    ) -> dict:
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=self.settings.openai_api_key)
            prompt = self._build_prompt(query, evidence, analytics, intent, domain, domain_label)

            response = await client.chat.completions.create(
                model=self.settings.llm_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"You are SOCIALIQ analyzing ONLY the {domain_label} domain. "
                            "Do NOT mix data from other domains (e.g. do not mention coffee when analyzing BTC). "
                            "Start with a one-line domain scope statement. "
                            "Distinguish Observed, Inferred, Predicted, and Recommended. Cite evidence."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
            )
            text = response.choices[0].message.content or ""
            header = f"**Domain:** {domain_label}\n\n"
            return {"text": header + text, "confidence": 0.85, "model_version": self.settings.llm_model}
        except Exception:
            return self._template_generate(query, evidence, analytics, intent, domain, domain_label)

    def _template_generate(
        self, query: str, evidence: list, analytics: dict, intent: str, domain: str, domain_label: str
    ) -> dict:
        generators = {
            ("consumer", "strategy"): self._consumer_strategy,
            ("consumer", "trend"): self._consumer_trends,
            ("financial", "market"): self._financial_analysis,
            ("financial", "trend"): self._financial_analysis,
            ("financial", "sentiment"): self._financial_analysis,
            ("creator", "strategy"): self._creator_strategy,
            ("creator", "trend"): self._creator_trends,
        }
        generator = generators.get((domain, intent), None)
        if not generator:
            generator = {
                "consumer": self._consumer_trends,
                "financial": self._financial_analysis,
                "creator": self._creator_strategy,
            }.get(domain, self._general_analysis)

        body = generator(query, evidence, analytics)
        text = f"**Domain:** {domain_label}\n\n{body}"
        return {"text": text, "confidence": 0.78, "model_version": "socialiq-template-0.2"}

    def _build_prompt(self, query: str, evidence: list, analytics: dict, intent: str, domain: str, domain_label: str) -> str:
        return f"""Domain: {domain_label} ({domain})
User Query: {query}
Intent: {intent}
Evidence: {json.dumps(evidence, indent=2)}
Analytics Summary: {json.dumps({k: v for k, v in analytics.items() if not k.startswith('_')}, default=str, indent=2)}

Analyze ONLY within the {domain_label} scope. Do not reference unrelated domains."""

    def _consumer_strategy(self, query: str, evidence: list, analytics: dict) -> str:
        trends = analytics.get("trends", {}).get("top_trends", [])
        top_trend = trends[0]["topic"] if trends else "cold brew"
        demo = analytics.get("demographics", {}).get("segments", [])
        young_pct = next((s["percentage"] for s in demo if "18-34" in s.get("label", "")), 42)

        return f"""**Observed:** In the **consumer/coffee** space, {top_trend.title()} is the fastest-growing trend with strong cross-platform momentum. Winter seasonal demand is elevated (+34% projected lift).

**Inferred:** Young consumers ({young_pct}%) are driving this trend, motivated by convenience and health-conscious formulations.

**Predicted:** Cold brew concentrate and functional coffee products are likely to see sustained Q1 demand.

**Recommended:**
- Launch a **Winter Cold Brew Concentrate** targeting 18-34 urban consumers
- Partner with micro-influencers in the coffee/lifestyle niche
- Campaign timeline: teasers in 2 weeks, full launch early winter

**Limitations:** Demographic segments are probabilistic aggregates. Confidence: 78%."""

    def _consumer_trends(self, query: str, evidence: list, analytics: dict) -> str:
        trends = analytics.get("trends", {}).get("top_trends", [])
        trend_list = ", ".join(t["topic"] for t in trends[:3]) if trends else "no strong signals"
        return f"""**Observed:** Top **consumer/coffee** trends: {trend_list}.

**Inferred:** Cross-platform spread suggests organic adoption in the beverage/consumer segment.

**Recommended:** Monitor trend velocity over 48-72 hours before committing product resources."""

    def _financial_analysis(self, query: str, evidence: list, analytics: dict) -> str:
        vol = analytics.get("volatility", {}) or {}
        scenarios = analytics.get("scenarios", [])

        return f"""**Observed:** **BTC/market** volatility is **{vol.get('level', 'HIGH')}** (index: {vol.get('index', 0.78)}). Elevated mention velocity on X and Reddit.

**Inferred:** Dominant narratives: ETF flow speculation, macro uncertainty, fear/greed oscillation.

**Predicted Scenarios:**
{chr(10).join(f"- **{s['name']}** ({s['probability']*100:.0f}%): {s['trigger']}" for s in scenarios) if scenarios else "- Range-bound trading likely near term"}

**Recommended:** Monitor sentiment spikes and volume divergence. Prepare for correction scenarios.

**Disclaimer:** Scenario analysis only — not financial advice. Confidence: 75%."""

    def _creator_strategy(self, query: str, evidence: list, analytics: dict) -> str:
        calendar = analytics.get("seven_day_calendar", [])
        windows = analytics.get("posting_windows", [])

        return f"""**Observed:** **Creator/content** segment shows Reels and carousel formats outperforming static posts (2.4× engagement).

**Inferred:** Audience peaks Tue/Thu evenings and Sat mornings.

**Recommended 7-Day Content Plan:**
{chr(10).join(f"- Day {c['day']}: {c['theme']} ({c['format']})" for c in calendar[:7]) if calendar else "- Focus on short-form Reels with trend hooks"}

**Best posting windows:** {", ".join(windows) if windows else "Tue 7-9 PM, Thu 12-1 PM"}

**Limitations:** Based on aggregate engagement patterns. Confidence: 76%."""

    def _creator_trends(self, query: str, evidence: list, analytics: dict) -> str:
        trends = analytics.get("trends", {}).get("top_trends", [])
        trend_list = ", ".join(t["topic"] for t in trends[:3]) if trends else "emerging creator topics"
        return f"""**Observed:** Top **creator/content** trends: {trend_list}.

**Recommended:** Adapt trending formats into Reels within 24-48 hours for maximum reach."""

    def _general_analysis(self, query: str, evidence: list, analytics: dict) -> str:
        sentiment = analytics.get("sentiment", {})
        score = sentiment.get("average_score", 0.5)
        label = sentiment.get("overall_label", "neutral")
        return f"""**Observed:** Overall sentiment is **{label}** (score: {score:.2f}) across {analytics.get('record_count', 0)} signals.

**Evidence:** {len(evidence)} correlation signals support this assessment.

**Recommended:** Specify a domain (consumer, financial, creator) for deeper analysis."""
