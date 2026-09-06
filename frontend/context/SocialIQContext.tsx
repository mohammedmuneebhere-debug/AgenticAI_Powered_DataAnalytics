"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import {
  sendMessage,
  getTools,
  getSession,
  listSessions,
  type ChatResponse,
  type ToolConfig,
  type ToolsCatalog,
  type DataSource,
  type SessionSummary,
} from "@/lib/api";
import {
  DEFAULT_AGENTS,
  DEFAULT_SOURCES,
  DEMO_MESSAGES,
  DEMO_SESSION_ID,
  DEMO_SESSION_TITLE,
  FALLBACK_AGENTS,
  FALLBACK_SOURCES,
} from "@/lib/constants";

export interface ChatMessageItem {
  id?: string;
  role: "user" | "assistant";
  content: string;
  response?: ChatResponse;
  timestamp?: string;
}

interface SocialIQContextType {
  activeMode: "chat" | "dashboard";
  setActiveMode: (mode: "chat" | "dashboard") => void;
  activeTopic: string;
  setActiveTopic: (topic: string) => void;
  analysisCache: Record<string, ChatResponse>;
  isAnalyzing: boolean;
  runTopicAnalysis: (topic: string, force?: boolean) => Promise<ChatResponse | null>;
  toolConfig: ToolConfig;
  setToolConfig: React.Dispatch<React.SetStateAction<ToolConfig>>;
  toolsCatalog: ToolsCatalog | null;
  toolsLoading: boolean;
  refreshToolsCatalog: () => Promise<void>;
  sessions: SessionSummary[];
  sessionsLoading: boolean;
  refreshSessions: () => Promise<void>;
  loadSession: (id: string) => Promise<void>;
  sessionId?: string;
  setSessionId: (id?: string) => void;
  chatMessages: ChatMessageItem[];
  setChatMessages: React.Dispatch<React.SetStateAction<ChatMessageItem[]>>;
  addChatMessage: (msg: ChatMessageItem) => void;
  newInvestigation: () => void;
  toolsCollapsed: boolean;
  setToolsCollapsed: React.Dispatch<React.SetStateAction<boolean>>;
}

const SocialIQContext = createContext<SocialIQContextType | undefined>(undefined);

export function SocialIQProvider({ children }: { children: React.ReactNode }) {
  const [activeMode, setActiveMode] = useState<"chat" | "dashboard">("chat");
  const [activeTopic, setActiveTopic] = useState<string>("AI Agents");
  const [analysisCache, setAnalysisCache] = useState<Record<string, ChatResponse>>({});
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [sessionId, setSessionId] = useState<string | undefined>(DEMO_SESSION_ID);
  const [toolsCollapsed, setToolsCollapsed] = useState(false);

  const [toolConfig, setToolConfig] = useState<ToolConfig>({
    mode: "auto",
    enabled_agents: DEFAULT_AGENTS,
    enabled_sources: DEFAULT_SOURCES,
  });

  const [toolsCatalog, setToolsCatalog] = useState<ToolsCatalog>({
    agents: FALLBACK_AGENTS,
    sources: FALLBACK_SOURCES as DataSource[],
  });
  const [toolsLoading, setToolsLoading] = useState(false);
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [sessionsLoading, setSessionsLoading] = useState(false);

  // Initial demonstration message aligned with design placeholders for first visit
  const [chatMessages, setChatMessages] = useState<ChatMessageItem[]>(DEMO_MESSAGES);

  const refreshToolsCatalog = useCallback(async () => {
    setToolsLoading(true);
    try {
      const cat = await getTools();
      setToolsCatalog(cat);
      setToolConfig((prev) =>
        prev.mode === "auto"
          ? {
              ...prev,
              enabled_agents: cat.agents.filter((agent) => agent.default_enabled).map((agent) => agent.id),
              enabled_sources: cat.sources.filter((source) => source.default_enabled).map((source) => source.id),
            }
          : prev
      );
    } catch {
      setToolsCatalog({
        agents: FALLBACK_AGENTS,
        sources: FALLBACK_SOURCES as DataSource[],
      });
    } finally {
      setToolsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshToolsCatalog();
  }, [refreshToolsCatalog]);

  const refreshSessions = useCallback(async () => {
    setSessionsLoading(true);
    try {
      const backendSessions = await listSessions();
      setSessions([
        {
          id: DEMO_SESSION_ID,
          title: DEMO_SESSION_TITLE,
          domain: "general",
          message_count: DEMO_MESSAGES.length,
        },
        ...backendSessions.filter((session) => session.id !== DEMO_SESSION_ID),
      ]);
    } catch (err) {
      console.error("Failed to load conversation history:", err);
    } finally {
      setSessionsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshSessions();
  }, [refreshSessions]);

  const loadSession = useCallback(async (id: string) => {
    if (id === DEMO_SESSION_ID) {
      setSessionId(id);
      setActiveTopic("AI Agents");
      setChatMessages(DEMO_MESSAGES);
      return;
    }
    const session = await getSession(id);
    setSessionId(session.id);
    setChatMessages(
      session.messages.map((message) => ({
        id: message.id,
        role: message.role,
        content: message.content,
        timestamp: message.created_at
          ? new Date(message.created_at).toISOString().slice(11, 19) + " UTC"
          : undefined,
      }))
    );
  }, []);

  const runTopicAnalysis = useCallback(
    async (topic: string, force = false): Promise<ChatResponse | null> => {
      const normalized = topic.trim();
      if (!normalized) return null;

      setActiveTopic(normalized);

      // Return cached analysis if available and not forced
      if (!force && analysisCache[normalized]) {
        return analysisCache[normalized];
      }

      setIsAnalyzing(true);
      try {
        const queryText = `${normalized} topic analysis and social signal telemetry`;
        const res = await sendMessage(queryText, sessionId, toolConfig);
        setAnalysisCache((prev) => ({ ...prev, [normalized]: res }));
        if (res.session_id) {
          setSessionId(res.session_id);
        }
        return res;
      } catch (err) {
        console.error("Failed to run topic analysis for:", normalized, err);
        return null;
      } finally {
        setIsAnalyzing(false);
      }
    },
    [analysisCache, sessionId, toolConfig]
  );

  const addChatMessage = (msg: ChatMessageItem) => {
    setChatMessages((prev) => [...prev, msg]);
  };

  const newInvestigation = () => {
    setSessionId(undefined);
    setChatMessages([]);
    setActiveTopic("AI Agents");
  };

  return (
    <SocialIQContext.Provider
      value={{
        activeMode,
        setActiveMode,
        activeTopic,
        setActiveTopic,
        analysisCache,
        isAnalyzing,
        runTopicAnalysis,
        toolConfig,
        setToolConfig,
        toolsCatalog,
        toolsLoading,
        refreshToolsCatalog,
        sessions,
        sessionsLoading,
        refreshSessions,
        loadSession,
        sessionId,
        setSessionId,
        chatMessages,
        setChatMessages,
        addChatMessage,
        newInvestigation,
        toolsCollapsed,
        setToolsCollapsed,
      }}
    >
      {children}
    </SocialIQContext.Provider>
  );
}

export function useSocialIQ() {
  const context = useContext(SocialIQContext);
  if (!context) {
    throw new Error("useSocialIQ must be used within a SocialIQProvider");
  }
  return context;
}
