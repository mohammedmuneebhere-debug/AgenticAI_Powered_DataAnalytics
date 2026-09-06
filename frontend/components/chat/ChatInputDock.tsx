"use client";

import React, { useRef, useEffect } from "react";

interface ChatInputDockProps {
  input: string;
  setInput: (v: string) => void;
  onSend: (text?: string) => void;
  loading: boolean;
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
    <div className="mt-4 pt-3 border-t border-border-subtle bg-[#090a0f]">
      <div className="max-w-4xl mx-auto w-full flex flex-col gap-2.5">
        <div className="w-full bg-[#13151b] border border-border-subtle hover:border-slate-500/50 focus-within:border-white/30 rounded-2xl p-3.5 transition-all shadow-sm flex flex-col gap-2.5">
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
              className="w-full bg-transparent border-0 p-0 text-[14px] text-white placeholder:text-slate-500 focus:outline-none focus:ring-0 resize-none font-sans leading-relaxed py-1"
            />
            <button
              id="send-btn"
              type="button"
              onClick={() => onSend()}
              disabled={loading || !input.trim()}
              className="w-8 h-8 rounded-full bg-white text-black hover:bg-slate-200 disabled:opacity-40 disabled:hover:bg-white flex items-center justify-center transition-all shadow-sm shrink-0"
              title="Send query"
            >
              <span className={`material-symbols-outlined text-[18px] font-semibold ${loading ? "animate-spin" : ""}`}>
                {loading ? "progress_activity" : "arrow_upward"}
              </span>
            </button>
          </div>
        </div>

        {/* Bottom Disclaimer */}
        <div className="flex items-center justify-between px-2 text-[11px] text-slate-500 font-mono flex-wrap gap-1">
          <span>SOCIALIQ can make mistakes. Verify important intelligence against source provenance.</span>
          <span className="uppercase">STRICT ZERO RETENTION SANDBOX ACTIVE</span>
        </div>
      </div>
    </div>
  );
}
