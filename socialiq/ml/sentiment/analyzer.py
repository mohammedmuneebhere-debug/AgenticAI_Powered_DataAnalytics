"""Sentiment analysis using rule-based + transformer-ready interface."""

from typing import Any


POSITIVE_WORDS = {"love", "great", "amazing", "best", "excited", "bullish", "growth", "premium", "delicious"}
NEGATIVE_WORDS = {"hate", "bad", "worst", "fear", "crash", "bearish", "disappointed", "overpriced", "scam"}


class SentimentAnalyzer:
    def analyze_batch(self, texts: list[str]) -> dict[str, Any]:
        if not texts:
            return {"overall_label": "neutral", "average_score": 0.5, "confidence": 0.0, "distribution": {}}

        scores = [self._score(t) for t in texts]
        avg = sum(scores) / len(scores)

        positive = sum(1 for s in scores if s > 0.6)
        negative = sum(1 for s in scores if s < 0.4)
        neutral = len(scores) - positive - negative

        label = "positive" if avg > 0.55 else "negative" if avg < 0.45 else "neutral"

        return {
            "overall_label": label,
            "average_score": round(avg, 3),
            "confidence": 0.72,
            "distribution": {"positive": positive, "negative": negative, "neutral": neutral},
            "scores": scores,
        }

    def _score(self, text: str) -> float:
        words = set(text.lower().split())
        pos = len(words & POSITIVE_WORDS)
        neg = len(words & NEGATIVE_WORDS)
        if pos + neg == 0:
            return 0.5
        return max(0.0, min(1.0, 0.5 + (pos - neg) * 0.15))
