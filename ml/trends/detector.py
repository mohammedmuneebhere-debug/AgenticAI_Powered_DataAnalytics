"""Trend detection — data-driven terms with mention-velocity z-scores.

Replaces the hardcoded TREND_KEYWORDS (leftover coffee/BTC demos) with a
generic, dataset-driven detector:

1. Candidate terms are the most frequent tokens/hashtags in THIS dataset
   (document frequency, so one verbose post cannot dominate).
2. For every candidate, daily mention counts are built from record timestamps
   and a z-score is computed for the most recent day against the prior days:
       z = (recent_count - mean(prior)) / (std(prior) + epsilon)
   A high z means the term accelerated NOW relative to its own baseline —
   real "trending" behavior, not just popularity.
3. Without usable timestamps (all records from one day, or none), the method
   falls back to the frequency+engagement score and says so.

Output shape (superset of the original — consumers only read known keys):

    {"top_trends": [{topic, mentions, engagement, velocity, confidence,
                     z_score?, growth_pct?, method}], "trend_count": n,
     "method": "velocity_zscore" | "frequency"}

Optional Prophet forecast (settings.trend_forecast_enabled): fits the top
term's daily series when it has >= 7 days of history and returns
{"forecast": {"topic", "points": [{"ds", "yhat"}]}} — any failure degrades
to {"forecast": None}.
"""

import math
import re
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any

from backend.config import get_settings

STOPWORDS = {
    "about", "after", "and", "are", "from", "into", "that", "the", "this",
    "with", "what", "signal", "discussion", "https", "http", "www", "com",
    "just", "have", "has", "was", "were", "will", "your", "they", "them",
    "their", "there", "than", "then", "when", "which", "while", "who",
    "why", "you", "not", "but", "for", "all", "can", "get", "out", "one",
    "our", "how", "its", "it's", "more", "over", "some", "very",
}


class TrendDetector:
    def detect(self, records: list[dict]) -> dict[str, Any]:
        corpus_texts = [str(r.get("text", "")) for r in records]
        candidates = self._candidate_terms(corpus_texts, limit=12)
        if not candidates:
            return {"top_trends": [], "trend_count": 0, "method": "frequency", "forecast": None}

        daily_counts, total_mentions = self._daily_counts(records, candidates)
        has_history = self._has_multi_day_history(daily_counts)

        trends = []
        for term in candidates:
            mentions = total_mentions.get(term, 0)
            if mentions == 0:
                continue
            engagement = self._engagement_for(records, term)
            if has_history:
                z, growth = self._velocity_zscore(daily_counts.get(term, {}))
                velocity = round(max(0.0, z) * 5 + min(mentions, 50) * 0.05, 2)
                confidence = min(0.95, 0.5 + max(0.0, z) * 0.08)
                trends.append({
                    "topic": term,
                    "mentions": mentions,
                    "engagement": engagement,
                    "velocity": velocity,
                    "z_score": round(z, 2),
                    "growth_pct": round(growth, 1) if growth is not None else None,
                    "confidence": round(confidence, 2),
                    "method": "velocity_zscore",
                })
            else:
                velocity = round(mentions * 0.3 + engagement * 0.001, 2)
                trends.append({
                    "topic": term,
                    "mentions": mentions,
                    "engagement": engagement,
                    "velocity": velocity,
                    "confidence": round(min(0.9, 0.4 + mentions * 0.1), 2),
                    "method": "frequency",
                })

        trends.sort(key=lambda t: t["velocity"], reverse=True)
        result: dict[str, Any] = {
            "top_trends": trends[:5],
            "trend_count": len(trends),
            "method": "velocity_zscore" if has_history else "frequency",
        }
        if get_settings().trend_forecast_enabled and has_history:
            result["forecast"] = self._forecast_top(trends, daily_counts)
        else:
            result["forecast"] = None
        return result

    # -- candidates ------------------------------------------------------------

    @staticmethod
    def _candidate_terms(texts: list[str], limit: int) -> list[str]:
        """Document-frequency ranking: a term must appear in several records."""
        doc_freq: Counter = Counter()
        for text in texts:
            lowered = text.lower()
            terms = set(re.findall(r"#\w{2,40}", lowered))
            terms |= {
                t for t in re.findall(r"\b[a-z][a-z0-9-]{2,}\b", lowered)
                if t not in STOPWORDS and len(t) > 2 and not t.isdigit()
            }
            doc_freq.update(terms)
        # Deterministic ranking: count desc, then alphabetical. Set iteration
        # order is hash-seed dependent, so it must never decide tie-breaks.
        ranked = sorted(doc_freq.items(), key=lambda kv: (-kv[1], kv[0]))
        return [term for term, _ in ranked[:limit]]

    # -- time series -------------------------------------------------------------

    @staticmethod
    def _daily_counts(records: list[dict], candidates: list[str]) -> tuple[dict[str, dict[str, int]], dict[str, int]]:
        daily: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        totals: Counter = Counter()
        for record in records:
            text = str(record.get("text", "")).lower()
            day = TrendDetector._record_day(record)
            for term in candidates:
                if term in text:
                    totals[term] += 1
                    if day is not None:
                        daily[term][day] += 1
        return daily, totals

    @staticmethod
    def _record_day(record: dict) -> str | None:
        timestamp = record.get("timestamp")
        if not timestamp:
            return None
        try:
            return datetime.fromisoformat(str(timestamp).replace("Z", "+00:00")).date().isoformat()
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _has_multi_day_history(daily: dict[str, dict[str, int]]) -> bool:
        all_days = set()
        for series in daily.values():
            all_days |= set(series)
        return len(all_days) >= 2

    @staticmethod
    def _velocity_zscore(series: dict[str, int]) -> tuple[float, float | None]:
        """z-score of the latest day vs prior days + % growth vs prior mean."""
        if not series:
            return 0.0, None
        ordered = sorted(series.items())
        *prior, (latest_day, latest_count) = ordered
        if not prior:
            return 0.0, None
        prior_values = [count for _, count in prior]
        mean = sum(prior_values) / len(prior_values)
        variance = sum((v - mean) ** 2 for v in prior_values) / len(prior_values)
        std = math.sqrt(variance)
        z = (latest_count - mean) / (std + 0.75)  # epsilon guards tiny baselines
        growth = ((latest_count - mean) / mean * 100) if mean > 0 else None
        return z, growth

    # -- engagement ----------------------------------------------------------------

    @staticmethod
    def _engagement_for(records: list[dict], term: str) -> int:
        total = 0
        for record in records:
            if term not in str(record.get("text", "")).lower():
                continue
            engagement = record.get("engagement") or {}
            if isinstance(engagement, dict):
                total += int(engagement.get("likes") or 0) + int(engagement.get("reposts") or 0)
        return total

    # -- optional Prophet forecast ---------------------------------------------------

    @staticmethod
    def _forecast_top(trends: list[dict], daily: dict[str, dict[str, int]]) -> dict[str, Any] | None:
        """Forecast the top trend's next 7 days with Prophet (best effort)."""
        if not trends:
            return None
        topic = trends[0]["topic"]
        series = daily.get(topic, {})
        if len(series) < 7:
            return None
        try:
            import pandas as pd
            from prophet import Prophet
        except Exception as exc:  # prophet optional; never break the pipeline
            return {"topic": topic, "points": [], "error": f"prophet unavailable: {exc.__class__.__name__}"}
        try:
            frame = pd.DataFrame(
                [(day, count) for day, count in sorted(series.items())],
                columns=["ds", "y"],
            )
            model = Prophet(daily_seasonality=False, weekly_seasonality=False, yearly_seasonality=False)
            model.fit(frame)
            future = model.make_future_dataframe(periods=7)
            forecast = model.predict(future).tail(7)
            return {
                "topic": topic,
                "points": [
                    {"ds": str(row.ds.date()), "yhat": round(float(row.yhat), 2)}
                    for row in forecast.itertuples()
                ],
            }
        except Exception as exc:
            return {"topic": topic, "points": [], "error": f"forecast failed: {exc.__class__.__name__}"}
