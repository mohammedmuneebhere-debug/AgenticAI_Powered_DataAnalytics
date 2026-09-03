"""Provenance Agent — hashes analytical state and records on blockchain."""

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from blockchain.ledger import BlockchainLedger
from backend.models.schemas import ProvenanceRecord


class ProvenanceAgent:
    """Creates tamper-evident provenance records for insights."""

    ANALYSIS_VERSION = "socialiq-0.1.0"

    def __init__(self):
        self.ledger = BlockchainLedger()

    async def record(
        self,
        dataset_snapshot: dict,
        evidence: list,
        insight_text: str,
        model_version: str,
    ) -> ProvenanceRecord:
        dataset_hash = dataset_snapshot.get("data_hash", self._hash(dataset_snapshot))
        evidence_hash = self._hash(evidence)
        insight_hash = self._hash(insight_text)

        record_data = {
            "dataset_hash": dataset_hash,
            "insight_hash": insight_hash,
            "evidence_hash": evidence_hash,
            "model_version": model_version,
            "analysis_version": self.ANALYSIS_VERSION,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        tx_id = self.ledger.record(record_data)

        return ProvenanceRecord(
            dataset_hash=dataset_hash,
            insight_hash=insight_hash,
            evidence_hash=evidence_hash,
            model_version=model_version,
            analysis_version=self.ANALYSIS_VERSION,
            timestamp=datetime.now(timezone.utc),
            blockchain_tx_id=tx_id,
        )

    def _hash(self, data: Any) -> str:
        content = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()
