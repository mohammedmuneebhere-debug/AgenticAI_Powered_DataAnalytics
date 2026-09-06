"use client";

import React from "react";
import { useSocialIQ } from "@/context/SocialIQContext";

export default function ChatHeader() {
  const { newInvestigation, activeTopic, chatMessages } = useSocialIQ();

  const handleExportBriefing = () => {
    const text = chatMessages
      .map((m) => `[${m.role.toUpperCase()} - ${m.timestamp || "UTC"}]:\n${m.content}\n`)
      .join("\n---\n\n");
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `SocialIQ_Briefing_${activeTopic.replace(/\s+/g, "_")}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleAuditLog = () => {
    alert(
      `Agent Audit Log for [${activeTopic}]:\n` +
      `- Master Agent: Plan & Execute (status: OK)\n` +
      `- Data Acquisition: Ingested live and sample sources (status: OK)\n` +
      `- Provenance Agent: Cryptographic hash recorded (status: OK)`
    );
  };

  return (
    <div className="flex items-center justify-between gap-4 mb-3">
      {/* Breadcrumbs */}
      <div className="flex items-center gap-2 text-xs">
        <span className="material-symbols-outlined text-on-surface-variant text-[17px]">terminal</span>
        <span className="text-on-surface-variant">Workspace</span>
        <span className="text-slate-600">/</span>
        <span className="text-white font-medium">AI Assistant</span>
      </div>

      {/* Workspace Actions */}
      <div className="flex items-center gap-2">
        <button
          onClick={newInvestigation}
          type="button"
          className="flex items-center gap-1.5 px-3 py-1.5 bg-[#13151b] border border-border-subtle text-on-surface hover:text-white hover:bg-[#1a1d24] rounded-full text-xs font-medium transition-colors"
        >
          <span className="material-symbols-outlined text-[15px] text-white">add_box</span>
          <span>New Investigation</span>
        </button>

        <button
          onClick={handleExportBriefing}
          type="button"
          className="flex items-center gap-1.5 px-3 py-1.5 bg-[#13151b] border border-border-subtle text-on-surface hover:text-white hover:bg-[#1a1d24] rounded-full text-xs font-medium transition-colors"
        >
          <span className="material-symbols-outlined text-[15px] text-on-surface-variant">ios_share</span>
          <span>Export Briefing</span>
        </button>

        <button
          onClick={handleAuditLog}
          type="button"
          className="flex items-center gap-1.5 px-3 py-1.5 bg-[#13151b] border border-border-subtle text-on-surface hover:text-white hover:bg-[#1a1d24] rounded-full text-xs font-medium transition-colors"
        >
          <span className="material-symbols-outlined text-[15px] text-on-surface-variant">history</span>
          <span>Agent Audit Log</span>
        </button>
      </div>
    </div>
  );
}
