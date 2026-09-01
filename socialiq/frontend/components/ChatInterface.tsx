"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Shield, Loader2 } from "lucide-react";
import { sendMessage, verifyInsight, type ChatResponse } from "@/lib/api";
import VisualizationPanel from "./VisualizationPanel";
import EvidencePanel from "./EvidencePanel";
import DemoQueries from "./DemoQueries";

interface Message {
  role: "user" | "assistant";
  content: string;
  response?: ChatResponse;
}

interface Props {
  sessionId?: string;
  onSessionId: (id: string) => void;
}

export default function ChatInterface({ sessionId, onSessionId }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [verifyResult, setVerifyResult] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async (text?: string) => {
    const msg = (text || input).trim();
    if (!msg || loading) return;

    setInput("");
    setVerifyResult(null);
    setMessages((prev) => [...prev, { role: "user", content: msg }]);
    setLoading(true);

    try {
      const response = await sendMessage(msg, sessionId);
      onSessionId(response.session_id);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: response.message, response },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Unable to reach SOCIALIQ backend. Ensure the API is running on port 8000.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async (response: ChatResponse) => {
    if (!response.provenance) return;
    setVerifying(true);
    try {
      const result = await verifyInsight(
        response.provenance.insight_hash,
        response.provenance.dataset_hash
      );
      setVerifyResult(result.message);
    } catch {
      setVerifyResult("Verification failed — backend unavailable.");
    } finally {
      setVerifying(false);
    }
  };

  const lastResponse = [...messages].reverse().find((m) => m.response)?.response;

  return (
    <div className="flex flex-col gap-4 flex-1">
      <DemoQueries onSelect={(q) => { setInput(q); handleSend(q); }} />

      <div className="glass rounded-2xl flex flex-col flex-1 min-h-[500px]">
        <div className="flex-1 overflow-y-auto p-6 space-y-6 chat-scroll">
          {messages.length === 0 && (
            <div className="text-center text-[var(--text-secondary)] py-20">
              <p className="text-lg mb-2">Ask SOCIALIQ anything about trends, markets, or audiences.</p>
              <p className="text-sm">Try a demo query above to get started.</p>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              <div
                className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                  msg.role === "user"
                    ? "bg-[var(--accent)] text-white"
                    : "bg-[var(--bg-card)] border border-[var(--border)]"
                }`}
              >
                {msg.role === "assistant" && (
                  <p className="text-xs text-[var(--accent)] mb-1 font-medium">SOCIALIQ</p>
                )}
                <div className="whitespace-pre-wrap text-sm leading-relaxed">{msg.content}</div>

                {msg.response && (
                  <div className="mt-4 space-y-3">
                    <div className="flex flex-wrap gap-2 text-xs">
                      {msg.response.workflow_used.map((w) => (
                        <span key={w} className="px-2 py-0.5 rounded bg-[var(--bg-primary)] text-[var(--text-secondary)]">
                          {w}
                        </span>
                      ))}
                      <span className="px-2 py-0.5 rounded bg-[var(--bg-primary)] text-[var(--success)]">
                        {Math.round(msg.response.confidence * 100)}% confidence
                      </span>
                    </div>

                    <EvidencePanel evidence={msg.response.evidence} />
                    <VisualizationPanel visualizations={msg.response.visualizations} />

                    {msg.response.provenance && (
                      <button
                        onClick={() => handleVerify(msg.response!)}
                        disabled={verifying}
                        className="flex items-center gap-2 text-xs px-3 py-1.5 rounded-lg border border-[var(--accent)] text-[var(--accent)] hover:bg-[var(--accent-glow)] transition-colors"
                      >
                        {verifying ? <Loader2 size={14} className="animate-spin" /> : <Shield size={14} />}
                        Verify Insight
                      </button>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex items-center gap-2 text-[var(--text-secondary)] text-sm">
              <Loader2 size={16} className="animate-spin" />
              Analyzing social signals…
            </div>
          )}

          {verifyResult && (
            <div className={`text-sm px-4 py-2 rounded-lg border ${
              verifyResult.includes("verified")
                ? "border-[var(--success)] text-[var(--success)]"
                : "border-yellow-500 text-yellow-400"
            }`}>
              {verifyResult}
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        <div className="border-t border-[var(--border)] p-4">
          <form
            onSubmit={(e) => { e.preventDefault(); handleSend(); }}
            className="flex gap-3"
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask SOCIALIQ anything…"
              className="flex-1 bg-[var(--bg-primary)] border border-[var(--border)] rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-[var(--accent)]"
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="bg-[var(--accent)] hover:opacity-90 disabled:opacity-40 text-white rounded-xl px-4 py-3 transition-opacity"
            >
              <Send size={18} />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
