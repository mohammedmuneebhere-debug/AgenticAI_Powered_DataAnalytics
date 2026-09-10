"""Pytest fixtures: isolated data stores and env for the SOCIALIQ test suite."""

import os
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

# Offline, deterministic defaults before settings are cached
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("SERPAPI_API_KEY", "")
os.environ.setdefault("NEWS_API_KEY", "")
os.environ.setdefault("OPENAI_API_KEY", "")
os.environ.setdefault("OLLAMA_BASE_URL", "http://localhost:11434")
os.environ.setdefault("USERS_STORE_PATH", "./data/test_users.json")
os.environ.setdefault("SESSIONS_STORE_PATH", "./data/test_sessions.json")


@pytest.fixture()
def stores(tmp_path):
    """Fresh UserStore + ChatStore pointed at temp files."""
    from backend.auth.store import UserStore
    from backend.services.chat_store import ChatStore

    users = UserStore(tmp_path / "users.json")
    sessions = ChatStore(tmp_path / "sessions.json")
    return users, sessions


@pytest.fixture()
def registered_user(stores):
    users, _ = stores
    return users.create("user@example.com", "Test User", "supersecret1")


@pytest.fixture()
def auth_headers(registered_user):
    from backend.auth.security import create_access_token

    return {"Authorization": f"Bearer {create_access_token(registered_user['id'])}"}


@pytest.fixture(autouse=True)
def clean_settings_cache():
    """Reset the cached Settings after each test so env changes don't leak."""
    from backend.config import get_settings

    yield
    get_settings.cache_clear()


@pytest.fixture()
def client(stores, monkeypatch):
    """FastAPI TestClient wired to the isolated stores."""
    from fastapi.testclient import TestClient
    import backend.auth.dependencies as deps
    import backend.auth.routes as auth_routes
    import backend.services.orchestrator as orch
    import backend.api.routes as routes

    users, sessions = stores
    monkeypatch.setattr(deps, "user_store", users)
    monkeypatch.setattr(auth_routes, "user_store", users)
    instance = orch.OrchestratorService()
    monkeypatch.setattr(instance, "chat_store", sessions)
    monkeypatch.setattr(routes, "orchestrator", instance)

    import backend.main as main

    with TestClient(main.app) as test_client:
        yield test_client
