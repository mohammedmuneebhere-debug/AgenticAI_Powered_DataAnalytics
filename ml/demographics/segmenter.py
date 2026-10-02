"""Aggregate audience segmentation from REAL author metadata.

Replaces the dormant static-segments stub. Segments are derived strictly from
data the X/Apify actors provide per author (followers, verified, bio,
location) — no invented demographics:

* Follower tiers (nano <10k, micro 10k-50k, mid 50k-500k, macro 500k+) with
  each author counted exactly once.
* Verified-account share.
* Top locations from explicit author.location plus spaCy GPE/LOC entities
  extracted from author bios (regex handles without spaCy).

Output shape (consumed by frontend/lib/adapter.ts -> audienceSegments):

    {
      "segments":     [{"label", "percentage", "confidence", "description"}],
      "methodology":  str,
      "disclaimer":   str,
      "coverage":     {"authors_with_metadata": n, "total_records": n,
                       "verified_share_pct": float, "top_locations": [...]},
    }

With zero author metadata the segments list is empty (the frontend falls back
to the interim Google Trends audience signal) — never fabricated numbers.
"""

import logging
import re
from collections import Counter
from typing import Any

logger = logging.getLogger(__name__)

FOLLOWER_TIERS = [
    ("Nano (<10K followers)", 0, 10_000),
    ("Micro (10K-50K)", 10_000, 50_000),
    ("Mid (50K-500K)", 50_000, 500_000),
    ("Macro (500K+)", 500_000, float("inf")),
]


class DemographicSegmenter:
    """Uses public signals for aggregate audience segments — not individual facts."""

    def __init__(self) -> None:
        self._entity_extractor = None

    def _extractor(self):
        if self._entity_extractor is None:
            from ml.entities.extractor import EntityExtractor

            self._entity_extractor = EntityExtractor()
        return self._entity_extractor

    def segment(self, records: list[dict]) -> dict[str, Any]:
        total = len(records)
        metas = [
            (str(r.get("author", "unknown")), r.get("author_meta") or {})
            for r in records
            if isinstance(r.get("author_meta"), dict) and r.get("author_meta")
        ]

        if not metas:
            return {
                "segments": [],
                "methodology": "No author metadata in this dataset (followers/bio/location unavailable).",
                "disclaimer": "Segments would be probabilistic aggregates from public signals only.",
                "coverage": {
                    "authors_with_metadata": 0,
                    "total_records": total,
                    "verified_share_pct": 0.0,
                    "top_locations": [],
                },
            }

        # One row per distinct author (a loud author must not skew the tiers)
        author_map: dict[str, dict] = {}
        for author, meta in metas:
            existing = author_map.setdefault(author, {})
            for key, value in meta.items():
                if value is not None and (key not in existing or existing[key] in (None, "")):
                    existing[key] = value

        authors = list(author_map.items())
        n = len(authors)

        # -- follower tiers -----------------------------------------------------
        tier_counts: Counter = Counter()
        verified = 0
        locations: Counter = Counter()
        bio_texts: list[str] = []

        for _, meta in authors:
            followers = meta.get("followers")
            if isinstance(followers, (int, float)) and followers >= 0:
                for label, low, high in FOLLOWER_TIERS:
                    if low <= followers < high:
                        tier_counts[label] += 1
                        break
            if meta.get("verified"):
                verified += 1
            if meta.get("location"):
                locations[str(meta["location"]).strip()] += 1
            if meta.get("bio"):
                bio_texts.append(str(meta["bio"]))

        segments: list[dict[str, Any]] = []
        for label, _, _ in FOLLOWER_TIERS:
            count = tier_counts.get(label, 0)
            if count == 0:
                continue
            confidence = min(0.9, round(0.45 + 0.11 * (count ** 0.5), 2))
            segments.append({
                "label": label,
                "percentage": round(count / n * 100, 1),
                "confidence": confidence,
                "description": f"{count} of {n} unique authors",
            })

        # -- locations: explicit fields + NER over bios -------------------------
        if bio_texts:
            try:
                extracted = self._extractor().extract(bio_texts, limit=10)
                for entity in extracted.get("entities", []):
                    if entity.get("label") in ("GPE", "LOC"):
                        locations[entity["text"]] += entity.get("count", 1)
            except Exception as exc:
                logger.info("Bio NER failed (%s) — using explicit locations only", exc.__class__.__name__)

        top_locations = [
            {"location": loc, "authors": count}
            for loc, count in locations.most_common(5)
        ]

        return {
            "segments": segments,
            "methodology": (
                f"Aggregate follower-tier, verified-status and location analysis over "
                f"{n} unique authors with public profile metadata."
            ),
            "disclaimer": "Segments are probabilistic aggregates from public profile signals, not verified individual attributes.",
            "coverage": {
                "authors_with_metadata": n,
                "total_records": total,
                "verified_share_pct": round(verified / n * 100, 1) if n else 0.0,
                "top_locations": top_locations,
            },
        }
