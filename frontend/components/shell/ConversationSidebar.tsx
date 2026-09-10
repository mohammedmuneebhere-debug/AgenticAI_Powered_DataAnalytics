"use client";

import React from "react";
import { MessageSquare, PanelLeft, PanelLeftClose, Plus, Trash2 } from "lucide-react";
import { useSocialIQ } from "@/context/SocialIQContext";
import { deleteSession } from "@/lib/api";
import { DEMO_SESSION_ID } from "@/lib/constants";

export default function ConversationSidebar() {
  const {
    sessionId,
    sessions,
    sessionsLoading,
    refreshSessions,
    loadSession,
    newInvestigation,
  } = useSocialIQ();
  const [collapsed, setCollapsed] = React.useState(false);

  const handleDelete = async (event: React.MouseEvent, id: string) => {
    event.stopPropagation();
    if (id === DEMO_SESSION_ID) return;
    await deleteSession(id);
    if (sessionId === id) newInvestigation();
    await refreshSessions();
  };

  if (collapsed) {
    return (
      <aside className="w-12 shrink-0 border-r border-border-subtle bg-[var(--bg-sidebar)] flex flex-col items-center gap-3 py-4">
        <button
          type="button"
          onClick={() => setCollapsed(false)}
          className="rounded-lg p-2 text-on-surface-variant hover:bg-[var(--bg-elevated)] hover:text-[var(--text-primary)]"
          title="Expand conversation history"
        >
          <PanelLeft size={18} />
        </button>
        <button
          type="button"
          onClick={newInvestigation}
          className="rounded-lg p-2 text-secondary hover:bg-[var(--bg-elevated)]"
          title="New investigation"
        >
          <Plus size={18} />
        </button>
      </aside>
    );
  }

  return (
    <aside className="w-64 shrink-0 border-r border-border-subtle bg-[var(--bg-sidebar)] flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-border-subtle px-4 py-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-[var(--text-primary)]">Conversations</p>
          <p className="mt-1 text-[10px] text-on-surface-variant">Investigation history</p>
        </div>
        <button
          type="button"
          onClick={() => setCollapsed(true)}
          className="rounded-lg p-1.5 text-on-surface-variant hover:bg-[var(--bg-elevated)] hover:text-[var(--text-primary)]"
          title="Collapse conversation history"
        >
          <PanelLeftClose size={17} />
        </button>
      </div>

      <div className="p-3">
        <button
          type="button"
          onClick={newInvestigation}
          className="flex w-full items-center justify-center gap-2 rounded-xl border border-border-subtle px-3 py-2 text-xs font-semibold text-[var(--text-primary)] transition-colors hover:bg-[var(--bg-elevated)]"
        >
          <Plus size={15} />
          New investigation
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-2 pb-4">
        {sessionsLoading && <p className="px-3 py-2 text-xs text-on-surface-variant">Loading history...</p>}
        {!sessionsLoading && sessions.length === 0 && (
          <p className="px-3 py-2 text-xs text-on-surface-variant">No conversations yet.</p>
        )}
        {sessions.map((session) => (
          <div
            key={session.id}
            role="button"
            tabIndex={0}
            onClick={() => void loadSession(session.id)}
            onKeyDown={(event) => {
              if (event.key === "Enter" || event.key === " ") void loadSession(session.id);
            }}
            className={`group mb-1 flex cursor-pointer items-start gap-2 rounded-xl px-3 py-2.5 text-left transition-colors ${
              sessionId === session.id ? "bg-[var(--bg-elevated)]" : "hover:bg-[var(--bg-surface)]"
            }`}
          >
            <MessageSquare size={15} className="mt-0.5 shrink-0 text-on-surface-variant" />
            <div className="min-w-0 flex-1">
              <p className="truncate text-xs font-medium text-[var(--text-primary)]">{session.title || "Untitled investigation"}</p>
              <p className="mt-1 text-[10px] text-on-surface-variant">
                {session.message_count} {session.message_count === 1 ? "message" : "messages"}
              </p>
            </div>
            <button
              type="button"
              onClick={(event) => void handleDelete(event, session.id)}
              disabled={session.id === DEMO_SESSION_ID}
              className="shrink-0 rounded p-1 text-on-surface-variant opacity-0 transition-opacity hover:bg-[var(--bg-app)] hover:text-error group-hover:opacity-100"
              title="Delete conversation"
            >
              <Trash2 size={13} />
            </button>
          </div>
        ))}
      </div>
    </aside>
  );
}
