"""Sentiment analysis — VADER (default) or transformer backend.

Public shape (unchanged from the original heuristic version):

    SentimentAnalyzer().analyze_batch(texts) -> {
        "overall_label":  "positive" | "negative" | "neutral",
        "average_score":  float in [0, 1] (0.5 = neutral),
        "confidence":     float in [0, 1],
        "distribution":   {"positive": n, "negative": n, "neutral": n},
        "scores":         [float] per input text,
    }

Backends (settings.ml_sentiment_backend):
    * "vader"        — VADER compound score mapped to [0, 1]; fast, no GPU,
                       robust for social text. Default.
    * "transformer"  — cardiffnlp/twitter-roberta-base-sentiment-latest via
                       transformers; lazy-loaded on first use and falls back
                       to VADER when weights are unavailable (offline, no
                       model cached).
"""

import logging
from typing import Any

from backend.config import get_settings

logger = logging.getLogger(__name__)

POSITIVE_WORDS = {"love", "great", "amazing", "best", "excited", "bullish", "growth", "premium", "delicious"}
NEGATIVE_WORDS = {"hate", "bad", "worst", "fear", "crash", "bearish", "disappointed", "overpriced", "scam"}

TRANSFORMER_MODEL = "cardiffnlp/twitter-roberta-base-sentiment-latest"

# Label id -> (label, polarity) for the cardiffnlp sentiment model
_TRANSFORMER_LABELS = {
    "positive": ("positive", 1.0),
    "neutral": ("neutral", 0.5),
    "negative": ("negative", 0.0),
}


class SentimentAnalyzer:
    def __init__(self, backend: str | None = None):
        self.backend_name = backend or get_settings().ml_sentiment_backend
        self._vader = None
        self._transformer = None
        self._transformer_failed = False

    # -- public API ----------------------------------------------------------

    def analyze_batch(self, texts: list[str]) -> dict[str, Any]:
        if not texts:
            return {"overall_label": "neutral", "average_score": 0.5, "confidence": 0.0, "distribution": {}}

        if self.backend_name == "transformer":
            scores = self._scores_transformer(texts)
        else:
            scores = self._scores_vader(texts)

        avg = sum(scores) / len(scores)
        positive = sum(1 for s in scores if s > 0.6)
        negative = sum(1 for s in scores if s < 0.4)
        neutral = len(scores) - positive - negative
        label = "positive" if avg > 0.55 else "negative" if avg < 0.45 else "neutral"

        # Confidence from how far the batch sits away from the neutral middle
        confidence = round(min(1.0, max(0.1, abs(avg - 0.5) * 2.2)), 3)

        return {
            "overall_label": label,
            "average_score": round(avg, 3),
            "confidence": confidence,
            "distribution": {"positive": positive, "negative": negative, "neutral": neutral},
            "scores": scores,
            "backend": self.backend_name,
        }

    # -- VADER ----------------------------------------------------------------

    def _get_vader(self):
        if self._vader is None:
            from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

            self._vader = SentimentIntensityAnalyzer()
        return self._vader

    def _scores_vader(self, texts: list[str]) -> list[float]:
        vader = self._get_vader()
        return [round((vader.polarity_scores(str(t))["compound"] + 1) / 2, 4) for t in texts]

    # -- transformer ------------------------------------------------------------

    def _scores_transformer(self, texts: list[str]) -> list[float]:
        pipe = self._get_transformer()
        if pipe is None:
            logger.info("Transformer sentiment unavailable — falling back to VADER")
            return self._scores_vader(texts)
        scores: list[float] = []
        for t in texts:
            try:
                result = pipe(str(t)[:512], truncation=True)[0]
                label = str(result.get("label", "")).lower()
                base = _TRANSFORMER_LABELS.get(label, ("neutral", 0.5))[1]
                strength = float(result.get("score", 0.5))
                # Push the class polarity toward 0/1 by its model confidence,
                # keeping the shared [0, 1] score space (0.5 = neutral)
                polarity = 2 * abs(base - 0.5)
                scores.append(round(0.5 + polarity * (strength - 0.5), 4))
            except Exception:
                scores.append(0.5)
        return scores

    def _get_transformer(self):
        if self._transformer is None and not self._transformer_failed:
            try:
                from transformers import pipeline

                self._transformer = pipeline(
                    "sentiment-analysis", model=TRANSFORMER_MODEL, truncation=True
                )
            except Exception as exc:
                logger.info("Could not load %s (%s)", TRANSFORMER_MODEL, exc.__class__.__name__)
                self._transformer_failed = True
        return self._transformer
