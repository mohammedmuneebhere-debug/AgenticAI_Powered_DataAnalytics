"use client";

import { useEffect, useState } from "react";
import { Settings2, Zap, Plug, PanelRightClose, PanelRight, RefreshCw } from "lucide-react";
import { getTools, type AgentTool, type DataSource, type ToolConfig } from "@/lib/api";
import { DEFAULT_AGENTS, DEFAULT_SOURCES, FALLBACK_SOURCES, SOURCE_ICONS } from "@/lib/constants";

interface Props {
  config: ToolConfig;
  onChange: (config: ToolConfig) => void;
  collapsed: boolean;
  onToggleCollapse: () => void;
}

function Toggle({ on, onToggle }: { on: boolean; onToggle: () => void }) {
  return (
    <button
      onClick={onToggle}
      className={`toggle-track relative w-9 h-5 rounded-full ${on ? "on" : "off"}`}
    >
      <span className={`absolute top-0.5 w-4 h-4 rounded-full bg-[var(--primary)] transition-transform ${on ? "left-[18px]" : "left-0.5"}`} />
    </button>
  );
}

/** Merge API sources with fallback so new connectors always appear in UI */
function mergeSources(apiSources: DataSource[]): DataSource[] {
  const byId = new Map<string, DataSource>();
  for (const s of FALLBACK_SOURCES) {
    byId.set(s.id, s as DataSource);
  }
  for (const s of apiSources) {
    byId.set(s.id, s);
  }
  return Array.from(byId.values());
}

export default function ToolsPanel({ config, onChange, collapsed, onToggleCollapse }: Props) {
  const [agents, setAgents] = useState<AgentTool[]>([]);
  const [sources, setSources] = useState<DataSource[]>(FALLBACK_SOURCES as DataSource[]);
  const [loading, setLoading] = useState(true);

  const loadTools = () => {
    setLoading(true);
    getTools()
      .then((c) => {
        setAgents(c.agents);
        setSources(mergeSources(c.sources));
      })
      .catch(() => {
        setSources(FALLBACK_SOURCES as DataSource[]);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadTools(); }, []);

  const isAuto = config.mode === "auto";
  const enabledAgents = config.enabled_agents ?? DEFAULT_AGENTS;
  const enabledSources = config.enabled_sources ?? DEFAULT_SOURCES;

  const toggleAgent = (id: string) => {
    if (isAuto) return;
    const next = enabledAgents.includes(id)
      ? enabledAgents.filter((a) => a !== id)
      : [...enabledAgents, id];
    onChange({ ...config, enabled_agents: next });
  };

  const toggleSource = (id: string) => {
    if (isAuto) return;
    const next = enabledSources.includes(id)
      ? enabledSources.filter((s) => s !== id)
      : [...enabledSources, id];
    onChange({ ...config, enabled_sources: next });
  };

  if (collapsed) {
    return (
      <div className="w-14 flex flex-col items-center py-3 gap-3 border-l border-[var(--border-subtle)] bg-[var(--bg-sidebar)]">
        <button onClick={onToggleCollapse} className="p-2 rounded-lg hover:bg-[var(--bg-surface)] text-[var(--text-secondary)]">
          <PanelRight size={20} />
        </button>
        <Settings2 size={20} className="text-[var(--text-muted)]" />
      </div>
    );
  }

  return (
    <aside className="w-[var(--tools-width)] flex flex-col border-l border-[var(--border-subtle)] bg-[var(--bg-sidebar)] h-full">
      <div className="flex items-center justify-between px-4 py-4 border-b border-[var(--border-subtle)]">
        <div className="flex items-center gap-2">
          <Settings2 size={18} className="text-[var(--accent)]" />
          <h2 className="text-sm font-medium">Tools & Connectors</h2>
        </div>
        <div className="flex items-center gap-1">
          <button onClick={loadTools} title="Refresh" className="p-1.5 rounded-lg hover:bg-[var(--bg-surface)] text-[var(--text-secondary)]">
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
          </button>
          <button onClick={onToggleCollapse} className="p-1.5 rounded-lg hover:bg-[var(--bg-surface)] text-[var(--text-secondary)]">
            <PanelRightClose size={18} />
          </button>
        </div>
      </div>

      <div className="px-4 py-3 border-b border-[var(--border-subtle)]">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <Zap size={14} className="text-[var(--accent)]" />
            <span className="text-xs font-medium">Orchestration</span>
          </div>
          <Toggle
            on={isAuto}
            onToggle={() => onChange({
              ...config,
              mode: isAuto ? "manual" : "auto",
              enabled_agents: isAuto ? DEFAULT_AGENTS : enabledAgents,
              enabled_sources: isAuto ? DEFAULT_SOURCES : enabledSources,
            })}
          />
        </div>
        <p className="text-[11px] text-[var(--text-muted)]">
          {isAuto ? "Automatic — SOCIALIQ selects agents per query" : "Manual — you choose agents & sources"}
        </p>
      </div>

      <div className="flex-1 overflow-y-auto sidebar-scroll px-4 py-3">
        <div className="flex items-center gap-2 mb-3">
          <Plug size={14} className="text-[var(--text-muted)]" />
          <span className="text-[11px] font-medium text-[var(--text-muted)] uppercase tracking-wider">Agents</span>
        </div>
        <div className="space-y-1.5 mb-5">
          {agents.map((a) => {
            const active = enabledAgents.includes(a.id);
            return (
              <button
                key={a.id}
                onClick={() => toggleAgent(a.id)}
                disabled={isAuto}
                className={`tool-chip w-full text-left px-3 py-2 rounded-lg border text-xs ${active ? "active" : "inactive"} ${isAuto ? "opacity-60 cursor-default" : "cursor-pointer"}`}
              >
                <p className="font-medium">{a.name}</p>
                <p className="text-[10px] mt-0.5 opacity-70">{a.description}</p>
              </button>
            );
          })}
        </div>

        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Plug size={14} className="text-[var(--text-muted)]" />
            <span className="text-[11px] font-medium text-[var(--text-muted)] uppercase tracking-wider">Data Sources</span>
          </div>
          <span className="text-[10px] text-[var(--text-muted)]">{sources.length} connectors</span>
        </div>
        <div className="space-y-1.5">
          {sources.map((s) => {
            const active = isAuto ? (s.default_enabled ?? true) : enabledSources.includes(s.id);
            const icon = SOURCE_ICONS[s.id] ?? "link";
            return (
              <button
                key={s.id}
                onClick={() => toggleSource(s.id)}
                disabled={isAuto}
                className={`tool-chip w-full text-left px-3 py-2 rounded-lg border text-xs ${active ? "active" : "inactive"} ${isAuto ? "opacity-80 cursor-default" : "cursor-pointer"}`}
              >
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-[16px] leading-none">{icon}</span>
                  <p className="font-medium">{s.name}</p>
                </div>
                <p className="text-[10px] mt-1 ml-6 opacity-70">{s.description}</p>
                {s.requires_key && (
                  <p className="text-[10px] mt-0.5 ml-6 text-[var(--warning)]">Requires API key</p>
                )}
                {!s.requires_key && s.id === "sample" && (
                  <p className="text-[10px] mt-0.5 ml-6 text-[var(--success)]">Always available</p>
                )}
              </button>
            );
          })}
        </div>
      </div>
    </aside>
  );
}
