"""Graph analytics — influence, communities, propagation."""

from typing import Any
from collections import defaultdict


class GraphAnalyzer:
    """Network intelligence from social interaction patterns."""

    def analyze(self, records: list[dict]) -> dict[str, Any]:
        nodes = {}
        edges = []
        interactions = defaultdict(int)

        for record in records:
            author = record.get("author", "unknown")
            if author not in nodes:
                engagement = record.get("engagement", {})
                nodes[author] = {
                    "id": author,
                    "label": author,
                    "size": engagement.get("likes", 0) + engagement.get("reposts", 0),
                }

            for other in record.get("mentions", []):
                edges.append({"source": author, "target": other, "type": "mention"})
                interactions[other] += 1

        top_influencers = sorted(
            nodes.keys(),
            key=lambda n: nodes[n]["size"],
            reverse=True,
        )[:5]

        return {
            "nodes": list(nodes.values()),
            "edges": edges,
            "top_influencers": top_influencers,
            "community_count": max(1, len(nodes) // 3),
        }
