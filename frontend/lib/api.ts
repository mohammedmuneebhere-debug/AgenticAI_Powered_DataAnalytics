// Call the backend directly instead of via the Next.js proxy: the dev proxy
// aborts long-running requests (LLM generations can take 30-60s) with
// ECONNRESET / "socket hang up", which the UI then misreports as a 500.
// NEXT_PUBLIC_API_URL can still override this for deployments.
export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Generations through a cold-started local LLM can legitimately take a while;
// give the backend a generous ceiling before the UI gives up.
const API_TIMEOUT_MS = 180_000;

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

export interface ProvenanceRecord {
  dataset_hash: string;
  insight_hash: string;
  evidence_hash: string;
  model_version: string;
  analysis_version: string;
  timestamp: string;
  blockchain_tx_id?: string;
}

export interface TopPost {
  rank: number;
  text: string;
  author: string;
  platform: string;
  url?: string;
  timestamp?: string;
  engagement_total: number;
  relevance_score: number;
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
  news_articles?: Array<{ title: string; description?: string; source: string; published_at?: string; url: string }>;
  top_posts?: TopPost[];
  analytics?: Record<string, unknown>;
  model_version?: string;
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

export interface AvailableModel {
  id: string;
  label: string;
  provider: "openai" | "ollama";
}

export interface LLMModelsResponse {
  default_model: string | null;
  models: AvailableModel[];
}

/** Redirect to login when the API reports an expired/missing session. */
function handleUnauthorized(): void {
  if (typeof window !== "undefined") {
    window.localStorage.removeItem("socialiq-token");
    window.localStorage.removeItem("socialiq-user");
    window.location.href = "/login";
  }
}

export async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const token = typeof window !== "undefined" ? window.localStorage.getItem("socialiq-token") : null;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options?.headers as Record<string, string>),
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  let res: Response;
  try {
    res = await fetch(`${API_URL}/api/v1${path}`, {
      ...options,
      headers,
      signal: AbortSignal.timeout(API_TIMEOUT_MS),
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === "TimeoutError") {
      throw new Error(
        "The request timed out - the intelligence pipeline is taking longer than 3 minutes. Try a narrower query or a faster model."
      );
    }
    throw new Error(
      "Unable to reach the SOCIALIQ backend. Please ensure the backend server is running on port 8000."
    );
  }
  if (!res.ok) {
    if (res.status === 401) {
      handleUnauthorized();
    }
    let detail = "";
    try {
      const body = await res.json();
      detail = typeof body?.detail === "string" ? `: ${body.detail}` : "";
    } catch {
      /* body was not JSON - fall back to the status code only */
    }
    throw new Error(`API error: ${res.status}${detail}`);
  }
  return res.json();
}

export async function sendMessage(
  message: string,
  sessionId?: string,
  tools?: ToolConfig,
  llmModel?: string | null
): Promise<ChatResponse> {
  return apiFetch<ChatResponse>("/chat", {
    method: "POST",
    body: JSON.stringify({ message, session_id: sessionId, tools, llm_model: llmModel ?? undefined }),
  });
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

export async function getLLMModels(): Promise<LLMModelsResponse> {
  return apiFetch<LLMModelsResponse>("/llm/models");
}
