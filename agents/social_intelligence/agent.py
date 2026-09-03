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

        if any(c in capabilities for c in ["trends", "data"]):
            results["topics"] = self.topics.detect(texts)
            results["trends"] = self.trends.detect(records)

        if "demographics" in capabilities:
            results["demographics"] = self.demographics.segment(records)

        if any(c in capabilities for c in ["graph", "propagation", "influence"]):
            results["network"] = self.graph.analyze(records)

        if "temporal" in capabilities:
            results["temporal"] = self._temporal_analysis(records, results.get("sentiment", {}))

        return results

    def _temporal_analysis(self, records: list[dict], sentiment: dict) -> dict:
        return {
            "timeline": [
                {"period": "last_24h", "sentiment_score": sentiment.get("average_score", 0.5)},
                {"period": "last_7d", "sentiment_score": sentiment.get("average_score", 0.5) * 0.95},
            ],
            "spike_detected": sentiment.get("average_score", 0.5) > 0.6,
        }
