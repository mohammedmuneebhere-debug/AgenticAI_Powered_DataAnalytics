import logging
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException
from backend.config import get_settings, split_allowed_domains
from backend.models.schemas import (
    ChatRequest, ChatResponse, VerifyRequest, VerifyResponse,
    HealthResponse, SessionSummary, SessionDetail, ToolsCatalogResponse,
    LLMModelsResponse, AvailableModel,
    SyntheticPostsRequest, SyntheticPostsResponse,
    SimilarRecord, SimilarRecordsResponse,
    ProvenanceVerifyRequest, ProvenanceVerifyResponse,
)
from agents.insight.agent import InsightAgent
from agents.synthetic_data.agent import SyntheticDataAgent
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
                    # Cloud-routed models (remote_host set) are served via
                    # ollama.com, not the local runtime - label them honestly.
                    suffix = "(Ollama cloud)" if entry.get("remote_host") else "(local Ollama)"
                    models.append(
                        AvailableModel(id=f"ollama:{name}", label=f"{name} {suffix}", provider="ollama")
                    )
    except Exception:
        pass  # Ollama offline — offer its configured default anyway
    default_id = f"ollama:{settings.ollama_model}" if not settings.openai_api_key else settings.llm_model
    if not any(m.id == default_id for m in models) and default_id:
        models.append(AvailableModel(id=default_id, label=f"{default_id} (default)", provider="openai"))
    return LLMModelsResponse(default_model=default_id, models=models)


@router.post("/synthetic-posts", response_model=SyntheticPostsResponse)
async def generate_synthetic_posts(
    request: SyntheticPostsRequest,
    user: Optional[dict] = Depends(_authenticate),
):
    """LLM-generate simulated posts for the relevant-posts card (on demand).

    Used by the dashboard when no posts were retrieved for the query. Posts are
    always platform="synthetic" with fictional sim_ handles and no URLs.
    """
    settings = get_settings()
    if not settings.synthetic_data_fallback:
        raise HTTPException(status_code=409, detail="Synthetic data fallback is disabled (SYNTHETIC_DATA_FALLBACK=false)")

    insight_agent = InsightAgent()
    agent = SyntheticDataAgent(insight_agent.generate_json)
    report = await agent.fill_gaps(
        query=request.query,
        intent="general",
        domain="general",
        analytics={},
        records=[],
        llm_model=None,
        only=["posts"],
    )
    if not report["synthetic_posts"]:
        raise HTTPException(status_code=503, detail="LLM unavailable - could not generate simulated posts")

    # Honest attribution: which engine actually served this generation
    generated_by = insight_agent._last_json_model_version or "llm"

    return SyntheticPostsResponse(
        query=request.query,
        generated_by=generated_by,
        disclosure=report["disclosure"] or "LLM-generated simulated posts (not retrieved posts).",
        synthetic_posts=report["synthetic_posts"],
    )


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


@router.get("/records/{record_hash}/similar", response_model=SimilarRecordsResponse)
async def similar_records(
    record_hash: str,
    limit: int = 5,
    min_similarity: float = 0.3,
    user: Optional[dict] = Depends(_authenticate),
):
    """Records semantically closest to a stored record (pgvector cosine).

    Returns an empty match list when semantic storage is unavailable, so the
    endpoint is safe to call in any deployment mode.
    """
    from backend.db.repository import get_embedding_record, similar_records as find_similar

    record = get_embedding_record(record_hash)
    if not record:
        raise HTTPException(status_code=404, detail="No embedded record with that hash")

    matches = find_similar(record_hash, limit=max(1, min(limit, 25)), min_similarity=min_similarity)
    return SimilarRecordsResponse(
        record_hash=record_hash,
        count=len(matches),
        min_similarity=min_similarity,
        matches=[SimilarRecord(**match) for match in matches],
    )


@router.post("/provenance/verify", response_model=ProvenanceVerifyResponse)
async def verify_provenance(
    request: ProvenanceVerifyRequest,
    user: Optional[dict] = Depends(_authenticate),
):
    """Re-fetch a pinned provenance record from IPFS and recompute its hash.

    Two independent checks run: the local hash chain must be intact, and (when
    the record was pinned) the bytes served by IPFS must hash to the same
    SHA-256 recorded in the ledger.
    """
    from blockchain.ledger import BlockchainLedger

    result = BlockchainLedger().verify_content(request.content_sha256, request.cid)
    return ProvenanceVerifyResponse(
        verified=bool(result.get("verified", False)),
        checked=bool(result.get("checked", False)),
        mode=result.get("mode", "hash_chain"),
        message=result.get("message", ""),
        tx_id=result.get("tx_id"),
        cid=result.get("cid"),
        pinned=bool(result.get("pinned", False)),
        chain_valid=result.get("chain_valid"),
        computed_sha256=result.get("computed_sha256"),
        record=result.get("record"),
    )


@router.post("/verify", response_model=VerifyResponse)
async def verify_insight(request: VerifyRequest):
    try:
        return await orchestrator.verify_insight(request)
    except Exception:
        logger.exception("Insight verification failed")
        raise HTTPException(status_code=500, detail="Unable to verify insight")
