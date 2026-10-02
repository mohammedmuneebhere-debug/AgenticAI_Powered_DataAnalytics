"""IPFS pinning for provenance records (kubo HTTP RPC).

Talks to the kubo HTTP RPC endpoint directly with httpx - one less client
dependency than ipfshttpclient, and the API we need is two calls.

Design rule: IPFS is an *enhancement*, never a requirement. When the node is
down or slow, ``available()`` is False, pinning is skipped, and provenance
degrades to the local SHA-256 hash chain, which still detects tampering with
the ledger itself. Nothing in this module raises to its callers.
"""

import hashlib
import json
import logging
from typing import Any, Optional

import httpx

from backend.config import get_settings

logger = logging.getLogger(__name__)


class IPFSClient:
    def __init__(self, api_url: Optional[str] = None, timeout: float = 10.0) -> None:
        self.api_url = (api_url or get_settings().ipfs_api_url).rstrip("/")
        self.timeout = timeout
        self._available: Optional[bool] = None

    # -- availability ---------------------------------------------------------

    def available(self) -> bool:
        if self._available is None:
            try:
                response = httpx.post(f"{self.api_url}/api/v0/id", timeout=self.timeout)
                self._available = response.status_code == 200
            except Exception as exc:
                logger.info("IPFS node unavailable (%s)", exc.__class__.__name__)
                self._available = False
        return bool(self._available)

    # -- pinning --------------------------------------------------------------

    def pin_json(self, payload: Any) -> Optional[dict]:
        """Pin a JSON-serializable payload; returns CID + content hash.

        Returns None when the node is unavailable, so callers can fall back to
        hash-only provenance.
        """
        if not self.available():
            return None
        raw = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        try:
            response = httpx.post(
                f"{self.api_url}/api/v0/add",
                params={"pin": "true", "cid-version": "1", "raw-leaves": "true"},
                files={"file": ("record.json", raw, "application/json")},
                timeout=self.timeout,
            )
            response.raise_for_status()
            entry = response.json()
            return {
                "cid": entry.get("Hash"),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "size": len(raw),
                "pinned": True,
            }
        except Exception as exc:
            logger.info("IPFS pin failed (%s)", exc.__class__.__name__)
            return None

    # -- retrieval / verification -----------------------------------------------

    def cat(self, cid: str) -> Optional[bytes]:
        if not self.available():
            return None
        try:
            response = httpx.post(
                f"{self.api_url}/api/v0/cat",
                params={"arg": cid},
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.content
        except Exception as exc:
            logger.info("IPFS cat failed (%s)", exc.__class__.__name__)
            return None

    def verify(self, cid: str, expected_sha256: str) -> dict[str, Any]:
        """Re-fetch a pinned record and recompute its SHA-256.

        ``verified`` is only true when the bytes come back from IPFS *and*
        hash to the expected value.
        """
        if not self.available():
            return {
                "verified": False,
                "checked": False,
                "cid": cid,
                "message": "IPFS node unavailable - cannot re-fetch the pinned record.",
            }
        raw = self.cat(cid)
        if raw is None:
            return {
                "verified": False,
                "checked": True,
                "cid": cid,
                "message": "Record could not be retrieved from IPFS.",
            }
        computed = hashlib.sha256(raw).hexdigest()
        verified = computed == expected_sha256
        return {
            "verified": verified,
            "checked": True,
            "cid": cid,
            "computed_sha256": computed,
            "expected_sha256": expected_sha256,
            "bytes": len(raw),
            "message": (
                "Pinned record re-fetched from IPFS and its SHA-256 matches the ledger."
                if verified
                else "Hash mismatch: the pinned record does not match the ledger entry."
            ),
        }
