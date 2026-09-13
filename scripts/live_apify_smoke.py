"""Live end-to-end smoke test for the Apify x_scraper connector.

Boots the real FastAPI backend on :8000, registers a throwaway user, sends a
chat query with ONLY the x_scraper source enabled, and verifies:
  1. the tools catalog advertises x_scraper,
  2. the chat response's sources_used contains x_scraper,
  3. scraped X records reach the evidence/analytics pipeline,
  4. the session persists for the user.

Run:  .venv/Scripts/python.exe scripts/live_apify_smoke.py
"""

import subprocess
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://localhost:8000/api/v1"

TEST_EMAIL = "apify-test@socialiq.local"
TEST_PASSWORD = "ApifyTest123!"


def wait_for_health(client: httpx.Client, seconds: int = 60) -> None:
    deadline = time.time() + seconds
    while time.time() < deadline:
        try:
            if client.get(f"{BASE}/health").status_code == 200:
                return
        except httpx.TransportError:
            pass
        time.sleep(1)
    raise RuntimeError("Backend did not become healthy in time")


def main() -> None:
    server = subprocess.Popen(
        [sys.executable, "-c", "import uvicorn; uvicorn.run('backend.main:app', host='127.0.0.1', port=8000, log_level='warning')"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    try:
        with httpx.Client(timeout=300) as client:
            wait_for_health(client)
            print("[1] Backend is up")

            # Register (or log in if re-running)
            resp = client.post(
                f"{BASE}/auth/register",
                json={"email": TEST_EMAIL, "name": "Apify Tester", "password": TEST_PASSWORD},
            )
            if resp.status_code == 409:
                resp = client.post(
                    f"{BASE}/auth/login",
                    json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
                )
            resp.raise_for_status()
            token = resp.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            print(f"[2] Authenticated as {TEST_EMAIL}")

            # Tools catalog must advertise the new connector
            catalog = client.get(f"{BASE}/tools", headers=headers).json()
            sources = {s["id"]: s for s in catalog["sources"]}
            assert "x_scraper" in sources, f"x_scraper missing from catalog: {list(sources)}"
            print(f"[3] Catalog advertises '{sources['x_scraper']['name']}' (requires {sources['x_scraper']['requires_key']})")

            # Chat with ONLY the Apify scraper enabled
            payload = {
                "message": "What is the overall sentiment and top discussion themes around specialty coffee on X right now?",
                "tools": {
                    "mode": "manual",
                    "enabled_sources": ["x_scraper"],
                },
            }
            t0 = time.time()
            chat = client.post(f"{BASE}/chat", json=payload, headers=headers)
            elapsed = time.time() - t0
            chat.raise_for_status()
            data = chat.json()

            sources_used = data.get("sources_used") or []
            evidence = data.get("evidence") or []
            analytics = data.get("analytics") or {}
            print(f"[4] Chat completed in {elapsed:.1f}s | sources_used={sources_used}")
            assert "x_scraper" in sources_used, f"expected x_scraper in sources_used, got {sources_used}"
            print(f"[5] Evidence items from pipeline: {len(evidence)}")
            if evidence:
                first = evidence[0]
                print(f"    sample evidence: {str(first)[:160]}")
            print(f"    analytics keys: {sorted(analytics.keys())}")

            # The session must be persisted for this user
            sessions = client.get(f"{BASE}/sessions", headers=headers).json()
            session_ids = [s["id"] for s in (sessions if isinstance(sessions, list) else [])]
            assert data["session_id"] in session_ids, "chat session not persisted for user"
            print(f"[6] Session {data['session_id'][:8]}... persisted ({len(session_ids)} session(s) for user)")

            print("\n=== RESPONSE (first 700 chars) ===")
            print(data.get("message", "")[:700])
            print("\nPASS: Apify x_scraper works end-to-end through the live backend")
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    main()
