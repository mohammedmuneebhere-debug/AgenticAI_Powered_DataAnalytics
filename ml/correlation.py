"""Evidence & Correlation Engine — combines multi-dimensional signals."""

from typing import Any


class EvidenceCorrelationEngine:
    """Safeguard against unsupported LLM explanations by structuring evidence."""

    def correlate(
        self,
        social_analytics: dict[str, Any],
        domain_analytics: dict[str, Any],
        query: str,
    ) -> list[dict]:
        evidence = []

        sentiment = social_analytics.get("sentiment", {})
        if sentiment:
            evidence.append({
                "type": "statistical",
                "label": "Overall Sentiment",
                "value": sentiment.get("overall_label", "neutral"),
                "confidence": sentiment.get("confidence", 0.7),
                "source": "sentiment_model",
            })

        trends = social_analytics.get("trends", {})
        for trend in trends.get("top_trends", [])[:3]:
            evidence.append({
                "type": "semantic",
                "label": f"Trend: {trend['topic']}",
                "value": f"velocity={trend['velocity']:.2f}",
                "confidence": trend.get("confidence", 0.75),
                "source": "trend_detector",
            })

        demographics = social_analytics.get("demographics", {})
        for seg in demographics.get("segments", [])[:2]:
            evidence.append({
                "type": "demographic",
                "label": seg["label"],
                "value": f"{seg['percentage']}%",
                "confidence": seg.get("confidence", 0.6),
                "source": "demographic_segmenter",
            })

        network = social_analytics.get("network", {})
        if network.get("top_influencers"):
            evidence.append({
                "type": "network",
                "label": "Top Influencer",
                "value": network["top_influencers"][0],
                "confidence": 0.7,
                "source": "graph_analyzer",
            })

        if domain_analytics.get("product_opportunities"):
            top = domain_analytics["product_opportunities"][0]
            evidence.append({
                "type": "domain",
                "label": "Product Opportunity",
                "value": top["product"],
                "confidence": top.get("score", 0.7),
                "source": "domain_analytics",
            })

        if domain_analytics.get("volatility"):
            evidence.append({
                "type": "temporal",
                "label": "Volatility Level",
                "value": domain_analytics["volatility"]["level"],
                "confidence": 0.8,
                "source": "market_analytics",
            })

        return evidence
