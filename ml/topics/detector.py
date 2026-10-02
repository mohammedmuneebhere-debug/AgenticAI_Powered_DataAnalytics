"""Topic detection — spaCy-lemmatized keyword clusters (BERTopic-ready interface).

spaCy (en_core_web_sm) groups inflections ("running"/"runs" -> "run") and
drops stopwords/punct properly; a regex fallback keeps the module dependency-
optional. Output shape (unchanged, plus a `backend` note):

    {"topics": [{"term": str, "count": n}], "topic_count": n, "backend": str}
"""

import re
from collections import Counter
from typing import Any


class TopicDetector:
    STOPWORDS = {
        "the", "a", "is", "are", "and", "or", "to", "in", "for", "of", "this",
        "that", "with", "it", "its", "as", "at", "be", "by", "an", "on", "from",
        "was", "were", "will", "has", "have", "had", "not", "but", "they",
        "their", "them", "you", "your", "we", "our", "can", "just", "about",
    }

    def __init__(self) -> None:
        self._nlp = None
        self._spacy_failed = False

    def _get_nlp(self):
        if self._nlp is None and not self._spacy_failed:
            try:
                import spacy

                self._nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])
            except Exception:
                self._spacy_failed = True
        return self._nlp

    def detect(self, texts: list[str]) -> dict[str, Any]:
        if not texts:
            return {"topics": [], "topic_count": 0, "backend": "regex"}

        nlp = self._get_nlp()
        if nlp is not None:
            return self._detect_spacy(nlp, texts)
        return self._detect_regex(texts)

    def _detect_spacy(self, nlp, texts: list[str]) -> dict[str, Any]:
        counter: Counter = Counter()
        for doc in nlp.pipe([str(t)[:1500] for t in texts], batch_size=32):
            for token in doc:
                if token.is_stop or token.is_punct or token.is_space:
                    continue
                if token.pos_ not in ("NOUN", "PROPN", "ADJ"):
                    continue
                lemma = token.lemma_.lower().strip()
                if len(lemma) < 3 or lemma in self.STOPWORDS or lemma.isdigit():
                    continue
                counter[lemma] += 1
        topics = [{"term": w, "count": c} for w, c in counter.most_common(10)]
        return {"topics": topics, "topic_count": len(topics), "backend": "spacy"}

    def _detect_regex(self, texts: list[str]) -> dict[str, Any]:
        words = []
        for text in texts:
            tokens = re.findall(r"\b[a-z]{3,}\b", text.lower())
            words.extend(t for t in tokens if t not in self.STOPWORDS)

        counter = Counter(words)
        topics = [{"term": w, "count": c} for w, c in counter.most_common(10)]
        return {"topics": topics, "topic_count": len(topics), "backend": "regex"}
