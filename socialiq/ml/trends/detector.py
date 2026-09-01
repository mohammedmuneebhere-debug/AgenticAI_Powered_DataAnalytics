"""Trend detection — velocity, growth, cross-platform spread."""

from typing import Any
from collections import Counter


TREND_KEYWORDS = {
    "cold brew": ["cold brew", "cold-brew", "concentrate"],
    "functional coffee": ["adaptogen", "functional", "mushroom coffee", "nootropic"],
    "premium pods": ["single origin", "premium pod", "nespresso"],
    "btc etf": ["etf", "inflow", "institutional"],
    "btc volatility": ["volatile", "volatility", "swing", "whipsaw"],
    "fear sentiment": ["fear", "crash", "correction", "bear"],
}


class TrendDetector:
    def detect(self, records: list[dict]) -> dict[str, Any]:
        text_corpus = " ".join(r.get("text", "").lower() for r in records)
        trends = []

        for topic, keywords in TREND_KEYWORDS.items():
            mentions = sum(text_corpus.count(kw) for kw in keywords)
            if mentions > 0:
                engagement = sum(
                    r.get("engagement", {}).get("likes", 0)
                    + r.get("engagement", {}).get("reposts", 0)
                    for r in records
                    if any(kw in r.get("text", "").lower() for kw in keywords)
                )
                velocity = mentions * 0.3 + engagement * 0.001
                trends.append({
                    "topic": topic,
                    "mentions": mentions,
                    "engagement": engagement,
                    "velocity": round(velocity, 2),
                    "confidence": min(0.95, 0.5 + mentions * 0.1),
                })

        trends.sort(key=lambda t: t["velocity"], reverse=True)
        return {"top_trends": trends[:5], "trend_count": len(trends)}
