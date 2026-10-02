"""Evidence & Correlation Engine - combines multi-dimensional signals.

Phase 4 adds semantic layers on top of the statistical evidence:

* **near-duplicate collapse** - signals that say the same thing in different
  words (or exact re-posts) are folded into one cluster, so the insight is
  not double-counted;
* **cross-source clustering** - a cluster containing the same story from two
  or more platforms becomes corroboration evidence, which is the strongest
  signal this product can produce;
* **cosine evidence links** - each cluster is reported with its similarity.

Semantic work is strictly optional: when the embedding model is unavailable
the engine returns the same statistical evidence it always did.
"""

from typing import Any, Optional

# Calibrated against all-MiniLM-L6-v2 cosine bands measured on real
# paraphrases: restatements of one fact score 0.90+, the same topic with a
# different fact (US vs EU installs) sits at 0.60-0.70, and unrelated posts
# land near 0.0-0.15. 0.85 sits inside the gap, so only genuine restatements
# of the same signal collapse.
NEAR_DUPLICATE_THRESHOLD = 0.85
MAX_EMBEDDED_RECORDS = 60


class EvidenceCorrelationEngine:
    """Safeguard against unsupported LLM explanations by structuring evidence."""

    def semantic_links(self, records: Optional[list[dict]]) -> dict[str, Any]:
        """Cluster records by embedding similarity.

        Returns a summary dict; ``available`` is False when embeddings are
        unavailable, in which case no semantic claims are made.
        """
        summary: dict[str, Any] = {
            "available": False,
            "clustered": 0,
            "unique": 0,
            "duplicates_collapsed": 0,
            "cross_source_clusters": [],
            "backend": None,
        }
        texts = [
            (str(record.get("text") or record.get("title") or "").strip(), str(record.get("platform") or "unknown"))
            for record in (records or [])
        ]
        texts = [(text, platform) for text, platform in texts if len(text) > 20][:MAX_EMBEDDED_RECORDS]
        if len(texts) < 2:
            return summary

        from ml.embeddings.service import get_embedding_service

        service = get_embedding_service()
        vectors = service.encode([text for text, _ in texts])
        if not vectors:
            return summary

        # Each cluster keeps its member vectors so the centroid stays a true
        # mean of the cluster, not of its labels.
        clusters: list[dict[str, Any]] = []
        for (text, platform), vector in zip(texts, vectors):
            best_index, best_score = -1, 0.0
            for index, cluster in enumerate(clusters):
                score = service.cosine_similarity(vector, cluster["centroid"])
                if score > best_score:
                    best_index, best_score = index, score
            if best_index >= 0 and best_score >= NEAR_DUPLICATE_THRESHOLD:
                cluster = clusters[best_index]
                cluster["members"].append((text, platform, vector))
                count = len(cluster["members"])
                cluster["centroid"] = [
                    sum(member[2][index] for member in cluster["members"]) / count
                    for index in range(len(vector))
                ]
                # Report the weakest link, not the best match: a cluster is
                # only as tight as its loosest member.
                cluster["similarity"] = round(min(cluster["similarity"], best_score), 3)
            else:
                clusters.append(
                    {
                        "centroid": list(vector),
                        "members": [(text, platform, vector)],
                        "similarity": 1.0,
                    }
                )

        cross_source = []
        for cluster in clusters:
            platforms = sorted({member[1] for member in cluster["members"]})
            if len(platforms) >= 2:
                cross_source.append(
                    {
                        "platforms": platforms,
                        "signals": len(cluster["members"]),
                        "similarity": cluster["similarity"],
                        "example": cluster["members"][0][0][:160],
                    }
                )
        cross_source.sort(key=lambda item: (-item["signals"], -item["similarity"]))

        summary.update(
            {
                "available": True,
                "clustered": len(texts),
                "unique": len(clusters),
                "duplicates_collapsed": len(texts) - len(clusters),
                "cross_source_clusters": cross_source[:5],
                "backend": service.model_name,
            }
        )
        return summary

    def correlate(
        self,
        social_analytics: dict[str, Any],
        domain_analytics: dict[str, Any],
        query: str,
        records: Optional[list[dict]] = None,
    ) -> list[dict]:
        evidence = []

        sentiment = social_analytics.get("sentiment", {})
        if sentiment:
            evidence.append({
                "type": "statistical",
                "label": "Overall Sentiment",
                "value": sentiment.get("overall_label", "neutral"),
                "confidence": sentiment.get("confidence", 0.7),
                "source": "sentiment_model",
            })

        trends = social_analytics.get("trends", {})
        for trend in trends.get("top_trends", [])[:3]:
            evidence.append({
                "type": "semantic",
                "label": f"Trend: {trend['topic']}",
                "value": f"velocity={trend['velocity']:.2f}",
                "confidence": trend.get("confidence", 0.75),
                "source": "trend_detector",
            })

        # Regional interest from real Google Trends data (replaces the removed
        # fake demographic segmenter as the audience/geography signal).
        google_trends = social_analytics.get("google_trends", {})
        for region in google_trends.get("interest_by_region", [])[:2]:
            evidence.append({
                "type": "regional",
                "label": f"Search interest: {region.get('location', 'unknown')}",
                "value": str(region.get("value", 0)),
                "confidence": 0.9,
                "source": "google_trends",
            })

        network = social_analytics.get("network", {})
        if network.get("top_influencers"):
            evidence.append({
                "type": "network",
                "label": "Top Influencer",
                "value": network["top_influencers"][0],
                "confidence": 0.7,
                "source": "graph_analyzer",
            })

        if domain_analytics.get("product_opportunities"):
            top = domain_analytics["product_opportunities"][0]
            evidence.append({
                "type": "domain",
                "label": "Product Opportunity",
                "value": top["product"],
                "confidence": top.get("score", 0.7),
                "source": "domain_analytics",
            })

        if domain_analytics.get("volatility"):
            evidence.append({
                "type": "temporal",
                "label": "Volatility Level",
                "value": domain_analytics["volatility"]["level"],
                "confidence": 0.8,
                "source": "market_analytics",
            })

        # ── Semantic layers (Phase 4) ────────────────────────────
        semantic = self.semantic_links(records)
        if semantic.get("available") and semantic["clustered"] >= 2:
            collapsed = semantic["duplicates_collapsed"]
            if collapsed:
                evidence.append({
                    "type": "deduplication",
                    "label": "Duplicate signals collapsed",
                    "value": f"{semantic['clustered']} signals -> {semantic['unique']} unique "
                             f"({collapsed} near-duplicates)",
                    "confidence": round(min(0.9, 0.6 + collapsed * 0.05), 2),
                    "source": "embedding_cluster",
                })
            for cluster in semantic["cross_source_clusters"][:2]:
                evidence.append({
                    "type": "cross_source",
                    "label": f"Corroborated across {len(cluster['platforms'])} sources",
                    "value": " + ".join(cluster["platforms"])
                             + f" ({cluster['signals']} signals, cosine {cluster['similarity']})",
                    "confidence": round(min(0.95, 0.7 + 0.05 * cluster["signals"]), 2),
                    "source": "embedding_cluster",
                })

        return evidence
