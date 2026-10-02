"""Phase 5 tests - provenance hash chain + IPFS pinning.

The hash-chain layer is always exercised. IPFS-specific tests skip when no
kubo node is reachable, and a fake offline client proves the hash-only
fallback path.
"""

import json

import pytest

from blockchain.ipfs import IPFSClient
from blockchain.ledger import BlockchainLedger


def _ipfs_up() -> bool:
    try:
        return IPFSClient().available()
    except Exception:
        return False


needs_ipfs = pytest.mark.skipif(not _ipfs_up(), reason="IPFS node not available")


class _OfflineIPFS:
    """Stands in for a dead node."""

    def available(self) -> bool:
        return False

    def pin_json(self, payload):
        return None

    def cat(self, cid):
        return None

    def verify(self, cid, expected_sha256):
        return {"verified": False, "checked": False, "message": "IPFS node unavailable"}


@pytest.fixture()
def ledger(tmp_path, monkeypatch):
    import backend.config as config

    settings = config.get_settings()
    monkeypatch.setattr(settings, "blockchain_ledger_path", str(tmp_path / "ledger.json"), raising=False)
    return BlockchainLedger(ipfs_client=_OfflineIPFS())


class TestHashChainAlways:
    def test_record_and_chain_integrity(self, ledger):
        ledger.record({"insight_hash": "a" * 64, "dataset_hash": "b" * 64})
        assert ledger.chain_integrity() == {"valid": True, "blocks": 2}  # genesis + 1

    def test_tampering_is_detected(self, ledger, tmp_path):
        ledger.record({"insight_hash": "a" * 64})
        chain = json.loads((tmp_path / "ledger.json").read_text())
        chain[-1]["data"]["insight_hash"] = "f" * 64  # edit history
        (tmp_path / "ledger.json").write_text(json.dumps(chain))

        result = ledger.chain_integrity()
        assert result["valid"] is False
        assert "modified" in result["reason"]

    def test_verify_content_unknown_hash(self, ledger):
        result = ledger.verify_content("0" * 64)
        assert result["verified"] is False and result["checked"] is False

    def test_hash_only_mode_is_labelled_honestly(self, ledger):
        """With the node down the record still verifies, but says it is local."""
        ledger.record({"insight_hash": "c" * 64})
        block = ledger._load_chain()[-1]
        assert block["pinned"] is False and block["cid"] is None

        result = ledger.verify_content(block["content_sha256"])
        assert result["verified"] is True
        assert result["mode"] == "hash_chain"
        assert "without an IPFS pin" in result["message"]

    def test_legacy_block_without_cid_still_loads(self, tmp_path, monkeypatch):
        """Blocks written before Phase 5 have no cid/content_sha256 fields."""
        import backend.config as config

        settings = config.get_settings()
        legacy = [
            {
                "index": 0,
                "timestamp": "2026-01-01T00:00:00+00:00",
                "data": {"message": "SOCIALIQ Genesis Block"},
                "previous_hash": "0" * 64,
                "hash": "",
            }
        ]
        legacy[0]["hash"] = BlockchainLedger(ipfs_client=_OfflineIPFS())._block_hash(legacy[0])
        path = tmp_path / "legacy.json"
        path.write_text(json.dumps(legacy))
        monkeypatch.setattr(settings, "blockchain_ledger_path", str(path), raising=False)

        legacy_ledger = BlockchainLedger(ipfs_client=_OfflineIPFS())
        assert legacy_ledger.chain_integrity()["valid"] is True
        assert legacy_ledger.verify_content("9" * 64)["verified"] is False


@needs_ipfs
class TestIPFSPinning:
    def test_pin_verify_round_trip(self, tmp_path, monkeypatch):
        import backend.config as config

        settings = config.get_settings()
        monkeypatch.setattr(settings, "blockchain_ledger_path", str(tmp_path / "ledger.json"), raising=False)
        live = BlockchainLedger()
        assert live.ipfs_available() is True

        tx_id = live.record({"insight_hash": "d" * 64, "dataset_hash": "e" * 64})
        block = live.find_by_tx(tx_id)
        assert block["pinned"] is True
        assert block["cid"] and block["cid"].startswith("bafk")

        result = live.verify_content(block["content_sha256"])
        assert result["mode"] == "ipfs"
        assert result["verified"] is True
        assert result["chain_valid"] is True
        assert result["computed_sha256"] == block["content_sha256"]

    def test_tampered_content_fails_verification(self, tmp_path, monkeypatch):
        import backend.config as config

        settings = config.get_settings()
        monkeypatch.setattr(settings, "blockchain_ledger_path", str(tmp_path / "ledger.json"), raising=False)
        live = BlockchainLedger()
        tx_id = live.record({"insight_hash": "1" * 64})
        block = live.find_by_tx(tx_id)

        # Ask IPFS for a different record's content: the hash must not match.
        other = live.record({"insight_hash": "2" * 64})
        other_block = live.find_by_tx(other)
        result = live.verify_content(block["content_sha256"], cid=other_block["cid"])
        assert result["verified"] is False
        assert result["computed_sha256"] != block["content_sha256"]
