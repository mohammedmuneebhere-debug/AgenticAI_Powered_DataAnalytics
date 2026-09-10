"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Shield, Loader2, ChevronDown, ChevronUp } from "lucide-react";
import { sendMessage, verifyInsight, getSession, type ChatResponse, type ToolConfig, type StoredMessage } from "@/lib/api";
import { DEMO_QUERIES, DOMAIN_COLORS } from "@/lib/constants";
import MarkdownMessage from "./MarkdownMessage";
import EvidencePanel from "./EvidencePanel";
import VisualizationPanel from "./VisualizationPanel";

interface Message {
  role: "user" | "assistant";
  content: string;
  response?: ChatResponse;
}

interface Props {
  sessionId?: string;
  onSessionId: (id: string) => void;
  toolConfig: ToolConfig;
}

export default function ChatArea({ sessionId, onSessionId, toolConfig }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [verifyResult, setVerifyResult] = useState<string | null>(null);
  const [expandedViz, setExpandedViz] = useState<Record<number, boolean>>({});
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!sessionId) { setMessages([]); return; }
    getSession(sessionId).then((s) => {
      setMessages(s.messages.map((m: StoredMessage) => ({
        role: m.role,
        content: m.content,
        response: m.role === "assistant" && m.metadata ? {
          session_id: s.id,
          message: m.content,
          intent: m.metadata.intent as string,
          domain: m.metadata.domain as string,
          domain_label: m.metadata.domain_label as string,
          entities: m.metadata.entities as string[],
          evidence: m.metadata.evidence as ChatResponse["evidence"],
          visualizations: m.metadata.visualizations as ChatResponse["visualizations"],
          provenance: m.metadata.provenance as ChatResponse["provenance"],
          confidence: m.metadata.confidence as number,
          workflow_used: m.metadata.workflow_used as string[],
          agents_used: m.metadata.agents_used as string[],
          sources_used: m.metadata.sources_used as string[],
        } : undefined,
      })));
    }).catch(() => setMessages([]));
  }, [sessionId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = async (text?: string) => {
    const msg = (text || input).trim();
    if (!msg || loading) return;

    setInput("");
    setVerifyResult(null);
    setMessages((prev) => [...prev, { role: "user", content: msg }]);
    setLoading(true);

    try {
      const response = await sendMessage(msg, sessionId, toolConfig);
      onSessionId(response.session_id);
      setMessages((prev) => [...prev, { role: "assistant", content: response.message, response }]);
    } catch {
      setMessages((prev) => [...prev, {
        role: "assistant",
        content: "Unable to reach SOCIALIQ backend. Ensure the API is running on port 8000.",
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async (response: ChatResponse) => {
    if (!response.provenance) return;
    setVerifying(true);
    try {
      const result = await verifyInsight(response.provenance.insight_hash, response.provenance.dataset_hash);
      setVerifyResult(result.message);
    } catch {
      setVerifyResult("Verification failed.");
    } finally {
      setVerifying(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Chat messages */}
      <div className="flex-1 overflow-y-auto chat-scroll px-6 py-6">
        {messages.length === 0 && (
          <div className="max-w-2xl mx-auto text-center pt-16">
            <div className="w-16 h-16 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-[#4285f4] via-[#8ab4f8] to-[#c58af9] flex items-center justify-center">
              <span className="text-2xl font-bold text-[var(--text-primary)]">S</span>
            </div>
            <h2 className="text-2xl font-normal text-[var(--text-primary)] mb-2">Hello, how can I help?</h2>
            <p className="text-sm text-[var(--text-secondary)] mb-8">
              Ask about trends, markets, audiences, or strategies across social platforms.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {DEMO_QUERIES.map((d) => (
                <button
                  key={d.domain}
                  onClick={() => handleSend(d.query)}
                  className="text-left p-4 rounded-2xl border border-[var(--border)] hover:bg-[var(--bg-surface)] transition-colors"
                >
                  <span className="text-[10px] font-medium uppercase tracking-wider" style={{ color: DOMAIN_COLORS[d.domain] }}>
                    {d.domain}
                  </span>
                  <p className="text-sm text-[var(--text-primary)] mt-1">{d.label}</p>
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="max-w-3xl mx-auto space-y-6">
          {messages.map((msg, i) => (
            <div key={i}>
              {msg.role === "user" ? (
                <div className="flex justify-end">
                  <div className="max-w-[80%] bg-[var(--bg-elevated)] rounded-3xl px-5 py-3">
                    <p className="text-sm">{msg.content}</p>
                  </div>
                </div>
              ) : (
                <div className="space-y-3">
                  {msg.response && (
                    <div className="flex items-center gap-2 flex-wrap">
                      <span
                        className="text-[11px] font-medium px-2.5 py-1 rounded-full"
                        style={{
                          background: `color-mix(in srgb, ${DOMAIN_COLORS[msg.response.domain] || DOMAIN_COLORS.general} 15%, transparent)`,
                          color: DOMAIN_COLORS[msg.response.domain] || DOMAIN_COLORS.general,
                        }}
                      >
                        {msg.response.domain_label}
                      </span>
                      <span className="text-[11px] text-[var(--text-muted)] px-2 py-0.5 rounded-full bg-[var(--bg-surface)]">
                        {msg.response.intent}
                      </span>
                      <span className="text-[11px] text-[var(--success)]">
                        {Math.round(msg.response.confidence * 100)}% confidence
                      </span>
                    </div>
                  )}
                  <MarkdownMessage content={msg.content} />

                  {msg.response && (
                    <div className="space-y-3 pt-2">
                      <div className="flex flex-wrap gap-1.5">
                        {msg.response.agents_used.slice(0, 5).map((a) => (
                          <span key={a} className="text-[10px] px-2 py-0.5 rounded-full bg-[var(--bg-surface)] text-[var(--text-muted)]">{a}</span>
                        ))}
                      </div>

                      <EvidencePanel evidence={msg.response.evidence} />

                      {msg.response.visualizations.length > 0 && (
                        <div>
                          <button
                            onClick={() => setExpandedViz((p) => ({ ...p, [i]: !p[i] }))}
                            className="flex items-center gap-1 text-xs text-[var(--accent)] mb-2"
                          >
                            {expandedViz[i] ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                            {expandedViz[i] ? "Hide" : "Show"} visualizations ({msg.response.visualizations.length})
                          </button>
                          {expandedViz[i] && (
                            <VisualizationPanel visualizations={msg.response.visualizations} />
                          )}
                        </div>
                      )}

                      {msg.response.provenance && (
                        <button
                          onClick={() => handleVerify(msg.response!)}
                          disabled={verifying}
                          className="flex items-center gap-2 text-xs px-3 py-1.5 rounded-full border border-[var(--border)] text-[var(--accent)] hover:bg-[var(--accent-bg)] transition-colors"
                        >
                          {verifying ? <Loader2 size={13} className="animate-spin" /> : <Shield size={13} />}
                          Verify Insight
                        </button>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex items-center gap-3 text-sm text-[var(--text-secondary)]">
              <Loader2 size={18} className="animate-spin text-[var(--accent)]" />
              <span>Analyzing social signals across agents…</span>
            </div>
          )}

          {verifyResult && (
            <div className={`text-sm px-4 py-2.5 rounded-xl border ${
              verifyResult.toLowerCase().includes("verified")
                ? "border-[var(--success)] text-[var(--success)] bg-[rgba(129,201,149,0.08)]"
                : "border-[var(--warning)] text-[var(--warning)]"
            }`}>
              {verifyResult}
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </div>

      {/* Input bar — Gemini style */}
      <div className="px-6 pb-6 pt-2">
        <div className="max-w-3xl mx-auto">
          <form
            onSubmit={(e) => { e.preventDefault(); handleSend(); }}
            className="flex items-center gap-2 bg-[var(--bg-input)] border border-[var(--border)] rounded-full px-2 py-1.5 focus-within:border-[var(--accent)] transition-colors"
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask SOCIALIQ anything…"
              className="flex-1 bg-transparent px-4 py-2.5 text-sm focus:outline-none placeholder:text-[var(--text-muted)]"
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="w-10 h-10 flex items-center justify-center rounded-full bg-[var(--accent)] hover:opacity-90 disabled:opacity-30 text-[var(--bg-app)] transition-opacity shrink-0"
            >
              <Send size={18} />
            </button>
          </form>
          <p className="text-center text-[10px] text-[var(--text-muted)] mt-2">
            SOCIALIQ may display inaccurate info. Verify important insights.
          </p>
        </div>
      </div>
    </div>
  );
}
