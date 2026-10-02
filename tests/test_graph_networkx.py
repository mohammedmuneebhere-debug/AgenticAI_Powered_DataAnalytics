"""Phase 3 graph tests - NetworkX analyzer output shape and semantics."""

from graph.analyzer import GraphAnalyzer


RECORDS = [
    # A talks about B and C, B talks about A, C and D form a second cluster
    {"author": "@alice", "text": "great work by @bob and @carol", "engagement": {"likes": 40, "reposts": 10}},
    {"author": "@alice", "text": "second post mentioning @bob", "engagement": {"likes": 20, "reposts": 5}},
    {"author": "@bob", "text": "agree with @alice", "engagement": {"likes": 30, "reposts": 8}},
    {"author": "@carol", "text": "shipping to @dave", "engagement": {"likes": 10, "reposts": 2}},
    {"author": "@dave", "text": "noted @carol", "engagement": {"likes": 4, "reposts": 1}},
    {"author": "@erin", "text": "lurking", "engagement": {"likes": 1}},
]


class TestGraphAnalyzer:
    def test_output_shape_preserved(self):
        result = GraphAnalyzer().analyze(RECORDS)
        assert set(["nodes", "edges", "top_influencers", "community_count"]) <= set(result)

    def test_mention_edges_are_real(self):
        result = GraphAnalyzer().analyze(RECORDS)
        pairs = {(e["source"], e["target"]) for e in result["edges"]}
        assert ("@alice", "@bob") in pairs
        assert ("@bob", "@alice") in pairs
        assert ("@carol", "@dave") in pairs
        # dedup: alice mentioned bob twice -> one edge with weight 2
        alice_bob = next(e for e in result["edges"] if (e["source"], e["target"]) == ("@alice", "@bob"))
        assert alice_bob["weight"] == 2

    def test_node_size_is_total_engagement(self):
        result = GraphAnalyzer().analyze(RECORDS)
        alice = next(n for n in result["nodes"] if n["id"] == "@alice")
        assert alice["size"] == 40 + 10 + 20 + 5

    def test_influence_ranking_and_communities(self):
        result = GraphAnalyzer().analyze(RECORDS)
        assert len(result["top_influencers"]) == 5
        assert result["top_influencers"][0] in ("@alice", "@bob")
        assert result["community_count"] >= 1
        assert all("community" in n for n in result["nodes"])

    def test_no_interactions_degrades_cleanly(self):
        result = GraphAnalyzer().analyze([{"author": "@solo", "text": "no mentions here", "engagement": {"likes": 3}}])
        assert result["edges"] == []
        assert result["nodes"][0]["id"] == "@solo"
        assert result["community_count"] >= 1

    def test_empty_input(self):
        result = GraphAnalyzer().analyze([])
        assert result["nodes"] == [] and result["edges"] == []
        assert result["top_influencers"] == []

    def test_memory_store_is_default(self):
        import backend.config as config

        assert config.get_settings().graph_store == "memory"
        result = GraphAnalyzer().analyze(RECORDS)
        assert result["method"] == "networkx"
