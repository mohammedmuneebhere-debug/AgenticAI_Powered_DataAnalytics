import logging

from fastapi import APIRouter, HTTPException
from backend.models.schemas import (
    ChatRequest, ChatResponse, VerifyRequest, VerifyResponse,
    HealthResponse, SessionSummary, SessionDetail, ToolsCatalogResponse,
)
from backend.services.orchestrator import OrchestratorService

router = APIRouter()
orchestrator = OrchestratorService()
logger = logging.getLogger(__name__)


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return await orchestrator.health_check()


@router.get("/tools", response_model=ToolsCatalogResponse)
async def list_tools():
    return orchestrator.get_tools()


@router.get("/sessions", response_model=list[SessionSummary])
async def list_sessions():
    return orchestrator.list_sessions()


@router.post("/sessions", response_model=SessionDetail)
async def create_session():
    return orchestrator.create_session()


@router.get("/sessions/{session_id}", response_model=SessionDetail)
async def get_session(session_id: str):
    session = orchestrator.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    if not orchestrator.delete_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    return {"deleted": True}


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        return await orchestrator.process_query(request)
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
