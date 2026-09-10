"use client";

import React, { useEffect, useRef, useState } from "react";
import { useSocialIQ } from "@/context/SocialIQContext";
import type { AvailableModel } from "@/lib/api";

interface ChatInputDockProps {
  input: string;
  setInput: (v: string) => void;
  onSend: (text?: string) => void;
  loading: boolean;
}

function providerIcon(provider: AvailableModel["provider"]): string {
  return provider === "ollama" ? "memory" : "auto_awesome";
}

function ModelSelector() {
  const { llmModels, selectedModel, setSelectedModel, refreshLLMModels } = useSocialIQ();
  const [open, setOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const close = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, []);

  const current = llmModels?.models.find((m) => m.id === selectedModel);

  if (!llmModels || llmModels.models.length === 0) {
    return null;
  }

  return (
    <div className="relative" ref={menuRef}>
      <button
        type="button"
        onClick={() => {
          setOpen((prev) => !prev);
          if (!open) void refreshLLMModels();
        }}
        title="Select intelligence model"
        className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-[11px] font-mono text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--border)] transition-colors"
      >
        <span className="material-symbols-outlined text-[14px] text-[var(--secondary)]">
          {current ? providerIcon(current.provider) : "neurology"}
        </span>
        <span className="max-w-[160px] truncate">{current?.label ?? "Default model"}</span>
        <span className="material-symbols-outlined text-[14px]">expand_more</span>
      </button>

      {open && (
        <div className="absolute bottom-9 left-0 w-64 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] shadow-xl py-1.5 z-50">
          <p className="px-3 py-1.5 text-[10px] font-mono uppercase tracking-wider text-[var(--text-muted)]">
            Intelligence model
          </p>
          {llmModels.models.map((model) => (
            <button
              key={model.id}
              type="button"
              onClick={() => {
                setSelectedModel(model.id);
                setOpen(false);
              }}
              className={`w-full flex items-center gap-2.5 px-3 py-2 text-left text-xs transition-colors ${
                model.id === selectedModel
                  ? "bg-[var(--bg-elevated)] text-[var(--text-primary)]"
                  : "text-[var(--text-secondary)] hover:bg-[var(--bg-elevated)] hover:text-[var(--text-primary)]"
              }`}
            >
              <span className="material-symbols-outlined text-[16px] text-[var(--secondary)]">
                {providerIcon(model.provider)}
              </span>
              <span className="flex-1 truncate">{model.label}</span>
              {model.id === selectedModel && (
                <span className="material-symbols-outlined text-[15px] text-[var(--secondary)]">check</span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default function ChatInputDock({ input, setInput, onSend, loading }: ChatInputDockProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [input]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (input.trim() && !loading) {
        onSend();
      }
    }
  };

  return (
    <div className="mt-4 pt-3 border-t border-[var(--border-subtle)] bg-[var(--bg-app)]">
      <div className="max-w-4xl mx-auto w-full flex flex-col gap-2.5">
        <div className="w-full bg-[var(--bg-surface)] border border-[var(--border-subtle)] hover:border-[var(--border)] focus-within:border-[var(--border)] rounded-2xl p-3.5 transition-all shadow-sm flex flex-col gap-2.5">
          <div className="flex items-center gap-3 w-full">
            <textarea
              id="chat-input-query"
              ref={textareaRef}
              rows={1}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={loading}
              placeholder="Ask SocialIQ anything or pivot context..."
              className="w-full bg-transparent border-0 p-0 text-[14px] text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:ring-0 resize-none font-sans leading-relaxed py-1"
            />
            <button
              id="send-btn"
              type="button"
              onClick={() => onSend()}
              disabled={loading || !input.trim()}
              className="w-8 h-8 rounded-full bg-[var(--primary)] text-[var(--on-primary)] hover:bg-[var(--primary-hover)] disabled:opacity-40 flex items-center justify-center transition-all shadow-sm shrink-0"
              title="Send query"
            >
              <span className={`material-symbols-outlined text-[18px] font-semibold ${loading ? "animate-spin" : ""}`}>
                {loading ? "progress_activity" : "arrow_upward"}
              </span>
            </button>
          </div>
          <div className="flex items-center justify-between">
            <ModelSelector />
            <span />
          </div>
        </div>

        {/* Bottom Disclaimer */}
        <div className="flex items-center justify-between px-2 text-[11px] text-[var(--text-muted)] font-mono flex-wrap gap-1">
          <span>SOCIALIQ can make mistakes. Verify important intelligence against source provenance.</span>
          <span className="uppercase">STRICT ZERO RETENTION SANDBOX ACTIVE</span>
        </div>
      </div>
    </div>
  );
}
