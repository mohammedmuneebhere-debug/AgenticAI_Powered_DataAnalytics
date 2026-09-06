"use client";

import React, { useState, useRef, useEffect } from "react";
import { useSocialIQ } from "@/context/SocialIQContext";
import { sendMessage } from "@/lib/api";
import { DEMO_SESSION_ID } from "@/lib/constants";
import ChatHeader from "./ChatHeader";
import ContextScopeBar from "./ContextScopeBar";
import UserMessage from "./UserMessage";
import AgentMessage from "./AgentMessage";
import SuggestedInquiries from "./SuggestedInquiries";
import ChatInputDock from "./ChatInputDock";

export default function ChatMode() {
  const {
    activeTopic,
    setActiveTopic,
    sessionId,
    setSessionId,
    toolConfig,
    chatMessages,
    addChatMessage,
  } = useSocialIQ();

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages, loading]);

  const handleSend = async (customQuery?: string) => {
    const queryText = (customQuery || input).trim();
    if (!queryText || loading) return;

    setInput("");
    const nowTime = new Date().toISOString().slice(11, 19) + " UTC";

    // 1. Add User Message
    addChatMessage({
      role: "user",
      content: queryText,
      timestamp: nowTime,
    });

    // Check if query implies a new topic
    if (
      !queryText.toLowerCase().includes(activeTopic.toLowerCase()) &&
      queryText.length > 3 &&
      !queryText.includes("?")
    ) {
      setActiveTopic(queryText.split(" ").slice(0, 3).join(" "));
    }

    setLoading(true);

    try {
      // 2. Call existing backend API pipeline
      const response = await sendMessage(
        queryText,
        sessionId === DEMO_SESSION_ID ? undefined : sessionId,
        toolConfig
      );
      if (response.session_id) {
        setSessionId(response.session_id);
      }

      // 3. Add Assistant Message with response payload
      addChatMessage({
        role: "assistant",
        content: response.message,
        response,
        timestamp: new Date().toISOString().slice(11, 19) + " UTC",
      });
    } catch (err) {
      console.error("Chat error:", err);
      addChatMessage({
        role: "assistant",
        content:
          "Unable to reach SOCIALIQ Agentic Core. Please ensure the backend server is running on port 8000.",
        timestamp: new Date().toISOString().slice(11, 19) + " UTC",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col w-full h-full justify-between">
      {/* Top Workspace Subheader */}
      <div className="flex flex-col w-full pb-5 mb-5 border-b border-border-subtle">
        <ChatHeader />
        <ContextScopeBar />
      </div>

      {/* Chat Stream Messages Container */}
      <div className="flex flex-col gap-6 flex-1 overflow-y-auto pr-1">
        <div className="w-full max-w-4xl mx-auto flex flex-col gap-8 py-2">
          {chatMessages.map((msg, index) => (
            <React.Fragment key={index}>
              {msg.role === "user" ? (
                <UserMessage content={msg.content} timestamp={msg.timestamp} />
              ) : (
                <AgentMessage
                  content={msg.content}
                  response={msg.response}
                  timestamp={msg.timestamp}
                />
              )}
            </React.Fragment>
          ))}

          {loading && (
            <div className="flex items-center gap-3 p-4 bg-[#13151b] border border-border-subtle rounded-2xl text-xs font-mono text-slate-400">
              <span className="material-symbols-outlined text-secondary text-[18px] animate-spin">
                progress_activity
              </span>
              <span>SOCIALIQ Multi-Agent Pipeline executing cross-platform telemetry...</span>
            </div>
          )}

          {/* Suggested Next Inquiries */}
          <SuggestedInquiries onSelectQuery={(q) => handleSend(q)} />

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Fixed Bottom Investigation Dock */}
      <ChatInputDock
        input={input}
        setInput={setInput}
        onSend={handleSend}
        loading={loading}
      />
    </div>
  );
}
