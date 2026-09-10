"use client";

import React from "react";
import { useSocialIQ } from "@/context/SocialIQContext";
import { FALLBACK_AGENTS, FALLBACK_SOURCES } from "@/lib/constants";

export default function ToolsConnectorsSidebar() {
  const {
    toolConfig,
    setToolConfig,
    toolsCatalog,
    toolsLoading,
    refreshToolsCatalog,
    toolsCollapsed,
    setToolsCollapsed,
  } = useSocialIQ();

  const isAuto = toolConfig.mode === "auto";

  const toggleOrchestration = () => {
    if (isAuto) {
      setToolConfig((prev) => ({ ...prev, mode: "manual" }));
      return;
    }

    const autoAgents = (toolsCatalog?.agents || FALLBACK_AGENTS)
      .filter((agent) => agent.default_enabled)
      .map((agent) => agent.id);
    const autoSources = (toolsCatalog?.sources || FALLBACK_SOURCES)
      .filter((source) => source.default_enabled)
      .map((source) => source.id);
    setToolConfig((prev) => ({
      ...prev,
      mode: "auto",
      enabled_agents: autoAgents,
      enabled_sources: autoSources,
    }));
  };

  const agentList = toolsCatalog?.agents || FALLBACK_AGENTS;
  const sourceList = toolsCatalog?.sources?.length ? toolsCatalog.sources : FALLBACK_SOURCES;

  const toggleAgent = (id: string) => {
    setToolConfig((prev) => {
      const enabled = new Set(prev.enabled_agents || []);
      if (enabled.has(id)) enabled.delete(id);
      else enabled.add(id);
      return { ...prev, mode: "manual", enabled_agents: [...enabled] };
    });
  };

  const toggleSource = (id: string) => {
    setToolConfig((prev) => {
      const enabled = new Set(prev.enabled_sources || []);
      if (enabled.has(id)) enabled.delete(id);
      else enabled.add(id);
      return { ...prev, mode: "manual", enabled_sources: [...enabled] };
    });
  };

  const Toggle = ({ enabled, onChange, label }: { enabled: boolean; onChange: () => void; label: string }) => (
    <label className="relative inline-flex h-6 w-11 shrink-0 cursor-pointer items-center">
      <input
        type="checkbox"
        className="peer sr-only"
        checked={enabled}
        onChange={onChange}
        aria-label={label}
      />
      <span
        aria-hidden="true"
        className="absolute inset-0 rounded-full border border-slate-600 bg-slate-700 transition-colors peer-checked:border-emerald-300 peer-checked:bg-secondary peer-focus-visible:outline peer-focus-visible:outline-2 peer-focus-visible:outline-secondary"
      />
      <span
        aria-hidden="true"
        className="relative z-10 ml-0.5 h-5 w-5 rounded-full bg-[var(--primary)] shadow-sm transition-transform peer-checked:translate-x-5"
      />
    </label>
  );

  if (toolsCollapsed) {
    return (
      <aside className="w-12 h-[calc(100vh-4rem)] sticky top-16 bg-[var(--bg-app)] border-l border-border-subtle flex flex-col items-center py-4 justify-between shrink-0">
        <button
          type="button"
          onClick={() => setToolsCollapsed(false)}
          title="Expand Tools & Connectors"
          className="p-2 rounded-lg hover:bg-[var(--bg-elevated)] text-on-surface-variant hover:text-[var(--text-primary)] transition-colors"
        >
          <span className="material-symbols-outlined text-[18px]">hub</span>
        </button>
        <span className="text-[9px] font-mono rotate-90 text-slate-500 whitespace-nowrap tracking-wider uppercase">
          TOOLS
        </span>
      </aside>
    );
  }

  return (
    <aside className="w-full lg:w-[24%] xl:w-[24%] h-[calc(100vh-4rem)] sticky top-16 bg-[var(--bg-app)] border-l border-border-subtle flex flex-col justify-between overflow-y-auto p-4 shrink-0 transition-all">
      <div className="space-y-5">
        {/* Sidebar Header */}
        <div className="flex items-center justify-between pb-2 border-b border-border-subtle">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-[var(--text-primary)] text-[17px]">hub</span>
            <span className="text-[11px] font-mono uppercase tracking-wider text-[var(--text-primary)] font-semibold">
              Tools &amp; Connectors
            </span>
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={() => refreshToolsCatalog()}
              className="p-1 text-on-surface-variant hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] rounded-full transition-colors"
              title="Refresh Connectors"
              type="button"
            >
              <span className={`material-symbols-outlined text-[15px] ${toolsLoading ? "animate-spin" : ""}`}>
                refresh
              </span>
            </button>
            <button
              onClick={() => setToolsCollapsed(true)}
              className="p-1 text-on-surface-variant hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] rounded-full transition-colors"
              title="Collapse Sidebar"
              type="button"
            >
              <span className="material-symbols-outlined text-[15px]">side_navigation</span>
            </button>
          </div>
        </div>

        {/* Auto Orchestration Status Card */}
        <div
          onClick={toggleOrchestration}
          className="bg-[var(--bg-surface)] p-3.5 border border-border-subtle hover:border-slate-600 rounded-2xl shadow-sm cursor-pointer transition-colors"
        >
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[11px] font-mono uppercase font-semibold text-[var(--text-primary)]">Auto Orchestration</span>
            <span
              className={`w-2 h-2 rounded-full ${
                isAuto ? "bg-secondary" : "bg-tertiary"
              }`}
            />
          </div>
          <p className="text-xs text-on-surface-variant leading-relaxed">
            {isAuto
              ? "Automatic agent routing per query active."
              : "Manual agent & source routing active."}
          </p>
        </div>

        {/* Active AI Agents List */}
        <div>
          <div className="text-[11px] font-mono uppercase tracking-wider text-on-surface-variant font-semibold mb-2 px-1">
            Active AI Agents
          </div>
          <div className="space-y-1.5">
            {agentList.map((agent) => {
              const enabled = toolConfig.enabled_agents?.includes(agent.id) ?? agent.default_enabled;
              return (
              <div
                key={agent.id}
                className="flex items-center justify-between px-3 py-2 bg-[var(--bg-surface)] border border-border-subtle rounded-xl text-xs"
              >
                <div className="min-w-0 pr-2">
                  <span className="block truncate text-[var(--text-primary)] font-medium">{agent.name}</span>
                  <span className="block truncate text-[10px] text-on-surface-variant">{agent.description}</span>
                </div>
                <Toggle enabled={enabled} onChange={() => toggleAgent(agent.id)} label={`Toggle ${agent.name}`} />
              </div>
              );
            })}
          </div>
        </div>

        {/* Data Source Connectors List */}
        <div>
          <div className="text-[11px] font-mono uppercase tracking-wider text-on-surface-variant font-semibold mb-2 px-1">
            Data Source Connectors
          </div>
          <div className="space-y-1.5">
            {sourceList.map((src) => {
              const enabled = toolConfig.enabled_sources?.includes(src.id) ?? src.default_enabled;
              return (
                <div
                  key={src.id}
                  className="flex items-center justify-between px-3 py-2 bg-[var(--bg-surface)] border border-border-subtle rounded-xl text-xs"
                >
                  <div className="min-w-0 pr-2">
                    <span className="block truncate text-[var(--text-primary)] font-medium">{src.name}</span>
                    <span className="block truncate text-[10px] text-on-surface-variant">
                      {src.requires_key ? `Uses ${src.requires_key}` : "No API key required"}
                    </span>
                  </div>
                  <Toggle enabled={enabled} onChange={() => toggleSource(src.id)} label={`Toggle ${src.name}`} />
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* System Telemetry Footer */}
      <div className="pt-3 border-t border-border-subtle text-center">
        <span className="text-[10px] font-mono tracking-wider text-slate-500 uppercase">
          SYSTEM TELEMETRY 99.98% OK
        </span>
      </div>
    </aside>
  );
}
