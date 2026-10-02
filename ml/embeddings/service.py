"""Semantic embeddings - sentence-transformers MiniLM, lazily loaded.

The model is a process-wide singleton loaded on first use (a few seconds,
once) and L2-normalized so cosine similarity is a plain dot product. Every
failure path degrades quietly: when the model or its weights are unavailable
the service reports ``available() == False`` and callers skip semantic work
rather than fabricating similarity numbers.
"""

import hashlib
import logging
import math
from functools import lru_cache
from typing import Any, Optional

from backend.config import get_settings

logger = logging.getLogger(__name__)


def record_hash(text: str) -> str:
    """Stable content hash used as the idempotent upsert key for embeddings."""
    normalized = " ".join(str(text).lower().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class EmbeddingService:
    def __init__(self, model_name: Optional[str] = None) -> None:
        self.model_name = model_name or get_settings().embedding_model
        self._model = None
        self._failed = False

    def _get_model(self):
        if self._model is None and not self._failed:
            try:
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer(self.model_name)
                logger.info("Embedding model ready: %s", self.model_name)
            except Exception as exc:
                logger.info(
                    "Embedding model %s unavailable (%s) - semantic features disabled",
                    self.model_name,
                    exc.__class__.__name__,
                )
                self._failed = True
        return self._model

    def available(self) -> bool:
        return self._get_model() is not None

    @property
    def dimension(self) -> int:
        model = self._get_model()
        if model is None:
            return 0
        try:
            return int(model.get_sentence_embedding_dimension())
        except Exception:
            return 0


    def encode(self, texts: list[str]) -> Optional[list[list[float]]]:
        """L2-normalized embeddings for ``texts`` (None when unavailable)."""
        cleaned = [str(t)[:1000] for t in texts if str(t).strip()]
        if not cleaned:
            return []
        model = self._get_model()
        if model is None:
            return None
        try:
            vectors = model.encode(cleaned, normalize_embeddings=True, show_progress_bar=False)
            return [[float(value) for value in vector] for vector in vectors]
        except Exception as exc:
            logger.info("Embedding encode failed (%s)", exc.__class__.__name__)
            return None

    def encode_one(self, text: str) -> Optional[list[float]]:
        vectors = self.encode([text])
        return vectors[0] if vectors else None

    @staticmethod
    def cosine_similarity(left: list[float], right: list[float]) -> float:
        """Cosine similarity of two vectors (1.0 identical, 0.0 orthogonal)."""
        if not left or not right or len(left) != len(right):
            return 0.0
        dot = sum(a * b for a, b in zip(left, right))
        norm_left = math.sqrt(sum(a * a for a in left))
        norm_right = math.sqrt(sum(b * b for b in right))
        if not norm_left or not norm_right:
            return 0.0
        return max(-1.0, min(1.0, dot / (norm_left * norm_right)))


@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()
