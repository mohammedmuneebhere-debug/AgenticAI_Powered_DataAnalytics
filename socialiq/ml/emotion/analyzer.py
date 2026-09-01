"""Emotion classification — excitement, anxiety, support, etc."""

from typing import Any
import re

EMOTION_PATTERNS = {
    "excitement": [r"!\s*$", r"amazing", r"love", r"can't wait", r"bullish"],
    "anxiety": [r"worried", r"fear", r"uncertain", r"volatile", r"crash"],
    "support": [r"support", r"behind", r"team", r"hodl"],
    "frustration": [r"frustrated", r"annoyed", r"overpriced", r"scam"],
}


class EmotionAnalyzer:
    def analyze_batch(self, texts: list[str]) -> dict[str, Any]:
        counts = {e: 0 for e in EMOTION_PATTERNS}
        for text in texts:
            for emotion, patterns in EMOTION_PATTERNS.items():
                if any(re.search(p, text.lower()) for p in patterns):
                    counts[emotion] += 1

        dominant = max(counts, key=counts.get) if texts else "neutral"
        return {"dominant_emotion": dominant, "distribution": counts, "confidence": 0.65}
