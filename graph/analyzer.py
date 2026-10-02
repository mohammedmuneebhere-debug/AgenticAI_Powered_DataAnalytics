"""Graph analytics — influence, communities, propagation (NetworkX).

Replaces the pure-python dict-counting stub with real graph analysis while
preserving the output keys consumers rely on:

    {
      "nodes":           [{"id", "label", "size", "community"}],
      "edges":           [{"source", "target", "type", "weight"}],
      "top_influencers": [author, ...] (top 5),
      "community_count": int,
    }

Real signals only: nodes are authors (node size = their total observed
engagement); edges are actual mentions — either an explicit ``mentions`` list
on the record or @handles parsed from the text. When a dataset has no
interaction edges the graph degrades to engagement-sorted nodes with zero
edges (the frontend already handles that), and the analyzer says so via
``method``.

Optional Neo4j mirror: when GRAPH_STORE=neo4j and the database is reachable,
nodes/edges are also written to Neo4j (best-effort, never blocks results).
"""

import logging
import re
from collections import defaultdict
from typing import Any

from backend.config import get_settings

logger = logging.getLogger(__name__)

_MENTION_RE = re.compile(r"@([A-Za-z0-9_]{2,30})")


class GraphAnalyzer:
    """Network intelligence from social interaction patterns."""

    def __init__(self) -> None:
        try:
            import networkx  # noqa: F401

            self._nx_available = True
        except ImportError:
            logger.warning("networkx not installed — falling back to dict counting")
            self._nx_available = False

    def analyze(self, records: list[dict]) -> dict[str, Any]:
        engagement = self._engagement_by_author(records)
        edges, mention_counts = self._interaction_edges(records)

        if self._nx_available:
            return self._analyze_networkx(records, engagement, edges, mention_counts)
        return self._analyze_fallback(records, engagement, edges)

    # -- extraction -----------------------------------------------------------

    @staticmethod
    def _engagement_by_author(records: list[dict]) -> dict[str, int]:
        totals: defaultdict[str, int] = defaultdict(int)
        for record in records:
            author = str(record.get("author") or "unknown")
            engagement = record.get("engagement") or {}
            if isinstance(engagement, dict):
                totals[author] += int(engagement.get("likes") or 0) + int(engagement.get("reposts") or 0)
        return dict(totals)

    @staticmethod
    def _interaction_edges(records: list[dict]) -> tuple[list[dict], defaultdict[str, int]]:
        # One edge per (source, target); repeated mentions raise its weight,
        # which is real signal about how strongly an account is discussed.
        weights: dict[tuple[str, str], int] = {}
        mention_counts: defaultdict[str, int] = defaultdict(int)
        for record in records:
            source = str(record.get("author") or "unknown")
            targets = set()
            explicit = record.get("mentions") or []
            if isinstance(explicit, list):
                targets |= {str(t) for t in explicit if t}
            text = str(record.get("text") or "")
            targets |= {f"@{m}" for m in _MENTION_RE.findall(text)}
            for target in targets:
                if target == source:
                    continue
                weights[(source, target)] = weights.get((source, target), 0) + 1
                mention_counts[target] += 1
        edges = [
            {"source": source, "target": target, "type": "mention", "weight": weight}
            for (source, target), weight in sorted(weights.items())
        ]
        return edges, mention_counts

    # -- networkx analysis ------------------------------------------------------

    def _analyze_networkx(
        self,
        records: list[dict],
        engagement: dict[str, int],
        edges: list[dict],
        mention_counts: defaultdict[str, int],
    ) -> dict[str, Any]:
        import networkx as nx

        graph = nx.DiGraph()
        for author, size in engagement.items():
            graph.add_node(author, size=size)
        for edge in edges:
            source, target = edge["source"], edge["target"]
            if graph.has_edge(source, target):
                graph[source][target]["weight"] += 1
            else:
                graph.add_edge(source, target, weight=1, type="mention")

        # Influence: blend PageRank (network position) with observed engagement.
        # Both are min-max normalized so neither saturates the ranking.
        if len(graph) == 0:
            return {"nodes": [], "edges": [], "top_influencers": [], "community_count": 0, "method": "networkx"}

        pagerank = nx.pagerank(graph, alpha=0.85, weight="weight") if graph.number_of_edges() else {
            node: 1.0 / len(graph) for node in graph
        }

        pagerank = nx.pagerank(graph, alpha=0.85, weight="weight") if graph.number_of_edges() else {
            node: 1.0 / len(graph) for node in graph
        }

        # Influence = network position + observed attention, combined as
        # *shares* of a common total. Min-max scaling would stretch tiny
        # PageRank gaps (0.19 vs 0.22) into dramatic-looking differences on
        # small graphs, which misrepresents the evidence.
        total_size = sum(engagement.values()) or 1
        ranked_nodes = sorted(
            graph.nodes,
            key=lambda n: 0.6 * pagerank.get(n, 0.0) + 0.4 * (engagement.get(n, 0) / total_size),
            reverse=True,
        )
        top_influencers = ranked_nodes[:5]

        # Communities on the undirected projection (greedy modularity; graceful
        # degradation to singleton groups when there are no edges)
        node_community: dict[str, int] = {}
        community_count = 0
        if graph.number_of_edges() >= len(graph) // 4 and len(graph) >= 3:
            try:
                undirected = graph.to_undirected()
                communities = nx.community.greedy_modularity_communities(undirected, weight="weight")
                community_count = len(communities)
                for index, community in enumerate(communities):
                    for node in community:
                        node_community[node] = index
            except Exception as exc:
                logger.info("Community detection failed (%s) — grouping by engagement", exc.__class__.__name__)
        if not node_community:
            # Deterministic fallback grouping by descending engagement
            ordered = sorted(graph.nodes, key=lambda n: engagement.get(n, 0), reverse=True)
            community_count = max(1, len(ordered) // 4) if ordered else 0
            for index, node in enumerate(ordered):
                node_community[node] = min(index // 4, max(0, community_count - 1))

        nodes = [
            {
                "id": author,
                "label": author,
                "size": engagement.get(author, 0),
                "community": node_community.get(author, 0),
                "mentions_received": mention_counts.get(author, 0),
            }
            for author in graph.nodes
        ]
        result = {
            "nodes": nodes,
            "edges": edges,
            "top_influencers": top_influencers,
            "community_count": community_count,
            "method": "networkx",
            "edge_count": len(edges),
        }
        self._mirror_to_neo4j(result)
        return result

    # -- fallback (no networkx) -----------------------------------------------------

    def _analyze_fallback(self, records: list[dict], engagement: dict[str, int], edges: list[dict]) -> dict[str, Any]:
        nodes = [
            {"id": author, "label": author, "size": size, "community": index // 3}
            for index, (author, size) in enumerate(
                sorted(engagement.items(), key=lambda kv: kv[1], reverse=True)
            )
        ]
        top_influencers = [n["id"] for n in nodes[:5]]
        return {
            "nodes": nodes,
            "edges": edges,
            "top_influencers": top_influencers,
            "community_count": max(1, len(nodes) // 3),
            "method": "fallback",
        }

    # -- optional Neo4j mirror --------------------------------------------------------

    @staticmethod
    def _mirror_to_neo4j(result: dict[str, Any]) -> None:
        if get_settings().graph_store != "neo4j":
            return
        try:
            from graph.neo4j_client import get_neo4j_client

            client = get_neo4j_client()
            if not client.available():
                return
            # Merge nodes and mention edges into the `Signal` graph
            client.run(
                "UNWIND $rows AS row MERGE (a:Signal {id: row.id}) "
                "SET a.size = row.size, a.community = row.community",
                rows=result["nodes"][:500],
            )
            client.run(
                "UNWIND $rows AS row "
                "MERGE (a:Signal {id: row.source}) MERGE (b:Signal {id: row.target}) "
                "MERGE (a)-[r:MENTIONS]->(b) SET r.weight = row.weight",
                rows=result["edges"][:1000],
            )
        except Exception as exc:
            logger.info("Neo4j mirror skipped: %s", exc.__class__.__name__)
