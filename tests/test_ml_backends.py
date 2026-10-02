"""Phase 2 ML backend tests — real implementations, graceful fallbacks.

The transformer backend is forced to fail (no model download in tests) to
prove the VADER fallback path; VADER and spaCy are real local dependencies.
"""

import pytest

from ml.sentiment.analyzer import SentimentAnalyzer
from ml.topics.detector import TopicDetector
from ml.trends.detector import TrendDetector
from ml.entities.extractor import EntityExtractor
from ml.demographics.segmenter import DemographicSegmenter


class TestSentiment:
    def test_vader_shape_and_range(self):
        result = SentimentAnalyzer("vader").analyze_batch(
            ["I love this amazing product!", "This is terrible and I hate it", "The meeting is at 3pm"]
        )
        assert set(["overall_label", "average_score", "confidence", "distribution", "scores"]) <= set(result)
        assert all(0.0 <= s <= 1.0 for s in result["scores"])
        total = result["distribution"]["positive"] + result["distribution"]["negative"] + result["distribution"]["neutral"]
        assert total == 3

    def test_vader_polarity_direction(self):
        analyzer = SentimentAnalyzer("vader")
        positive = analyzer.analyze_batch(["I absolutely love this, wonderful and exciting"])
        negative = analyzer.analyze_batch(["I hate this, awful and disappointing"])
        assert positive["average_score"] > negative["average_score"]
        assert positive["overall_label"] in ("positive", "neutral")
        assert negative["overall_label"] in ("negative", "neutral")

    def test_empty_batch(self):
        assert SentimentAnalyzer("vader").analyze_batch([])["overall_label"] == "neutral"

    def test_transformer_falls_back_to_vader_without_model(self):
        analyzer = SentimentAnalyzer("transformer")
        # Force the lazy transformer load to fail (no network/model in tests)
        analyzer._transformer_failed = True
        result = analyzer.analyze_batch(["I love this"])
        vader = SentimentAnalyzer("vader").analyze_batch(["I love this"])
        assert result["scores"] == vader["scores"]
        assert result["backend"] == "transformer"  # requested backend is reported


class TestEntities:
    def test_regex_fallback_handles_and_hashtags(self):
        extractor = EntityExtractor()
        extractor._spacy_failed = True  # force fallback path
        result = extractor.extract(["@OpenAI released GPT-5 says @elonmusk #AI #agents"])
        texts = [e["text"].lower() for e in result["entities"]]
        assert "@openai" in texts and "#ai" in texts
        assert result["backend"] == "regex"

    def test_spacy_backend_when_available(self):
        extractor = EntityExtractor()
        if extractor._get_nlp() is None:
            pytest.skip("spaCy model not available")
        result = extractor.extract(["Tim Cook announced Apple earnings in Cupertino yesterday"])
        assert result["backend"] == "spacy"
        texts = {e["text"] for e in result["entities"]}
        assert any("Apple" in t or "Tim Cook" in t for t in texts)

    def test_empty_texts(self):
        assert EntityExtractor().extract([])["entity_count"] == 0


class TestTrends:
    def _records_with_history(self):
        # Term "solar" accelerates on the last day; "wind" stays flat
        records = []
        for day in range(1, 6):
            count = 1 if day < 5 else 10
            for i in range(count):
                records.append({
                    "text": f"solar energy update {i}",
                    "timestamp": f"2026-09-{20 + day - 1}T10:00:00+00:00",
                    "engagement": {"likes": 5, "reposts": 2},
                })
            for i in range(2):
                records.append({
                    "text": f"wind energy update {i}",
                    "timestamp": f"2026-09-{20 + day - 1}T10:00:00+00:00",
                    "engagement": {"likes": 3, "reposts": 1},
                })
        return records

    def test_velocity_zscore_method(self):
        result = TrendDetector().detect(self._records_with_history())
        assert result["method"] == "velocity_zscore"
        assert result["trend_count"] >= 2
        by_topic = {t["topic"]: t for t in result["top_trends"]}
        assert "solar" in by_topic
        assert by_topic["solar"]["z_score"] > 0
        # "solar" accelerated on the last day; "wind" stayed flat
        assert by_topic["solar"]["velocity"] > by_topic.get("wind", {}).get("velocity", 0)

    def test_no_hardcoded_keywords(self):
        # The old TREND_KEYWORDS (cold brew, btc etf) must not invent trends
        # that are absent from the dataset.
        result = TrendDetector().detect(self._records_with_history())
        topics = {t["topic"] for t in result["top_trends"]}
        assert "cold brew" not in topics and "btc etf" not in topics

    def test_frequency_fallback_without_timestamps(self):
        records = [
            {"text": "solar panels are great", "engagement": {"likes": 10}},
            {"text": "more solar panels talk", "engagement": {"likes": 5}},
            {"text": "solar surge continues", "engagement": {"likes": 2}},
            {"text": "wind turbines also exist", "engagement": {"likes": 1}},
        ]
        result = TrendDetector().detect(records)
        assert result["method"] == "frequency"
        # "solar" is in 3 of 4 records -> unambiguous top trend
        assert result["top_trends"][0]["topic"] == "solar"
        assert result["top_trends"][0]["mentions"] == 3

    def test_ties_break_deterministically(self):
        # solar/panels appear in identical records: equal mentions and
        # engagement, so the ranking must fall back to a stable rule
        # (alphabetical) rather than set/hash iteration order.
        records = [
            {"text": "solar panels", "engagement": {"likes": 5}},
            {"text": "panels solar", "engagement": {"likes": 5}},
        ]
        result = TrendDetector().detect(records)
        topics = [t["topic"] for t in result["top_trends"][:2]]
        assert topics == ["panels", "solar"]
        # Repeat runs must agree exactly
        assert [t["topic"] for t in TrendDetector().detect(records)["top_trends"]] == [
            t["topic"] for t in result["top_trends"]
        ]

    def test_forecast_disabled_by_default(self):
        result = TrendDetector().detect(self._records_with_history())
        assert result["forecast"] is None


class TestTopics:
    def test_shape_and_stopwords(self):
        result = TopicDetector().detect(["Solar energy is booming", "Solar panels everywhere", "the the the"])
        assert "topics" in result and "topic_count" in result
        terms = {t["term"] for t in result["topics"]}
        assert "the" not in terms
        assert any("solar" in t for t in terms)

    def test_empty(self):
        assert TopicDetector().detect([])["topic_count"] == 0


class TestDemographics:
    def test_real_segments_from_author_metadata(self):
        records = [
            {"text": "post one", "author": "@a", "author_meta": {"followers": 5000, "verified": False, "location": "New York, USA", "bio": "Coffee lover from Seattle"}},
            {"text": "post two", "author": "@b", "author_meta": {"followers": 30000, "verified": True, "location": "London, UK"}},
            {"text": "post three", "author": "@c", "author_meta": {"followers": 120000, "verified": False, "bio": "Tech journalist in Berlin"}},
            {"text": "post four", "author": "@d", "author_meta": {"followers": 900000, "verified": True}},
            {"text": "post five", "author": "@a", "author_meta": {"followers": 5000}},  # duplicate author counts once
        ]
        result = DemographicSegmenter().segment(records)
        assert len(result["segments"]) >= 3
        assert result["coverage"]["authors_with_metadata"] == 4
        assert result["coverage"]["verified_share_pct"] == 50.0
        # Percentages sum to ~100 across tiers
        total_pct = sum(s["percentage"] for s in result["segments"])
        assert 99.0 <= total_pct <= 101.0
        locations = [loc["location"] for loc in result["coverage"]["top_locations"]]
        assert any("new york" in loc.lower() for loc in locations)

    def test_no_metadata_no_fabrication(self):
        result = DemographicSegmenter().segment([{"text": "no meta here", "author": "@x"}])
        assert result["segments"] == []
        assert result["coverage"]["authors_with_metadata"] == 0

    def test_static_stub_segments_gone(self):
        # The old dormant stub returned invented 18-34 Urban segments; ensure
        # fabricated segments can no longer appear without metadata.
        result = DemographicSegmenter().segment([])
        assert result["segments"] == []
        assert "18-34 Urban" not in [s.get("label") for s in result["segments"]]
