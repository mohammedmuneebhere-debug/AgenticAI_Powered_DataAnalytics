"""Topic detection via keyword clustering (BERTopic-ready interface)."""

from typing import Any
from collections import Counter
import re


class TopicDetector:
    STOPWORDS = {"the", "a", "is", "are", "and", "or", "to", "in", "for", "of", "this", "that", "with"}

    def detect(self, texts: list[str]) -> dict[str, Any]:
        words = []
        for text in texts:
            tokens = re.findall(r"\b[a-z]{3,}\b", text.lower())
            words.extend(t for t in tokens if t not in self.STOPWORDS)

        counter = Counter(words)
        topics = [{"term": w, "count": c} for w, c in counter.most_common(10)]

        return {"topics": topics, "topic_count": len(topics)}
