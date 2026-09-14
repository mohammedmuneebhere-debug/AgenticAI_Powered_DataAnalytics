"""Live verification of the dynamic-response fallback chain.

Boots nothing itself: expects the backend to already be listening on
API_PORT (default 8000). Registers a throwaway user, sends one chat
request, and prints the model_version + response text so the path
(OpenAI / Ollama / offline composer) can be confirmed.

Usage:
    .venv/Scripts/python.exe scripts/live_dynamic_response_check.py
"""

import json
import sys
import uuid

import httpx

BASE = "http://localhost:8000/api/v1"


def main() -> int:
    email = f"dyncheck-{uuid.uuid4().hex[:8]}@example.com"
    with httpx.Client(timeout=300) as client:
        health = client.get(f"{BASE}/health")
        print(f"health: {health.status_code} {health.json()}")
        if health.status_code != 200:
            return 1

        reg = client.post(
            f"{BASE}/auth/register",
            json={"email": email, "name": "Dyn Check", "password": "supersecret1"},
        )
        if reg.status_code not in (200, 201):
            print("register failed:", reg.status_code, reg.text)
            return 1
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        chat = client.post(
            f"{BASE}/chat",
            headers=headers,
            json={"message": "What coffee product should I launch this winter?"},
        )
        if chat.status_code != 200:
            print("chat failed:", chat.status_code, chat.text[:500])
            return 1

        payload = chat.json()
        print("\n=== CHAT RESULT ===")
        print("sources_used:", payload.get("sources_used"))
        print("model_version:", payload.get("model_version"))
        print("confidence:", payload.get("confidence"))
        print("evidence items:", len(payload.get("evidence") or []))
        print("\n--- response text ---")
        print(payload.get("message", "")[:2200])
        print("--- end (truncated) ---")

        text = str(payload.get("message") or "")
        if "Offline summary composed directly from pipeline analytics" in text:
            print("\npath: OFFLINE COMPOSER (as expected when Ollama is down)")
            canned = [c for c in ("cold brew", "+34%", "tue/thu", "2.4x") if c in text.lower()]
            print("canned-claim scan:", "CLEAN" if not canned else f"FOUND {canned}")
        elif text.strip():
            print("\npath: LLM (OpenAI or Ollama) — narrative text present")
        return 0


if __name__ == "__main__":
    sys.exit(main())
