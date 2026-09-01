"""Data Intelligence Agent — cleaning, normalization, PII masking."""

import hashlib
import json
import re
from typing import Any
from datetime import datetime, timezone


PII_PATTERNS = [
    (re.compile(r"\b[\w.-]+@[\w.-]+\.\w+\b"), "[EMAIL]"),
    (re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"), "[PHONE]"),
]


class DataIntelligenceAgent:
    """Converts raw social data into a standardized analytical dataset."""

    async def process(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        records = raw_data.get("records", [])
        seen = set()
        cleaned = []

        for record in records:
            text = record.get("text", "").strip()
            if not text or text in seen:
                continue
            seen.add(text)

            text = self._mask_pii(text)
            text = self._normalize(text)

            cleaned.append({
                **record,
                "text": text,
                "language": self._detect_language(text),
                "entities_mentioned": self._extract_entities(text),
                "processed_at": datetime.now(timezone.utc).isoformat(),
            })

        snapshot_hash = hashlib.sha256(
            json.dumps(cleaned, sort_keys=True, default=str).encode()
        ).hexdigest()

        return {
            "records": cleaned,
            "count": len(cleaned),
            "snapshot": {
                "snapshot_id": raw_data.get("snapshot_id"),
                "data_hash": snapshot_hash,
                "platforms": raw_data.get("platforms", []),
                "query": raw_data.get("query"),
                "record_count": len(cleaned),
            },
        }

    def _mask_pii(self, text: str) -> str:
        for pattern, replacement in PII_PATTERNS:
            text = pattern.sub(replacement, text)
        return text

    def _normalize(self, text: str) -> str:
        text = re.sub(r"http\S+", "[URL]", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _detect_language(self, text: str) -> str:
        return "en"

    def _extract_entities(self, text: str) -> list[str]:
        keywords = ["coffee", "btc", "bitcoin", "cold brew", "espresso", "crypto", "winter"]
        return [kw for kw in keywords if kw.lower() in text.lower()]
