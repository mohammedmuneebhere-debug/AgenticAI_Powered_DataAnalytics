"use client";

import { useEffect, useState } from "react";
import {
  Plus, MessageSquare, Trash2, PanelLeftClose, PanelLeft,
  Coffee, TrendingUp, Smartphone, Search,
} from "lucide-react";
import { listSessions, createSession, deleteSession, type SessionSummary } from "@/lib/api";
import { DOMAIN_COLORS } from "@/lib/constants";

const DOMAIN_ICON: Record<string, React.ReactNode> = {
  consumer: <Coffee size={14} />,
  financial: <TrendingUp size={14} />,
  creator: <Smartphone size={14} />,
  general: <Search size={14} />,
};

interface Props {
  activeSessionId?: string;
  onSelectSession: (id: string) => void;
  onNewChat: () => void;
  collapsed: boolean;
  onToggleCollapse: () => void;
}

export default function Sidebar({ activeSessionId, onSelectSession, onNewChat, collapsed, onToggleCollapse }: Props) {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);

  const refresh = () => listSessions().then(setSessions).catch(() => {});

  useEffect(() => { refresh(); }, [activeSessionId]);

  const handleNew = async () => {
    onNewChat();
    refresh();
  };

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    await deleteSession(id);
    refresh();
    if (activeSessionId === id) onNewChat();
  };

  if (collapsed) {
    return (
      <div className="w-14 flex flex-col items-center py-3 gap-3 border-r border-[var(--border-subtle)] bg-[var(--bg-sidebar)]">
        <button onClick={onToggleCollapse} className="p-2 rounded-lg hover:bg-[var(--bg-surface)] text-[var(--text-secondary)]">
          <PanelLeft size={20} />
        </button>
        <button onClick={handleNew} className="p-2 rounded-lg hover:bg-[var(--bg-surface)] text-[var(--accent)]">
          <Plus size={20} />
        </button>
      </div>
    );
  }

  return (
    <aside className="w-[var(--sidebar-width)] flex flex-col border-r border-[var(--border-subtle)] bg-[var(--bg-sidebar)] h-full">
      <div className="flex items-center justify-between px-4 py-4 border-b border-[var(--border-subtle)]">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#4285f4] to-[#8ab4f8] flex items-center justify-center text-white text-xs font-bold">S</div>
          <div>
            <h1 className="text-sm font-medium text-[var(--text-primary)]">SOCIALIQ</h1>
            <p className="text-[10px] text-[var(--text-muted)]">Enterprise Intelligence</p>
          </div>
        </div>
        <button onClick={onToggleCollapse} className="p-1.5 rounded-lg hover:bg-[var(--bg-surface)] text-[var(--text-secondary)]">
          <PanelLeftClose size={18} />
        </button>
      </div>

      <div className="p-3">
        <button
          onClick={handleNew}
          className="w-full flex items-center gap-2 px-4 py-2.5 rounded-full border border-[var(--border)] hover:bg-[var(--bg-surface)] text-sm text-[var(--text-primary)] transition-colors"
        >
          <Plus size={16} />
          New chat
        </button>
      </div>

      <div className="flex-1 overflow-y-auto sidebar-scroll px-2 pb-4">
        <p className="px-3 py-2 text-[11px] font-medium text-[var(--text-muted)] uppercase tracking-wider">Recent</p>
        {sessions.length === 0 && (
          <p className="px-3 text-xs text-[var(--text-muted)]">No conversations yet</p>
        )}
        {sessions.map((s) => (
          <button
            key={s.id}
            onClick={() => onSelectSession(s.id)}
            className={`w-full group flex items-start gap-2.5 px-3 py-2.5 rounded-xl text-left transition-colors mb-0.5 ${
              activeSessionId === s.id
                ? "bg-[var(--bg-elevated)]"
                : "hover:bg-[var(--bg-surface)]"
            }`}
          >
            <MessageSquare size={16} className="mt-0.5 shrink-0 text-[var(--text-muted)]" />
            <div className="flex-1 min-w-0">
              <p className="text-sm text-[var(--text-primary)] truncate">{s.title}</p>
              {s.domain && (
                <span
                  className="inline-flex items-center gap-1 text-[10px] mt-0.5"
                  style={{ color: DOMAIN_COLORS[s.domain] || DOMAIN_COLORS.general }}
                >
                  {DOMAIN_ICON[s.domain]} {s.domain}
                </span>
              )}
            </div>
            <button
              onClick={(e) => handleDelete(e, s.id)}
              className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-[var(--bg-app)] text-[var(--text-muted)] shrink-0"
            >
              <Trash2 size={13} />
            </button>
          </button>
        ))}
      </div>
    </aside>
  );
}
