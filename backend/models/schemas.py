from pydantic import BaseModel, Field
from typing import Any, Optional, Literal
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class QueryIntent(str, Enum):
    TREND = "trend"
    SENTIMENT = "sentiment"
    DEMOGRAPHICS = "demographics"
    INFLUENCE = "influence"
    STRATEGY = "strategy"
    MARKET = "market"
    GENERAL = "general"


class QueryDomain(str, Enum):
    CONSUMER = "consumer"
    FINANCIAL = "financial"
    CREATOR = "creator"
    GENERAL = "general"


class OrchestrationMode(str, Enum):
    AUTO = "auto"
    MANUAL = "manual"


class AgentTool(BaseModel):
    id: str
    name: str
    description: str
    category: str
    default_enabled: bool = True


class DataSource(BaseModel):
    id: str
    name: str
    description: str
    default_enabled: bool = True
    requires_key: Optional[str] = None


class ToolConfig(BaseModel):
    mode: OrchestrationMode = OrchestrationMode.AUTO
    enabled_agents: Optional[list[str]] = None
    enabled_sources: Optional[list[str]] = None


class ChatMessage(BaseModel):
    role: MessageRole
    content: str
    metadata: Optional[dict[str, Any]] = None


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    tools: Optional[ToolConfig] = None


class EvidenceItem(BaseModel):
    type: str
    label: str
    value: Any
    confidence: float = Field(ge=0.0, le=1.0)
    source: Optional[str] = None


class VisualizationSpec(BaseModel):
    type: str
    title: str
    data: dict[str, Any]


class ProvenanceRecord(BaseModel):
    dataset_hash: str
    insight_hash: str
    evidence_hash: str
    model_version: str
    analysis_version: str
    timestamp: datetime
    blockchain_tx_id: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    message: str
    intent: QueryIntent
    domain: QueryDomain
    entities: list[str] = []
    domain_label: str = ""
    evidence: list[EvidenceItem] = []
    visualizations: list[VisualizationSpec] = []
    provenance: Optional[ProvenanceRecord] = None
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    workflow_used: list[str] = []
    agents_used: list[str] = []
    sources_used: list[str] = []


class SessionSummary(BaseModel):
    id: str
    title: str
    domain: Optional[str] = None
    updated_at: Optional[str] = None
    message_count: int = 0


class SessionDetail(BaseModel):
    id: str
    title: str
    domain: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    messages: list[dict[str, Any]] = []


class ToolsCatalogResponse(BaseModel):
    agents: list[AgentTool]
    sources: list[DataSource]


class VerifyRequest(BaseModel):
    insight_hash: str
    dataset_hash: str


class VerifyResponse(BaseModel):
    verified: bool
    message: str
    record: Optional[ProvenanceRecord] = None


class HealthResponse(BaseModel):
    status: str
    version: str = "0.2.0"
    services: dict[str, str] = {}
