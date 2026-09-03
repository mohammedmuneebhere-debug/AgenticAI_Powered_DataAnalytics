"""Local blockchain provenance ledger (SHA-256 + JSON chain)."""

import json
import hashlib
import uuid
from pathlib import Path
from typing import Any
from datetime import datetime, timezone

from backend.config import get_settings


class BlockchainLedger:
    """Prototype permissioned ledger for insight provenance verification."""

    def __init__(self):
        self.settings = get_settings()
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
        chain = self._load_chain()
        previous = chain[-1]

        block = {
            "index": len(chain),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data,
            "previous_hash": previous["hash"],
            "tx_id": str(uuid.uuid4())[:12],
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

    def is_available(self) -> bool:
        return self.ledger_path.exists()
