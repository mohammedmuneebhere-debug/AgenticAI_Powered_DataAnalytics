const API_URL = process.env.NEXT_PUBLIC_API_URL || "";
const N8N_WEBHOOK_URL =
  process.env.NEXT_PUBLIC_N8N_WEBHOOK_URL ||
  "http://localhost:5678/webhook/socialiq";

export interface EvidenceItem {
  type: string;
  label: string;
  value: unknown;
  confidence: number;
  source?: string;
}

export interface VisualizationSpec {
  type: string;
  title: string;
  data: Record<string, unknown>;
}

export interface NewsArticle {
  title: string;
  description: string;
  source: string;
  published_at?: string;
  url: string;
}

export interface ProvenanceRecord {
  dataset_hash: string;
  insight_hash: string;
  evidence_hash: string;
  model_version: string;
  analysis_version: string;
  timestamp: string;
  blockchain_tx_id?: string;
}

export interface ToolConfig {
  mode: "auto" | "manual";
  enabled_agents?: string[];
  enabled_sources?: string[];
}

export interface ChatResponse {
  session_id: string;
  message: string;
  intent: string;
  domain: string;
  domain_label: string;
  entities: string[];
  evidence: EvidenceItem[];
  visualizations: VisualizationSpec[];
  provenance?: ProvenanceRecord;
  confidence: number;
  workflow_used: string[];
  agents_used: string[];
  sources_used: string[];
  news_articles: NewsArticle[];
}

export interface SessionSummary {
  id: string;
  title: string;
  domain?: string;
  updated_at?: string;
  message_count: number;
}

export interface SessionDetail {
  id: string;
  title: string;
  domain?: string;
  created_at?: string;
  updated_at?: string;
  messages: StoredMessage[];
}

export interface StoredMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  metadata?: Record<string, unknown>;
  created_at?: string;
}

export interface AgentTool {
  id: string;
  name: string;
  description: string;
  category: string;
  default_enabled: boolean;
}

export interface DataSource {
  id: string;
  name: string;
  description: string;
  default_enabled: boolean;
  requires_key?: string;
}

export interface ToolsCatalog {
  agents: AgentTool[];
  sources: DataSource[];
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}/api/v1${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function sendMessage(
  message: string,
  sessionId?: string,
  tools?: ToolConfig
): Promise<ChatResponse> {
  const res = await fetch(N8N_WEBHOOK_URL, {
    headers: { "Content-Type": "application/json" },
    method: "POST",
    body: JSON.stringify({ message, session_id: sessionId, tools }),
  });
  if (!res.ok) throw new Error(`n8n webhook error: ${res.status}`);
  return res.json();
}

export async function verifyInsight(insightHash: string, datasetHash: string) {
  return apiFetch<{ verified: boolean; message: string }>("/verify", {
    method: "POST",
    body: JSON.stringify({ insight_hash: insightHash, dataset_hash: datasetHash }),
  });
}

export async function listSessions(): Promise<SessionSummary[]> {
  return apiFetch<SessionSummary[]>("/sessions");
}

export async function getSession(id: string): Promise<SessionDetail> {
  return apiFetch<SessionDetail>(`/sessions/${id}`);
}

export async function createSession(): Promise<SessionDetail> {
  return apiFetch<SessionDetail>("/sessions", { method: "POST" });
}

export async function deleteSession(id: string): Promise<void> {
  await apiFetch(`/sessions/${id}`, { method: "DELETE" });
}

export async function getTools(): Promise<ToolsCatalog> {
  return apiFetch<ToolsCatalog>("/tools");
}
