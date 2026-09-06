import uuid
from datetime import datetime, timezone

from backend.models.schemas import (
    ChatRequest,
    ChatResponse,
    VerifyRequest,
    VerifyResponse,
    HealthResponse,
    QueryIntent,
    QueryDomain,
    SessionSummary,
    SessionDetail,
    ToolsCatalogResponse,
)
from agents.master.planner import MasterAgent
from agents.provenance.agent import ProvenanceAgent
from blockchain.ledger import BlockchainLedger
from backend.services.chat_store import ChatStore
from backend.services.tools_registry import get_tools_catalog


class OrchestratorService:
    """Coordinates the multi-agent pipeline for user queries."""

    def __init__(self):
        self.master_agent = MasterAgent()
        self.provenance_agent = ProvenanceAgent()
        self.ledger = BlockchainLedger()
        self.chat_store = ChatStore()

    async def process_query(self, request: ChatRequest) -> ChatResponse:
        session_id = request.session_id or str(uuid.uuid4())

        tools_config = request.tools.model_dump() if request.tools else None
        plan = await self.master_agent.plan_and_execute(request.message, tools_config=tools_config)

        self.chat_store.add_message(session_id, "user", request.message)

        provenance = None
        if not tools_config or "provenance" in (tools_config.get("enabled_agents") or ["provenance"]):
            provenance = await self.provenance_agent.record(
                dataset_snapshot=plan["dataset_snapshot"],
                evidence=plan["evidence"],
                insight_text=plan["response"],
                model_version=plan.get("model_version", "socialiq-0.2"),
            )

        metadata = {
            "intent": plan.get("intent"),
            "domain": plan.get("domain"),
            "domain_label": plan.get("domain_label"),
            "entities": plan.get("entities"),
            "confidence": plan.get("confidence"),
            "workflow_used": plan.get("workflow"),
            "agents_used": plan.get("agents_used"),
            "sources_used": plan.get("sources_used"),
            "evidence": plan.get("evidence"),
            "visualizations": plan.get("visualizations"),
            "provenance": provenance.model_dump() if provenance else None,
            "news_articles": plan.get("news_articles", []),
            "analytics": plan.get("analytics", {}),
        }
        self.chat_store.add_message(session_id, "assistant", plan["response"], metadata)

        return ChatResponse(
            session_id=session_id,
            message=plan["response"],
            intent=QueryIntent(plan.get("intent", "general")),
            domain=QueryDomain(plan.get("domain", "general")),
            domain_label=plan.get("domain_label", "General Social Intelligence"),
            entities=plan.get("entities", []),
            evidence=plan.get("evidence", []),
            visualizations=plan.get("visualizations", []),
            provenance=provenance,
            confidence=plan.get("confidence", 0.75),
            workflow_used=plan.get("workflow", []),
            agents_used=plan.get("agents_used", []),
            sources_used=plan.get("sources_used", []),
            news_articles=plan.get("news_articles", []),
            analytics=plan.get("analytics", {}),
        )

    async def verify_insight(self, request: VerifyRequest) -> VerifyResponse:
        result = self.ledger.verify(
            insight_hash=request.insight_hash,
            dataset_hash=request.dataset_hash,
        )
        return VerifyResponse(
            verified=result["verified"],
            message=result["message"],
            record=result.get("record"),
        )

    def list_sessions(self) -> list[SessionSummary]:
        return [SessionSummary(**s) for s in self.chat_store.list_sessions()]

    def get_session(self, session_id: str) -> SessionDetail | None:
        session = self.chat_store.get_session(session_id)
        if not session:
            return None
        return SessionDetail(**session)

    def create_session(self) -> SessionDetail:
        session = self.chat_store.create_session()
        return SessionDetail(**session)

    def delete_session(self, session_id: str) -> bool:
        return self.chat_store.delete_session(session_id)

    def get_tools(self) -> ToolsCatalogResponse:
        catalog = get_tools_catalog()
        return ToolsCatalogResponse(**catalog)

    async def health_check(self) -> HealthResponse:
        return HealthResponse(
            status="healthy",
            services={
                "master_agent": "ready",
                "blockchain": "ready" if self.ledger.is_available() else "degraded",
                "chat_store": "ready",
            },
        )
