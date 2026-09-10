"""Insight & Recommendation Agent — LLM-powered evidence-backed responses.

Supports two providers, selected per request via ``llm_model``:
- OpenAI chat models (default, ``gpt-4o-mini`` unless configured otherwise)
- Local Ollama models (``ollama:<model>``), base URL configurable via env

When the pipeline supplies a web-search tool, both providers can call it
(OpenAI via native function calling, Ollama via a JSON tool protocol) to pull
additional live results before composing the final answer.
"""

import json
import logging
from typing import Any, Awaitable, Callable, Optional
from urllib.parse import urlparse

import httpx

from backend.config import get_settings, split_allowed_domains

logger = logging.getLogger(__name__)

WebSearchTool = Callable[[str, int], Awaitable[list[dict]]]

WEB_SEARCH_TOOL_SPEC = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": (
            "Search the web for current information. Use when the query needs "
            "recent events, live prices, or facts beyond the supplied evidence."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Focused search query (keywords, not sentences).",
                },
                "max_results": {
                    "type": "integer",
                    "description": "How many results to return (1-6).",
                },
            },
            "required": ["query"],
        },
    },
}


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
        llm_model: Optional[str] = None,
        web_search_tool: Optional[WebSearchTool] = None,
    ) -> dict[str, Any]:
        requested = llm_model or self.settings.llm_model

        if requested.startswith("ollama:"):
            model = requested.split(":", 1)[1].strip() or self.settings.ollama_model
            return await self._ollama_generate(
                model, query, evidence, analytics, intent, domain, domain_label, web_search_tool
            )

        if self.settings.openai_api_key:
            return await self._llm_generate(
                requested, query, evidence, analytics, intent, domain, domain_label, web_search_tool
            )
        return self._template_generate(query, evidence, analytics, intent, domain, domain_label)

    # ── Provider resolution ────────────────────────────────────────────

    def resolve_provider(self, llm_model: Optional[str]) -> tuple[str, str]:
        """Map the requested model id to (provider, model_name)."""
        requested = llm_model or self.settings.llm_model
        if requested.startswith("ollama:"):
            return "ollama", requested.split(":", 1)[1].strip() or self.settings.ollama_model
        return "openai", requested

    # ── OpenAI ─────────────────────────────────────────────────────────

    async def _llm_generate(
        self,
        model: str,
        query: str,
        evidence: list,
        analytics: dict,
        intent: str,
        domain: str,
        domain_label: str,
        web_search_tool: Optional[WebSearchTool] = None,
    ) -> dict:
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=self.settings.openai_api_key)
            system_prompt = self._build_system_prompt(domain_label, web_search_tool)
            user_prompt = self._build_prompt(query, evidence, analytics, intent, domain, domain_label)

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
            tools = [WEB_SEARCH_TOOL_SPEC] if web_search_tool else None
            tool_rounds = 0

            while True:
                kwargs: dict[str, Any] = {
                    "model": model,
                    "messages": messages,
                    "temperature": 0.3,
                }
                if tools and tool_rounds < 3:
                    kwargs["tools"] = tools
                response = await client.chat.completions.create(**kwargs)
                choice = response.choices[0]
                message = choice.message

                calls = list(message.tool_calls or [])
                if not tools or not calls or tool_rounds >= 3:
                    text = message.content or ""
                    break

                tool_rounds += 1
                messages.append(
                    {
                        "role": "assistant",
                        "content": message.content,
                        "tool_calls": [
                            {
                                "id": call.id,
                                "type": "function",
                                "function": {
                                    "name": call.function.name,
                                    "arguments": call.function.arguments,
                                },
                            }
                            for call in calls
                        ],
                    }
                )
                for call in calls:
                    result = await self._run_tool_call(
                        web_search_tool,
                        call.function.name,
                        call.function.arguments,
                    )
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": call.id,
                            "content": json.dumps(result, default=str),
                        }
                    )

            header = f"**Domain:** {domain_label}\n\n"
            return {"text": header + text, "confidence": 0.85, "model_version": model}
        except Exception:
            logger.exception("OpenAI generation failed; falling back to templates")
            return self._template_generate(query, evidence, analytics, intent, domain, domain_label)

    # ── Ollama ─────────────────────────────────────────────────────────

    async def _ollama_generate(
        self,
        model: str,
        query: str,
        evidence: list,
        analytics: dict,
        intent: str,
        domain: str,
        domain_label: str,
        web_search_tool: Optional[WebSearchTool] = None,
    ) -> dict:
        """Generate via a local Ollama instance (base URL from OLLAMA_BASE_URL)."""
        base_url = self.settings.ollama_base_url.rstrip("/")
        system_prompt = self._build_system_prompt(domain_label, web_search_tool)
        user_prompt = self._build_prompt(query, evidence, analytics, intent, domain, domain_label)

        messages: list[dict] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                # Manual tool loop: Ollama's function-calling support varies by
                # model, so we keep the protocol explicit and bounded.
                for _ in range(3):
                    response = await client.post(
                        f"{base_url}/api/chat",
                        json={
                            "model": model,
                            "messages": messages,
                            "stream": False,
                            "options": {"temperature": 0.3},
                        },
                    )
                    response.raise_for_status()
                    payload = response.json()
                    message = payload.get("message") or {}
                    content = message.get("content") or ""
                    tool_calls = message.get("tool_calls") or []

                    if not web_search_tool or not tool_calls:
                        text = content
                        break

                    messages.append(message)
                    executed = False
                    for call in tool_calls:
                        fn = call.get("function") or {}
                        result = await self._run_tool_call(
                            web_search_tool, fn.get("name", ""), fn.get("arguments") or {}
                        )
                        if result:
                            executed = True
                            messages.append(
                                {
                                    "role": "tool",
                                    "content": json.dumps(result, default=str),
                                }
                            )
                    if not executed:
                        text = content
                        break
                else:
                    text = messages[-1].get("content", "")

            header = f"**Domain:** {domain_label}\n\n"
            return {"text": header + text, "confidence": 0.8, "model_version": f"ollama:{model}"}
        except Exception:
            logger.exception("Ollama generation failed (%s at %s); falling back to templates", model, base_url)
            return self._template_generate(query, evidence, analytics, intent, domain, domain_label)

    # ── Web search tool execution ──────────────────────────────────────

    async def _run_tool_call(
        self, tool: Optional[WebSearchTool], name: str, raw_args: Any
    ) -> list[dict] | dict:
        """Execute a web_search tool call, applying safety guards."""
        if not tool or name != "web_search":
            return {"error": f"Unknown tool: {name}"}

        args: dict = {}
        if isinstance(raw_args, str):
            try:
                args = json.loads(raw_args or "{}")
            except json.JSONDecodeError:
                args = {"query": raw_args}
        elif isinstance(raw_args, dict):
            args = raw_args

        query = str(args.get("query", "")).strip()
        if not query:
            return {"error": "web_search requires a non-empty query"}

        max_results = args.get("max_results") or self.settings.web_search_max_results
        try:
            max_results = max(1, min(int(max_results), 6))
        except (TypeError, ValueError):
            max_results = self.settings.web_search_max_results

        try:
            results = await tool(query, max_results)
        except Exception as exc:
            logger.warning("web_search tool failed: %s", type(exc).__name__)
            return {"error": f"web_search failed: {type(exc).__name__}"}

        allowed = split_allowed_domains(self.settings.web_search_allowed_domains)
        filtered = []
        for result in results:
            url = result.get("url") or ""
            host = urlparse(url).netloc.lower() if url else ""
            if allowed and host and not any(host == d or host.endswith(f".{d}") for d in allowed):
                continue
            filtered.append({k: v for k, v in result.items() if k != "content"} | {
                "content": (result.get("content") or "")[:1200]
            })
            if len(filtered) >= max_results:
                break

        return {
            "query": query,
            "results": filtered,
            "instructions": (
                "Cite these results inline as [Source: url] where used. "
                "Never fabricate URLs that are not listed here."
            ),
        }

    # ── Prompts ────────────────────────────────────────────────────────

    def _build_system_prompt(self, domain_label: str, web_search_tool: Optional[WebSearchTool]) -> str:
        lines = [
            f"You are SOCIALIQ analyzing ONLY the {domain_label} domain.",
            "Do NOT mix data from other domains (e.g. do not mention coffee when analyzing BTC).",
            "Start with a one-line domain scope statement.",
            "Distinguish Observed, Inferred, Predicted, and Recommended sections.",
            "Cite evidence: when a claim draws on a supplied evidence item or web search result,",
            "reference it explicitly (e.g. [Source: url] for web results).",
            "Never fabricate statistics, sources, or URLs.",
        ]
        if web_search_tool:
            lines.append(
                "You have a web_search tool for current information. Call it when the evidence "
                "is insufficient for recency-sensitive questions (live prices, recent events), "
                "then ground your answer in both the pipeline evidence and the search results."
            )
        return "\n".join(lines)

    def _build_prompt(self, query: str, evidence: list, analytics: dict, intent: str, domain: str, domain_label: str) -> str:
        return f"""Domain: {domain_label} ({domain})
User Query: {query}
Intent: {intent}
Evidence: {json.dumps(evidence, indent=2)}
Analytics Summary: {json.dumps({k: v for k, v in analytics.items() if not k.startswith('_')}, default=str, indent=2)}

Analyze ONLY within the {domain_label} scope. Do not reference unrelated domains."""

    # ── Template fallback (offline, deterministic) ─────────────────────

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

        return f"""**Observed:** **Creator/content** segment shows Reels and carousel formats outperforming static posts (2.4x engagement).

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
