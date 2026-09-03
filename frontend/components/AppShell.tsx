"use client";

import { useState } from "react";
import Sidebar from "./Sidebar";
import ToolsPanel from "./ToolsPanel";
import ChatArea from "./ChatArea";
import type { ToolConfig } from "@/lib/api";
import { DEFAULT_AGENTS, DEFAULT_SOURCES } from "@/lib/constants";

export default function AppShell() {
  const [sessionId, setSessionId] = useState<string | undefined>();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [toolsCollapsed, setToolsCollapsed] = useState(false);
  const [toolConfig, setToolConfig] = useState<ToolConfig>({
    mode: "auto",
    enabled_agents: DEFAULT_AGENTS,
    enabled_sources: DEFAULT_SOURCES,
  });

  const handleNewChat = () => setSessionId(undefined);

  return (
    <div className="flex h-screen w-screen overflow-hidden">
      <Sidebar
        activeSessionId={sessionId}
        onSelectSession={setSessionId}
        onNewChat={handleNewChat}
        collapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed((p) => !p)}
      />

      <main className="flex-1 flex flex-col min-w-0 bg-[var(--bg-app)]">
        <header className="flex items-center justify-between px-6 py-3 border-b border-[var(--border-subtle)] shrink-0">
          <div className="flex items-center gap-2">
            <span className="live-dot w-2 h-2 rounded-full bg-[var(--success)]" />
            <span className="text-xs text-[var(--text-secondary)]">Live</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs px-2.5 py-1 rounded-full bg-[var(--bg-surface)] text-[var(--text-muted)]">
              {toolConfig.mode === "auto" ? "Auto orchestration" : "Manual tools"}
            </span>
          </div>
        </header>

        <ChatArea
          sessionId={sessionId}
          onSessionId={setSessionId}
          toolConfig={toolConfig}
        />
      </main>

      <ToolsPanel
        config={toolConfig}
        onChange={setToolConfig}
        collapsed={toolsCollapsed}
        onToggleCollapse={() => setToolsCollapsed((p) => !p)}
      />
    </div>
  );
}
