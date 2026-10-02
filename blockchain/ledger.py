"""Local provenance ledger: SHA-256 hash chain + optional IPFS pinning.

Two independent integrity layers:

1. **Hash chain (always on)** - every block hashes its own content plus the
   previous block hash, so any edit to history invalidates every later block.
2. **IPFS pin (best effort)** - the canonical record bytes are pinned to the
   local kubo node and the CID is stored in the block. When the node is down
   the record is stored hash-only and says so; verification then relies on
   the chain, which still detects ledger tampering.

``cid``/``pinned``/``content_sha256`` are part of the block *before* the block
hash is computed, so they are covered by the chain as well.
"""

import json
import hashlib
import uuid
from pathlib import Path
from typing import Any
from datetime import datetime, timezone

from backend.config import get_settings
from blockchain.ipfs import IPFSClient


class BlockchainLedger:
    """Prototype permissioned ledger for insight provenance verification."""

    def __init__(self, ipfs_client: "IPFSClient | None" = None):
        self.settings = get_settings()
        self.ipfs = ipfs_client if ipfs_client is not None else IPFSClient()
        self.ledger_path = Path(self.settings.blockchain_ledger_path)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.ledger_path.exists():
            self._init_ledger()

    def _init_ledger(self):
        genesis = {
            "index": 0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {"message": "SOCIALIQ Genesis Block"},
            "previous_hash": "0" * 64,
            "hash": "",
        }
        genesis["hash"] = self._block_hash(genesis)
        self.ledger_path.write_text(json.dumps([genesis], indent=2))

    def _load_chain(self) -> list[dict]:
        return json.loads(self.ledger_path.read_text())

    def _save_chain(self, chain: list[dict]):
        self.ledger_path.write_text(json.dumps(chain, indent=2))

    def _block_hash(self, block: dict) -> str:
        block_copy = {k: v for k, v in block.items() if k != "hash"}
        content = json.dumps(block_copy, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()

    def record(self, data: dict) -> str:
        """Append a block for ``data``; returns its tx_id (unchanged API)."""
        chain = self._load_chain()
        previous = chain[-1]

        # Canonical bytes of the record: this exact serialization is what gets
        # pinned and what verification later re-hashes.
        canonical = json.dumps(data, sort_keys=True, default=str)
        content_sha256 = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        pin = self.ipfs.pin_json(data)

        block = {
            "index": len(chain),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data,
            "previous_hash": previous["hash"],
            "tx_id": str(uuid.uuid4())[:12],
            "content_sha256": content_sha256,
            "cid": pin.get("cid") if pin else None,
            "pinned": bool(pin and pin.get("pinned")),
        }
        block["hash"] = self._block_hash(block)
        chain.append(block)
        self._save_chain(chain)
        return block["tx_id"]

    def verify(self, insight_hash: str, dataset_hash: str) -> dict[str, Any]:
        chain = self._load_chain()

        for block in reversed(chain):
            data = block.get("data", {})
            if (
                data.get("insight_hash") == insight_hash
                and data.get("dataset_hash") == dataset_hash
            ):
                return {
                    "verified": True,
                    "message": "Provenance verified — insight matches blockchain record.",
                    "record": data,
                }

        return {
            "verified": False,
            "message": "No matching provenance record found on the ledger.",
        }

    def chain_integrity(self) -> dict[str, Any]:
        """Recompute every block hash and check the links hold."""
        chain = self._load_chain()
        previous_hash = "0" * 64
        for position, block in enumerate(chain):
            if block.get("index") != position:
                return {"valid": False, "reason": f"block {position} has a wrong index"}
            if block.get("previous_hash") != previous_hash:
                return {"valid": False, "reason": f"block {position} breaks the chain"}
            if self._block_hash(block) != block.get("hash"):
                return {"valid": False, "reason": f"block {position} contents were modified"}
            previous_hash = block["hash"]
        return {"valid": True, "blocks": len(chain)}

    def find_by_tx(self, tx_id: str) -> dict | None:
        """Return the newest block with this tx_id (used to read back the pin)."""
        for block in reversed(self._load_chain()):
            if block.get("tx_id") == tx_id:
                return block
        return None

    def verify_content(self, content_sha256: str, cid: str | None = None) -> dict[str, Any]:
        """Verify a record end to end: ledger block + IPFS content.

        The IPFS leg only runs when the block was pinned; a hash-only record is
        reported honestly rather than being called IPFS-verified.
        """
        chain = self._load_chain()
        block = next(
            (b for b in reversed(chain) if b.get("content_sha256") == content_sha256),
            None,
        )
        if not block:
            return {
                "verified": False,
                "checked": False,
                "message": "No ledger block matches that content hash.",
            }

        integrity = self.chain_integrity()
        result: dict[str, Any] = {
            "tx_id": block.get("tx_id"),
            "content_sha256": content_sha256,
            "cid": block.get("cid"),
            "pinned": bool(block.get("pinned")),
            "chain_valid": integrity["valid"],
            "chain_reason": integrity.get("reason"),
            "record": block.get("data"),
        }
        if not integrity["valid"]:
            result.update(
                {
                    "verified": False,
                    "checked": True,
                    "mode": "hash_chain",
                    "message": f"Ledger integrity check failed: {integrity['reason']}",
                }
            )
            return result

        target_cid = cid or block.get("cid")
        if block.get("pinned") and target_cid:
            ipfs_result = self.ipfs.verify(target_cid, content_sha256)
            result.update(
                {
                    "verified": bool(ipfs_result.get("verified")),
                    "checked": bool(ipfs_result.get("checked", False)),
                    "mode": "ipfs",
                    "computed_sha256": ipfs_result.get("computed_sha256"),
                    "bytes": ipfs_result.get("bytes"),
                    "message": ipfs_result.get("message"),
                }
            )
            return result

        result.update(
            {
                "verified": True,
                "checked": True,
                "mode": "hash_chain",
                "message": (
                    "Record verified against the local hash chain only - it was "
                    "stored without an IPFS pin (node unavailable at record time)."
                ),
            }
        )
        return result

    def is_available(self) -> bool:
        return self.ledger_path.exists()

    def ipfs_available(self) -> bool:
        return self.ipfs.available()
