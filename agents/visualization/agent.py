"""Visualization Agent — generates chart specs for the frontend."""

from typing import Any


class VisualizationAgent:
    """Produces visualization specifications from analytics results."""

    async def generate(
        self,
        social_analytics: dict[str, Any],
        domain_analytics: dict[str, Any],
        intent: str,
    ) -> list[dict]:
        viz = []

        sentiment = social_analytics.get("sentiment", {})
        temporal = social_analytics.get("temporal", {})
        timeline = temporal.get("timeline", [])
        if timeline:
            viz.append({
                "type": "sentiment_timeline",
                "title": "Sentiment Over Time",
                "data": {
                    "labels": [point["period"] for point in timeline],
                    "values": [point["sentiment_score"] for point in timeline],
                },
            })

        trends = social_analytics.get("trends", {})
        if trends.get("top_trends"):
            viz.append({
                "type": "trend_bars",
                "title": "Top Trends",
                "data": {
                    "labels": [t["topic"] for t in trends["top_trends"][:5]],
                    "values": [t["velocity"] for t in trends["top_trends"][:5]],
                },
            })

        demographics = social_analytics.get("demographics", {})
        if demographics.get("segments"):
            viz.append({
                "type": "demographic_pie",
                "title": "Audience Segments",
                "data": {
                    "labels": [s["label"] for s in demographics["segments"]],
                    "values": [s["percentage"] for s in demographics["segments"]],
                },
            })

        network = social_analytics.get("network", {})
        if network.get("nodes"):
            viz.append({
                "type": "network_graph",
                "title": "Influence Network",
                "data": {"nodes": network["nodes"], "edges": network["edges"]},
            })

        if domain_analytics.get("scenarios"):
            viz.append({
                "type": "scenario_matrix",
                "title": "Scenario Analysis",
                "data": {
                    "scenarios": domain_analytics.get("scenarios", []),
                    "volatility": domain_analytics.get("volatility", {}),
                },
            })

        if domain_analytics.get("product_opportunities"):
            viz.append({
                "type": "opportunity_matrix",
                "title": "Product Opportunities",
                "data": {"opportunities": domain_analytics["product_opportunities"]},
            })

        return viz
