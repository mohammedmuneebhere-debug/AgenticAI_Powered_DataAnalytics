import logging
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException
from backend.config import get_settings, split_allowed_domains
from backend.models.schemas import (
    ChatRequest, ChatResponse, VerifyRequest, VerifyResponse,
    HealthResponse, SessionSummary, SessionDetail, ToolsCatalogResponse,
    LLMModelsResponse, AvailableModel,
)
from backend.services.orchestrator import OrchestratorService
from backend.auth.dependencies import get_current_user

router = APIRouter()
orchestrator = OrchestratorService()
logger = logging.getLogger(__name__)


def _authenticate(
    authorization: Optional[str] = Header(default=None),
    x_api_key: Optional[str] = Header(default=None),
) -> Optional[dict]:
    """Accept either a user JWT (Bearer) or the shared N8N_API_KEY.

    Service integrations (n8n) authenticate with the API key; interactive
    users authenticate with a JWT. When no API key is configured the
    deployment runs in open local mode and requests pass through unauthenticated.
    """
    settings = get_settings()
    if settings.n8n_api_key and x_api_key == settings.n8n_api_key:
        return None
    if authorization:
        try:
            return get_current_user(authorization.removeprefix("Bearer ").strip())
        except HTTPException:
            raise
    if settings.n8n_api_key:
        raise HTTPException(status_code=401, detail="Missing or invalid credentials")
    return None


def _user_id(principal: Optional[dict]) -> str:
    return principal["id"] if principal else "local"


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return await orchestrator.health_check()


@router.get("/tools", response_model=ToolsCatalogResponse)
async def list_tools():
    return orchestrator.get_tools()


@router.get("/llm/models", response_model=LLMModelsResponse)
async def list_llm_models():
    settings = get_settings()
    models: list[AvailableModel] = []
    if settings.openai_api_key:
        models.append(AvailableModel(id="gpt-4o-mini", label="GPT-4o mini (cloud)", provider="openai"))
        models.append(AvailableModel(id="gpt-4o", label="GPT-4o (cloud)", provider="openai"))
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            resp = await client.get(f"{settings.ollama_base_url.rstrip('/')}/api/tags")
            resp.raise_for_status()
            for entry in resp.json().get("models", []):
                name = entry.get("name", "")
                if name:
                    models.append(
                        AvailableModel(id=f"ollama:{name}", label=f"{name} (local Ollama)", provider="ollama")
                    )
    except Exception:
        pass  # Ollama offline — offer its configured default anyway
    default_id = f"ollama:{settings.ollama_model}" if not settings.openai_api_key else settings.llm_model
    if not any(m.id == default_id for m in models) and default_id:
        models.append(AvailableModel(id=default_id, label=f"{default_id} (default)", provider="openai"))
    return LLMModelsResponse(default_model=default_id, models=models)


@router.get("/sessions", response_model=list[SessionSummary])
async def list_sessions(user: Optional[dict] = Depends(_authenticate)):
    return orchestrator.list_sessions(_user_id(user))


@router.post("/sessions", response_model=SessionDetail)
async def create_session(user: Optional[dict] = Depends(_authenticate)):
    return orchestrator.create_session(_user_id(user))


@router.get("/sessions/{session_id}", response_model=SessionDetail)
async def get_session(session_id: str, user: Optional[dict] = Depends(_authenticate)):
    session = orchestrator.get_session(session_id, _user_id(user))
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, user: Optional[dict] = Depends(_authenticate)):
    if not orchestrator.delete_session(session_id, _user_id(user)):
        raise HTTPException(status_code=404, detail="Session not found")
    return {"deleted": True}


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, user: Optional[dict] = Depends(_authenticate)):
    try:
        return await orchestrator.process_query(request, _user_id(user))
    except Exception:
        logger.exception("Chat request failed")
        raise HTTPException(status_code=500, detail="Unable to process chat request")


@router.post("/verify", response_model=VerifyResponse)
async def verify_insight(request: VerifyRequest):
    try:
        return await orchestrator.verify_insight(request)
    except Exception:
        logger.exception("Insight verification failed")
        raise HTTPException(status_code=500, detail="Unable to verify insight")
