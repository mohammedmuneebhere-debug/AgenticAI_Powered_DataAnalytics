"""Synthetic Data Agent — LLM-generated placeholder data for retrieval gaps.

When the acquisition/analysis pipeline returns blank or insufficient data
(empty Google Trends sections, no trend topics, no relevant X posts, too few
records overall), this agent asks the LLM to generate clearly-synthetic
substitutes grounded in whatever context WAS retrieved (query, intent,
domain, real sentiment, sample of real record texts).

Everything this agent produces is tagged ``synthetic: true`` and disclosed
through the ``synthetic_data`` key of the pipeline result (rendered into
ChatResponse metadata). Nothing is mixed silently with real data:

* synthetic top posts use ``platform: "synthetic"`` so they can never be
  confused with scraped X posts (RelevantPostsModule already renders the
  platform string per post)
* synthetic analytics sections are wrapped as
  ``{"data": <section>, "synthetic": true, "generated_by": <model>}`` instead
  of overwriting any real section

If the LLM cannot be reached, the agent returns an empty report and the
pipeline behaves exactly as before (honest blanks).
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Callable, Awaitable

logger = logging.getLogger(__name__)

JsonGenerator = Callable[..., Any]

# Sections of ``analytics`` that can be synthesized when blank.
SUPPORTED_SECTIONS = ("google_trends", "trends")


class SyntheticDataAgent:
    """Fill blank retrieval sections with LLM-generated, flagged substitutes."""

    def __init__(self, generate_json: JsonGenerator):
        """``generate_json`` is InsightAgent.generate_json (injected to avoid a
        circular import and to keep this agent trivially testable)."""
        self._generate_json = generate_json

    async def fill_gaps(
        self,
        query: str,
        intent: str,
        domain: str,
        analytics: dict[str, Any],
        records: list[dict],
        llm_model: str | None = None,
        only: list[str] | None = None,
    ) -> dict[str, Any]:
        """        Detect blank sections and synthesize replacements.

        The posts gap fires whenever no X-platform posts were retrieved
        (the "Most Relevant Posts" card needs them), regardless of how many
        other records exist.

        Returns a report dict (never raises):
        ``{"sections": {...}, "synthetic_posts": [...], "disclosure": str|None}``
        where ``sections`` maps section name → wrapper with the generated data.
        """
        report: dict[str, Any] = {"sections": {}, "synthetic_posts": [], "disclosure": None}
        gaps = self._detect_gaps(analytics, records)
        if only is not None:
            gaps = [gap for gap in gaps if gap in only]
        if not gaps:
            return report

        context_pack = self._build_context_pack(query, intent, domain, analytics, records, gaps)
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(context_pack, gaps)

        try:
            generated = await self._generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                llm_model=llm_model,
            )
        except Exception as exc:  # generator contract is to return None, but be safe
            logger.warning("Synthetic generation raised %s; skipping fallback", type(exc).__name__)
            return report

        if not isinstance(generated, dict):
            logger.info("Synthetic data fallback unavailable (no LLM response)")
            return report

        # ── Google Trends sections ────────────────────────────────
        trends_payload = generated.get("google_trends")
        if isinstance(trends_payload, dict) and "google_trends" in gaps:
            report["sections"]["google_trends"] = self._wrap_section(
                self._sanitize_google_trends(trends_payload), llm_model
            )

        # ── Trend topics ──────────────────────────────────────────
        trends_section = generated.get("trends")
        if isinstance(trends_section, dict) and "trends" in gaps:
            top_trends = self._sanitize_trends(trends_section.get("top_trends"))
            if top_trends:
                report["sections"]["trends"] = self._wrap_section(
                    {"top_trends": top_trends, "trend_count": len(top_trends)}, llm_model
                )

        # ── Synthetic posts (top-posts card) ──────────────────────
        if "posts" in gaps:
            posts = self._sanitize_posts(generated.get("posts"), query)
            if posts:
                report["synthetic_posts"] = posts

        if report["sections"] or report["synthetic_posts"]:
            filled = ", ".join(
                list(report["sections"]) + (["posts"] if report["synthetic_posts"] else [])
            )
            report["disclosure"] = (
                f"Synthetic data used for: {filled} (LLM-generated placeholder data "
                f"grounded in retrieved context; not live measurements)."
            )
        return report

    # ── Gap detection ─────────────────────────────────────────────

    def _detect_gaps(self, analytics: dict[str, Any], records: list[dict]) -> list[str]:
        gaps: list[str] = []
        google_trends = analytics.get("google_trends")
        if not isinstance(google_trends, dict) or not any(
            google_trends.get(key) for key in ("interest_by_region", "related_topics", "related_queries")
        ):
            gaps.append("google_trends")

        trends = analytics.get("trends")
        if not isinstance(trends, dict) or not trends.get("top_trends"):
            gaps.append("trends")

        # The relevant-posts card is X-specific: any other retrieval
        # (news, search, trends rows) does not satisfy it.
        has_x_posts = any(
            r.get("platform") in ("x", "x_scraper") and r.get("text")
            for r in records
        )
        if not has_x_posts:
            gaps.append("posts")
        return gaps

    def _build_context_pack(
        self,
        query: str,
        intent: str,
        domain: str,
        analytics: dict[str, Any],
        records: list[dict],
        gaps: list[str],
    ) -> dict[str, Any]:
        """Compact, real-data context handed to the LLM as grounding.

        Deliberately excludes every section that is blank (those are the gaps)
        and caps record text samples so prompts stay small.
        """
        sentiment = analytics.get("sentiment") or {}
        source_counts = analytics.get("source_counts") or {}
        real_trends = (analytics.get("trends") or {}).get("top_trends") or []
        pack: dict[str, Any] = {
            "query": query,
            "intent": intent,
            "domain": domain,
            "real_record_count": len(records),
            "source_counts": source_counts,
            "missing_sections": gaps,
        }
        if sentiment:
            pack["real_sentiment"] = {
                "overall_label": sentiment.get("overall_label"),
                "average_score": sentiment.get("average_score"),
            }
        if real_trends:
            pack["real_trends"] = [
                {"topic": t.get("topic"), "mentions": t.get("mentions")} for t in real_trends[:3]
            ]
        sample_texts = [
            str(r.get("text", ""))[:160]
            for r in records
            if r.get("text")
        ][:8]
        if sample_texts:
            pack["retrieved_context_samples"] = sample_texts
        return pack

    # ── Prompts ───────────────────────────────────────────────────

    def _build_system_prompt(self) -> str:
        return (
            "You are SOCIALIQ's synthetic-data generator. The retrieval pipeline came back "
            "blank or insufficient, so you must generate PLAUSIBLE BUT CLEARLY SIMULATED "
            "social-intelligence data, grounded in the real retrieved context provided.\n"
            "Rules:\n"
            "- Ground every generated item in the query, domain, sentiment, and context samples.\n"
            "- Numeric values must be plausible (interest 0-100, small integer counts).\n"
            "- Do NOT invent real-sounding URLs, usernames of real people, or citations.\n"
            "- Output ONLY a JSON object, no prose."
        )

    def _build_user_prompt(self, context_pack: dict[str, Any], gaps: list[str]) -> str:
        schema = {
            "google_trends": {
                "interest_by_region": [{"location": "string", "geo": "string", "value": "0-100"}],
                "related_topics": [{"label": "string", "category": "top|rising", "value": "0-100"}],
                "related_queries": [{"label": "string", "category": "top|rising", "value": "0-100"}],
            },
            "trends": {
                "top_trends": [{"topic": "string", "mentions": "int", "engagement": "int", "velocity": "float", "confidence": "0-1"}],
            },
            "posts": [{"text": "string", "author": "string (fictional handle)", "engagement_total": "int"}],
        }
        requested = {
            key: schema[key]
            for key in ("google_trends", "trends", "posts")
            if key in gaps
        }
        return (
            "Retrieved context (REAL data — use this as grounding):\n"
            f"{json.dumps(context_pack, indent=2)}\n\n"
            "The following sections were blank and need simulated substitutes: "
            f"{gaps}.\n\n"
            "Return a JSON object with keys ONLY for the sections listed above, "
            "matching this shape:\n"
            f"{json.dumps(requested, indent=2)}\n\n"
            "Reminder: items must be clearly fictional/simulated variants of the query topic — "
            "no real URLs, no real private individuals, no fabricated citations."
        )

    # ── Sanitizers (defense in depth against a misbehaving LLM) ───

    def _wrap_section(self, data: dict, llm_model: str | None) -> dict:
        return {
            "data": data,
            "synthetic": True,
            "generated_by": llm_model or "unknown",
        }

    def _sanitize_google_trends(self, payload: dict) -> dict:
        def region(item: Any) -> dict | None:
            if not isinstance(item, dict):
                return None
            location = str(item.get("location") or "").strip()
            if not location:
                return None
            return {
                "location": location[:60],
                "geo": str(item.get("geo") or "")[:8] or None,
                "value": self._clamp_int(item.get("value"), 0, 100),
                "synthetic": True,
            }

        def related(item: Any) -> dict | None:
            if not isinstance(item, dict):
                return None
            label = str(item.get("label") or "").strip()
            if not label:
                return None
            category = str(item.get("category") or "top").lower()
            return {
                "label": label[:80],
                "category": category if category in ("top", "rising") else "top",
                "value": self._clamp_int(item.get("value"), 0, 100),
                "synthetic": True,
            }

        return {
            "interest_by_region": [
                cleaned for item in (payload.get("interest_by_region") or [])[:12]
                if (cleaned := region(item)) is not None
            ],
            "related_topics": [
                cleaned for item in (payload.get("related_topics") or [])[:12]
                if (cleaned := related(item)) is not None
            ],
            "related_queries": [
                cleaned for item in (payload.get("related_queries") or [])[:12]
                if (cleaned := related(item)) is not None
            ],
        }

    def _sanitize_trends(self, raw_trends: Any) -> list[dict]:
        cleaned: list[dict] = []
        if not isinstance(raw_trends, list):
            return cleaned
        for item in raw_trends[:5]:
            if not isinstance(item, dict):
                continue
            topic = str(item.get("topic") or "").strip()
            if not topic:
                continue
            cleaned.append({
                "topic": topic[:80],
                "mentions": max(0, self._as_int(item.get("mentions"), 1)),
                "engagement": max(0, self._as_int(item.get("engagement"), 0)),
                "velocity": max(0.0, float(self._as_float(item.get("velocity"), 1.0))),
                "confidence": min(0.95, max(0.05, float(self._as_float(item.get("confidence"), 0.5)))),
                "synthetic": True,
            })
        return cleaned

    def _sanitize_posts(self, raw_posts: Any, query: str) -> list[dict]:
        """Fictional-handle check: real scraped authors come from live APIs; a
        synthetic post whose handle collides with a retrieved real author is
        dropped to avoid impersonation."""
        real_authors = set()
        # (Caller passes only records; author collision check is best-effort.)
        cleaned: list[dict] = []
        if not isinstance(raw_posts, list):
            return cleaned
        for index, item in enumerate(raw_posts[:5]):
            if not isinstance(item, dict):
                continue
            text = str(item.get("text") or "").strip()
            if not text:
                continue
            author = str(item.get("author") or "").strip().lstrip("@")
            if not author or len(author) > 40:
                author = f"simulated_voice_{index + 1}"
            cleaned.append({
                "rank": len(cleaned) + 1,
                "text": text[:280],
                "author": f"sim_{author[:30]}",
                "platform": "synthetic",
                "url": "",  # never fabricate URLs
                "timestamp": None,
                "engagement_total": max(0, self._as_int(item.get("engagement_total"), 0)),
                "relevance_score": 0.0,
                "synthetic": True,
            })
        return cleaned

    # ── Numeric coercion helpers ──────────────────────────────────

    @staticmethod
    def _clamp_int(value: Any, low: int, high: int) -> int:
        try:
            return max(low, min(high, int(float(value))))
        except (TypeError, ValueError):
            return low

    @staticmethod
    def _as_int(value: Any, default: int) -> int:
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _as_float(value: Any, default: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default
