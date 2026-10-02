"""Named entity extraction — spaCy en_core_web_sm with regex fallback.

Output shape (kept stable for analytics consumers):

    EntityExtractor().extract(texts) -> {
        "entities":     [{"text": str, "label": str, "count": n}, ...] top 15,
        "entity_count": distinct entities found,
        "backend":      "spacy" | "regex",
    }

The regex fallback surfaces @handles, #hashtags and Capitalized multi-word
sequences so the pipeline never depends on the spaCy model being installed.
spaCy is lazy-loaded once per process; failures degrade quietly.
"""

import logging
import re
from collections import Counter
from typing import Any

logger = logging.getLogger(__name__)

_KEEP_LABELS = {"PERSON", "ORG", "GPE", "LOC", "PRODUCT", "EVENT", "NORP", "WORK_OF_ART"}


class EntityExtractor:
    def __init__(self) -> None:
        self._nlp = None
        self._spacy_failed = False

    def _get_nlp(self):
        if self._nlp is None and not self._spacy_failed:
            try:
                import spacy

                self._nlp = spacy.load("en_core_web_sm", disable=["parser", "lemmatizer"])
            except Exception as exc:
                logger.info("spaCy model unavailable (%s) — using regex entity fallback", exc.__class__.__name__)
                self._spacy_failed = True
        return self._nlp

    def extract(self, texts: list[str], limit: int = 15) -> dict[str, Any]:
        if not texts:
            return {"entities": [], "entity_count": 0, "backend": "regex"}

        nlp = self._get_nlp()
        if nlp is not None:
            return self._extract_spacy(nlp, texts, limit)
        return self._extract_regex(texts, limit)

    # -- spaCy backend --------------------------------------------------------

    def _extract_spacy(self, nlp, texts: list[str], limit: int) -> dict[str, Any]:
        counts: Counter = Counter()
        labels: dict[str, str] = {}
        # Batch for throughput; cap each doc so a pasted essay cannot stall NER
        for doc in nlp.pipe([str(t)[:2000] for t in texts], batch_size=32):
            for ent in doc.ents:
                if ent.label_ not in _KEEP_LABELS:
                    continue
                text = ent.text.strip()
                if len(text) < 2 or len(text) > 60:
                    continue
                key = text.lower()
                counts[key] += 1
                labels.setdefault(key, text)
                labels.setdefault(f"label::{key}", ent.label_)
        return self._finalize(counts, labels, limit, backend="spacy")

    # -- regex fallback ---------------------------------------------------------

    def _extract_regex(self, texts: list[str], limit: int) -> dict[str, Any]:
        counts: Counter = Counter()
        labels: dict[str, str] = {}
        joined = "\n".join(str(t) for t in texts)

        for handle in re.findall(r"@[A-Za-z0-9_]{2,30}", joined):
            key = handle.lower()
            counts[key] += 1
            labels[key] = handle
        for hashtag in re.findall(r"#\w{2,40}", joined):
            key = hashtag.lower()
            counts[key] += 1
            labels[key] = hashtag
        # Capitalized multi-word sequences (naive ORG/PERSON proxy)
        for phrase in re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})\b", joined):
            if len(phrase) < 4:
                continue
            key = phrase.lower()
            counts[key] += 1
            labels[key] = phrase

        return self._finalize(counts, labels, limit, backend="regex")

    # -- shared -------------------------------------------------------------------

    @staticmethod
    def _finalize(counts: Counter, labels: dict[str, str], limit: int, backend: str) -> dict[str, Any]:
        # Deterministic order (count desc, then text asc) so repeated runs and
        # different hash seeds produce identical output.
        ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
        entities = [
            {"text": labels[key], "label": labels.get(f"label::{key}", "ENTITY"), "count": count}
            for key, count in ranked[:limit]
        ]
        return {"entities": entities, "entity_count": len(counts), "backend": backend}
