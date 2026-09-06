"""Social Intelligence Agent — sentiment, trends, demographics, graph analytics."""

from typing import Any

from ml.sentiment.analyzer import SentimentAnalyzer
from ml.emotion.analyzer import EmotionAnalyzer
from ml.topics.detector import TopicDetector
from ml.trends.detector import TrendDetector
from ml.demographics.segmenter import DemographicSegmenter
from graph.analyzer import GraphAnalyzer


class SocialIntelligenceAgent:
    """Central analytical layer for social signals."""

    def __init__(self):
        self.sentiment = SentimentAnalyzer()
        self.emotion = EmotionAnalyzer()
        self.topics = TopicDetector()
        self.trends = TrendDetector()
        self.demographics = DemographicSegmenter()
        self.graph = GraphAnalyzer()

    async def analyze(self, dataset: dict[str, Any], capabilities: list[str]) -> dict[str, Any]:
        records = dataset.get("records", [])
        texts = [r.get("text", "") for r in records]

        results: dict[str, Any] = {"record_count": len(records)}

        if any(c in capabilities for c in ["data", "sentiment", "correlation", "llm"]):
            results["sentiment"] = self.sentiment.analyze_batch(texts)
            results["emotion"] = self.emotion.analyze_batch(texts)
            results["temporal"] = self._temporal_analysis(
                records,
                results["sentiment"],
            )

        if any(c in capabilities for c in ["trends", "data"]):
            results["topics"] = self.topics.detect(texts)
            results["trends"] = self.trends.detect(records)

        if "demographics" in capabilities:
            results["demographics"] = self.demographics.segment(records)

        if any(c in capabilities for c in ["graph", "propagation", "influence"]):
            results["network"] = self.graph.analyze(records)

        return results

    def _temporal_analysis(self, records: list[dict], sentiment: dict) -> dict:
        from collections import defaultdict
        from datetime import datetime

        scores = sentiment.get("scores", [])
        grouped: dict[str, list[float]] = defaultdict(list)
        for index, record in enumerate(records):
            timestamp = record.get("timestamp")
            try:
                label = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00")).date().isoformat()
            except (TypeError, ValueError):
                label = f"Signal {index + 1}"
            if index < len(scores):
                grouped[label].append(scores[index])

        timeline = [
            {
                "period": period,
                "sentiment_score": round(sum(values) / len(values), 3),
                "signal_count": len(values),
                "distribution": {
                    "positive": sum(1 for value in values if value > 0.6),
                    "neutral": sum(1 for value in values if 0.4 <= value <= 0.6),
                    "negative": sum(1 for value in values if value < 0.4),
                },
            }
            for period, values in sorted(grouped.items())
            if values
        ]
        if not timeline:
            timeline = [{"period": "All signals", "sentiment_score": sentiment.get("average_score", 0.5), "signal_count": len(records), "distribution": sentiment.get("distribution", {})}]

        return {
            "timeline": timeline,
            "spike_detected": sentiment.get("average_score", 0.5) > 0.6,
        }
