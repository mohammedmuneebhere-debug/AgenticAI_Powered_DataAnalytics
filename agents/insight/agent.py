"""Insight & Recommendation Agent — LLM-powered evidence-backed responses.

Provider chain, in order:
1. OpenAI chat models (default ``gpt-4o-mini``; per request via ``llm_model``)
2. Local Ollama models (``ollama:<model>`` explicit, or auto-selected when no
   OpenAI key is configured and the local instance responds; base URL from env)
3. Offline dynamic composer — a deterministic summary built ONLY from the real
   pipeline analytics; used when both providers are unavailable or fail

When the pipeline supplies a web-search tool, both LLM providers can call it
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

    # After an OpenAI AuthenticationError (401/invalid key) the provider is
    # skipped entirely for this cooldown window so every chat doesn't pay the
    # dead-key round-trip before Ollama gets its turn.
    OPENAI_CIRCUIT_BREAKER_SECONDS = 900  # 15 minutes

    def __init__(self):
        self.settings = get_settings()
        self._openai_disabled_until: float = 0.0

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

        if self.settings.openai_api_key and not self._openai_circuit_open():
            return await self._llm_generate(
                requested, query, evidence, analytics, intent, domain, domain_label, web_search_tool
            )
        if self._openai_circuit_open():
            logger.info("OpenAI circuit breaker open (bad key); going straight to Ollama")

        # No OpenAI key: try the local Ollama instance before the offline
        # composer (opt-out via OLLAMA_AUTO_FALLBACK=false).
        if self.settings.ollama_auto_fallback and await self._ollama_available():
            return await self._ollama_generate(
                self.settings.ollama_model,
                query,
                evidence,
                analytics,
                intent,
                domain,
                domain_label,
                web_search_tool,
            )

        return self._compose_dynamic_response(query, evidence, analytics, intent, domain, domain_label)

    # ── Provider resolution ────────────────────────────────────────────

    def resolve_provider(self, llm_model: Optional[str]) -> tuple[str, str]:
        """Map the requested model id to (provider, model_name)."""
        requested = llm_model or self.settings.llm_model
        if requested.startswith("ollama:"):
            return "ollama", requested.split(":", 1)[1].strip() or self.settings.ollama_model
        return "openai", requested

    def _openai_circuit_open(self) -> bool:
        import time

        return time.monotonic() < self._openai_disabled_until

    def _trip_openai_circuit(self) -> None:
        import time

        self._openai_disabled_until = time.monotonic() + self.OPENAI_CIRCUIT_BREAKER_SECONDS
        logger.warning(
            "OpenAI authentication failed - circuit breaker open for %s minutes",
            self.OPENAI_CIRCUIT_BREAKER_SECONDS // 60,
        )

    async def _ollama_available(self) -> bool:
        """Probe the configured Ollama instance (sub-second timeout)."""
        base_url = self.settings.ollama_base_url.rstrip("/")
        try:
            async with httpx.AsyncClient(timeout=1.5) as client:
                response = await client.get(f"{base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False

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
        except Exception as exc:
            # Authentication failures mean the key itself is bad: retrying on
            # the next request cannot succeed, so open the circuit breaker.
            try:
                from openai import AuthenticationError

                auth_failure = isinstance(exc, AuthenticationError)
            except ImportError:
                auth_failure = False
            if auth_failure:
                self._trip_openai_circuit()
            logger.exception("OpenAI generation failed; trying local Ollama before composer")
            if self.settings.ollama_auto_fallback and await self._ollama_available():
                return await self._ollama_generate(
                    self.settings.ollama_model,
                    query,
                    evidence,
                    analytics,
                    intent,
                    domain,
                    domain_label,
                    web_search_tool,
                )
            return self._compose_dynamic_response(query, evidence, analytics, intent, domain, domain_label)

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
                            "keep_alive": self.settings.ollama_keep_alive,
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
            logger.exception("Ollama generation failed (%s at %s); falling back to offline composer", model, base_url)
            return self._compose_dynamic_response(query, evidence, analytics, intent, domain, domain_label)

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

    # ── Offline fallback: dynamic analytics composer ───────────────────

    def _compose_dynamic_response(
        self,
        query: str,
        evidence: list,
        analytics: dict,
        intent: str,
        domain: str,
        domain_label: str,
    ) -> dict:
        """Deterministic offline response composed ONLY from real analytics.

        Used when both OpenAI and local Ollama are unavailable or fail. Every
        number and label is drawn from the supplied ``analytics``/``evidence``;
        sections with no data are omitted rather than fabricated.
        """
        sentiment = analytics.get("sentiment") or {}
        trends = (analytics.get("trends") or {}).get("top_trends") or []
        emotion = analytics.get("emotion") or {}
        temporal = analytics.get("temporal") or {}
        timeline = temporal.get("timeline") or []
        source_counts: dict = analytics.get("source_counts") or {}
        regional_interest = (
            (analytics.get("google_trends") or {}).get("interest_by_region") or []
        )
        scenarios = analytics.get("scenarios") or []
        volatility = analytics.get("volatility") or {}
        try:
            record_count = int(analytics.get("record_count") or 0)
        except (TypeError, ValueError):
            record_count = 0

        lines: list[str] = [f"**Domain:** {domain_label}", ""]

        # ── Observed ──────────────────────────────────────────────
        lines.append("**Observed**")
        if record_count:
            ranked = sorted(source_counts.items(), key=lambda kv: -kv[1])
            source_desc = ", ".join(f"{platform} ({count})" for platform, count in ranked)
            lines.append(
                f"- Analyzed **{record_count}** social signal(s)"
                + (f" from: {source_desc}." if source_desc else ".")
            )
        else:
            lines.append("- No records were returned by the enabled data sources for this query.")

        dist = sentiment.get("distribution") or {}
        dist_total = sum(dist.values())
        if sentiment:
            mix = ""
            if dist_total:
                parts = [
                    f"{key} {value / dist_total * 100:.0f}%"
                    for key, value in sorted(dist.items(), key=lambda kv: -kv[1])
                    if value
                ]
                mix = " — mix: " + ", ".join(parts)
            lines.append(
                f"- Overall sentiment is **{sentiment.get('overall_label', 'neutral')}**"
                f" (score {float(sentiment.get('average_score', 0.5)):.2f} on 0-1){mix}."
            )

        for trend in trends[:3]:
            engagement = int(trend.get("engagement") or 0)
            lines.append(
                f"- Trend **{trend.get('topic', 'unknown')}**: {int(trend.get('mentions') or 0)} mention(s),"
                f" engagement {engagement:,}, velocity {float(trend.get('velocity') or 0):.2f}."
            )

        dominant_emotion = emotion.get("dominant_emotion")
        if dominant_emotion and dominant_emotion != "neutral":
            lines.append(f"- Dominant expressed emotion: **{dominant_emotion}**.")

        # ── Temporal movement ─────────────────────────────────────
        if timeline:
            lines += ["", "**Temporal movement**"]
            first, last = timeline[0], timeline[-1]
            first_score = float(first.get("sentiment_score") or 0)
            last_score = float(last.get("sentiment_score") or 0)
            if len(timeline) >= 2:
                delta = last_score - first_score
                direction = "rose" if delta > 0.02 else "dipped" if delta < -0.02 else "held steady"
                lines.append(
                    f"- Sentiment {direction} from {first_score:.2f} ({first.get('period', 'start')})"
                    f" to {last_score:.2f} ({last.get('period', 'end')}) across {len(timeline)} period(s)."
                )
            else:
                lines.append(
                    f"- Single-period snapshot ({first.get('period', 'all signals')}): sentiment {last_score:.2f}."
                )
            if temporal.get("spike_detected"):
                lines.append("- A positive sentiment spike was detected in this window.")

        # ── Inferred ──────────────────────────────────────────────
        inferred: list[str] = []
        top = trends[0] if trends else None
        label = sentiment.get("overall_label")
        avg_score = float(sentiment.get("average_score", 0.5))
        if top and label:
            topic = top.get("topic", "the leading trend")
            if label == "positive":
                inferred.append(
                    f"Conversation around **{topic}** carries favorable sentiment ({avg_score:.2f}),"
                    " consistent with growing organic interest."
                )
            elif label == "negative":
                inferred.append(
                    f"Discussion of **{topic}** is net-negative ({avg_score:.2f}); high volume with"
                    " negative tone warrants closer review of the underlying complaints."
                )
            else:
                inferred.append(
                    f"**{topic}** leads mentions while sentiment stays neutral ({avg_score:.2f}) —"
                    " interest without a strong emotional charge."
                )
        if volatility:
            inferred.append(
                f"Domain analytics put volatility at **{volatility.get('level', 'unspecified')}**"
                f" (index {float(volatility.get('index') or 0):.2f})."
            )
        for scenario in scenarios[:3]:
            try:
                prob = float(scenario.get("probability") or 0) * 100
            except (TypeError, ValueError):
                prob = 0.0
            inferred.append(
                f"Scenario **{scenario.get('name', 'unnamed')}** (~{prob:.0f}%):"
                f" {scenario.get('trigger', 'trigger unspecified')}."
            )
        if regional_interest:
            top_regions = [
                f"**{region.get('location', 'Unknown')}" f" ({region.get('value', 0)})**"
                for region in regional_interest[:3]
            ]
            inferred.append(
                "Google Trends interest concentrates in: " + ", ".join(top_regions)
                + " (relative 0-100 search-interest scores)."
            )
        elif record_count:
            inferred.append(
                "No regional interest data was returned for this query, so geographic"
                " audience patterns cannot be assessed from this dataset."
            )

        lines += ["", "**Inferred**"]
        if inferred:
            lines += [f"- {item}" for item in inferred]
        else:
            lines.append(
                "- Insufficient signal diversity in the returned data to infer"
                " relationships beyond the counts above."
            )

        # ── Recommended ───────────────────────────────────────────
        recs: list[str] = []
        if top:
            recs.append(
                f"Track **{top.get('topic', 'the leading trend')}** velocity over the next"
                " 48-72 hours before committing resources."
            )
        if dist_total:
            neg_share = dist.get("negative", 0) / dist_total
            pos_share = dist.get("positive", 0) / dist_total
            if neg_share >= 0.4:
                recs.append(
                    f"Negative signals are {neg_share * 100:.0f}% of the sample — review recurring"
                    " complaints in the evidence before acting."
                )
            elif pos_share >= 0.5:
                recs.append(
                    f"Positive signals are {pos_share * 100:.0f}% of the sample — a favorable window"
                    " to amplify the leading themes."
                )
        if record_count and record_count < 10:
            recs.append(
                f"Sample is small ({record_count} record(s)) — enable more sources or widen the"
                " query for sturdier conclusions."
            )
        if not recs:
            recs.append("Re-run with more sources or a refined query to gather a usable evidence base.")

        lines += ["", "**Recommended**", *[f"- {rec}" for rec in recs]]

        # ── Evidence ──────────────────────────────────────────────
        lines += ["", "**Evidence**"]
        if evidence:
            for item in evidence[:6]:
                try:
                    conf = float(item.get("confidence") or 0)
                except (TypeError, ValueError):
                    conf = 0.0
                value = item.get("value")
                value_part = f" — {value}" if value else ""
                lines.append(
                    f"- {item.get('label', 'unnamed signal')}{value_part}"
                    f" (confidence {conf * 100:.0f}%, via {item.get('source', 'unknown')})"
                )
        else:
            lines.append("- No correlation evidence was produced for this query.")

        lines += [
            "",
            "*Offline summary composed directly from pipeline analytics (no LLM available)."
            " Configure OPENAI_API_KEY or start local Ollama for narrative analysis.*",
        ]

        confidence = 0.5
        if sentiment:
            confidence += 0.1
        if trends:
            confidence += 0.1
        if timeline:
            confidence += 0.05
        if evidence:
            confidence += 0.05

        return {
            "text": "\n".join(lines),
            "confidence": round(min(confidence, 0.8), 2),
            "model_version": "socialiq-template-0.3",
        }


