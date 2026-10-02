"""Phase 4 tests - embeddings, semantic correlation, pgvector similarity.

Model-dependent and database-dependent tests skip cleanly when the MiniLM
weights or PostgreSQL are unavailable, so the suite stays green on a bare
checkout.
"""

import uuid

import pytest

from ml.embeddings.service import EmbeddingService, get_embedding_service, record_hash
from ml.correlation import EvidenceCorrelationEngine


def _model_available() -> bool:
    try:
        return get_embedding_service().available()
    except Exception:
        return False


def _pg_up() -> bool:
    try:
        from backend.db.session import ping

        return ping()
    except Exception:
        return False


needs_model = pytest.mark.skipif(not _model_available(), reason="MiniLM model unavailable")
needs_pg = pytest.mark.skipif(not _pg_up(), reason="PostgreSQL not available")


RECORDS = [
    {"platform": "x", "text": "Solar panel installs hit a record high this quarter in the US market"},
    {"platform": "news", "text": "US solar panel installs hit a record high quarter, analysts say demand is strong"},
    {"platform": "reddit", "text": "My pasta recipe needs fresh basil and good olive oil, never dried herbs"},
    {"platform": "x", "text": "Wildlife photographers spot rare birds in the coastal wetlands this spring"},
]


def _delete_hashes(hashes):
    """Remove test rows so runs do not leak state into the shared database."""
    try:
        from sqlalchemy import delete

        from backend.db.models import RecordEmbeddingModel
        from backend.db.session import session_scope

        with session_scope() as db:
            db.execute(delete(RecordEmbeddingModel).where(RecordEmbeddingModel.record_hash.in_(hashes)))
    except Exception:
        pass


class TestEmbeddingService:
    def test_record_hash_is_stable_and_normalized(self):
        assert record_hash("Solar  Panel Rises") == record_hash("solar panel rises")
        assert record_hash("a") != record_hash("b")
        assert len(record_hash("anything")) == 64

    def test_cosine_math(self):
        service = EmbeddingService("unused-model")
        assert service.cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0
        assert service.cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0
        assert service.cosine_similarity([1.0, 0.0], [2.0, 0.0]) == 1.0  # scale invariant
        assert service.cosine_similarity([1.0, 0.0], [1.0]) == 0.0  # dim mismatch
        assert service.cosine_similarity([], [1.0]) == 0.0

    def test_encode_degrades_when_model_unavailable(self):
        service = EmbeddingService("definitely-not-a-real-model-name")
        service._failed = True  # simulate an unavailable model
        assert service.encode(["some text"]) is None
        assert service.available() is False

    def test_encode_empty_list(self):
        service = EmbeddingService("unused-model")
        service._failed = True
        assert service.encode([]) == []


@needs_model
class TestSemanticLinks:
    def test_near_duplicates_collapse(self):
        summary = EvidenceCorrelationEngine().semantic_links(RECORDS)
        assert summary["available"] is True
        assert summary["clustered"] == 4
        # the two US-solar restatements collapse into one cluster
        assert summary["unique"] == 3
        assert summary["duplicates_collapsed"] == 1
        assert summary["backend"] == "all-MiniLM-L6-v2"

    def test_cross_source_corroboration_detected(self):
        summary = EvidenceCorrelationEngine().semantic_links(RECORDS)
        platforms = [c["platforms"] for c in summary["cross_source_clusters"]]
        assert ["news", "x"] in platforms
        cluster = summary["cross_source_clusters"][0]
        # similarity is the weakest link in the cluster, not 1.0
        assert 0.5 < cluster["similarity"] < 1.0

    def test_evidence_includes_semantic_layers(self):
        evidence = EvidenceCorrelationEngine().correlate({}, {}, "solar", records=RECORDS)
        types = [item["type"] for item in evidence]
        assert "deduplication" in types and "cross_source" in types

    def test_no_fabrication_without_embeddings(self, monkeypatch):
        service = get_embedding_service()
        monkeypatch.setattr(service, "encode", lambda texts: None, raising=False)
        summary = EvidenceCorrelationEngine().semantic_links(RECORDS)
        assert summary["available"] is False
        evidence = EvidenceCorrelationEngine().correlate({}, {}, "solar", records=RECORDS)
        assert [item for item in evidence if item["source"] == "embedding_cluster"] == []

    def test_short_input_is_ignored(self):
        summary = EvidenceCorrelationEngine().semantic_links([{"text": "ok", "platform": "x"}])
        assert summary["available"] is False

@needs_pg
@needs_model
class TestPgVectorRepository:
    # Content hashes are the upsert key, so a fixed corpus would already exist
    # in the database on the second run. Unique text per run keeps the count
    # assertions exact; teardown removes what the test inserted.
    RUN = uuid.uuid4().hex[:8]
    TEXTS = [
        f"[{RUN}] Solar panel installs hit a record high this quarter in the US market",
        f"[{RUN}] US solar panel installs hit a record high quarter, analysts say demand is strong",
        f"[{RUN}] The best pasta recipe uses fresh basil and good olive oil",
        f"[{RUN}] Wildlife photographers spot rare birds in the coastal wetlands",
    ]

    @pytest.fixture(autouse=True)
    def _cleanup(self):
        yield
        _delete_hashes([record_hash(text) for text in self.TEXTS])

    def _entries(self):
        service = get_embedding_service()
        vectors = service.encode(self.TEXTS)
        return [
            {
                "record_hash": record_hash(text),
                "content": text,
                "vector": vector,
                "metadata": {"platform": "x", "run": uuid.uuid4().hex[:8]},
            }
            for text, vector in zip(self.TEXTS, vectors)
        ]

    def test_upsert_is_idempotent(self):
        from backend.db.repository import embedding_stats, upsert_record_embeddings

        entries = self._entries()
        before = embedding_stats()["count"]
        assert upsert_record_embeddings(entries) == 4
        after_first = embedding_stats()["count"]
        assert upsert_record_embeddings(entries) == 4
        assert embedding_stats()["count"] == after_first
        assert after_first == before + 4

    def test_similar_records_ranked_and_filtered(self):
        from backend.db.repository import similar_records, upsert_record_embeddings

        upsert_record_embeddings(self._entries())
        matches = similar_records(record_hash(self.TEXTS[0]), limit=25, min_similarity=0.0)
        assert matches, "expected at least one nearest neighbour"
        by_content = {m["content"]: m["similarity"] for m in matches}

        # The restatement of the same fact must rank above unrelated content.
        # (Ranking is asserted relatively: this is a shared database, so other
        # near-duplicate rows may legitimately sit at the very top.)
        assert self.TEXTS[1] in by_content, "restatement should be a neighbour"
        assert by_content[self.TEXTS[1]] > by_content.get(self.TEXTS[3], -1.0)
        assert by_content[self.TEXTS[1]] > 0.8

        similarities = [m["similarity"] for m in matches]
        assert similarities == sorted(similarities, reverse=True)

        # Unrelated content stays below the default floor of 0.3.
        assert by_content.get(self.TEXTS[3], 0.0) < 0.3

    def test_get_embedding_record(self):
        from backend.db.repository import get_embedding_record, upsert_record_embeddings

        upsert_record_embeddings(self._entries())
        record = get_embedding_record(record_hash(self.TEXTS[0]))
        assert record["content"] == self.TEXTS[0]
        assert record["metadata"]["platform"] == "x"
        assert get_embedding_record("0" * 64) is None

    def test_similar_records_unknown_hash_is_empty(self):
        from backend.db.repository import similar_records

        assert similar_records("f" * 64) == []


@needs_pg
@needs_model
class TestSimilarRecordsEndpoint:
    def test_endpoint_returns_matches(self, client, auth_headers):
        from backend.db.repository import upsert_record_embeddings
        from ml.embeddings.service import get_embedding_service, record_hash

        run = uuid.uuid4().hex[:8]
        texts = [
            f"[{run}] Endpoint test: solar panel installs hit a record high this quarter",
            f"[{run}] Endpoint test: US solar panel installs hit a record high quarter",
            f"[{run}] Endpoint test: an unrelated note about birdwatching in the wetlands",
        ]
        vectors = get_embedding_service().encode(texts)
        upsert_record_embeddings(
            [
                {"record_hash": record_hash(t), "content": t, "vector": v, "metadata": {}}
                for t, v in zip(texts, vectors)
            ]
        )

        try:
            response = client.get(
                f"/api/v1/records/{record_hash(texts[0])}/similar?limit=3", headers=auth_headers
            )
        finally:
            _delete_hashes([record_hash(text) for text in texts])
        assert response.status_code == 200
        payload = response.json()
        assert payload["record_hash"] == record_hash(texts[0])
        assert payload["count"] == len(payload["matches"])
        assert payload["matches"][0]["record_hash"] == record_hash(texts[1])

    def test_endpoint_unknown_hash_is_404(self, client, auth_headers):
        response = client.get("/api/v1/records/" + "e" * 64 + "/similar", headers=auth_headers)
        assert response.status_code == 404
