"use client";

// Verification is real, not decorative: the button calls the backend, which
// re-fetches the pinned record from IPFS, recomputes its SHA-256 and checks
// the local hash chain. A failure is reported as a failure - the previous
// version showed a green "verified" badge whenever the request threw, and
// substituted hardcoded dummy hashes when none were present.

import React, { useState } from "react";
import { verifyInsight, verifyProvenance } from "@/lib/api";
import type { ProvenanceVerifyResult } from "@/lib/api";
import type { NormalizedDashboardData } from "@/lib/adapter";

interface ProvenanceModuleProps {
  data: NormalizedDashboardData;
}

type VerifyState =
  | { kind: "idle" }
  | { kind: "done"; verified: boolean; message: string; mode: string; checked: boolean }
  | { kind: "error"; message: string };

export default function ProvenanceModule({ data }: ProvenanceModuleProps) {
  const { provenance } = data;
  const [verifying, setVerifying] = useState(false);
  const [state, setState] = useState<VerifyState>({ kind: "idle" });

  const canVerifyContent = Boolean(provenance.contentSha256);
  const canVerifyLedger = Boolean(provenance.insightHash && provenance.datasetHash);

  const handleVerify = async () => {
    setVerifying(true);
    setState({ kind: "idle" });
    try {
      if (canVerifyContent) {
        const res: ProvenanceVerifyResult = await verifyProvenance(
          provenance.contentSha256 as string,
          provenance.cid
        );
        setState({
          kind: "done",
          verified: res.verified,
          checked: res.checked,
          mode: res.mode,
          message: res.message,
        });
        return;
      }
      if (canVerifyLedger) {
        const res = await verifyInsight(provenance.insightHash as string, provenance.datasetHash as string);
        setState({
          kind: "done",
          verified: res.verified,
          checked: true,
          mode: "hash_chain",
          message: res.message,
        });
        return;
      }
      setState({
        kind: "error",
        message: "This insight carries no provenance hash, so there is nothing to verify.",
      });
    } catch (error) {
      setState({
        kind: "error",
        message: error instanceof Error ? error.message : "Verification request failed.",
      });
    } finally {
      setVerifying(false);
    }
  };

  const pinBadge = provenance.pinned ? (
    <span className="flex items-center gap-1.5 bg-secondary-container/30 text-secondary border border-secondary/30 px-2.5 py-0.5 rounded-full">
      <span className="material-symbols-outlined text-[12px]">cloud_done</span>
      <span className="font-mono text-[10px] font-bold">Pinned to IPFS</span>
    </span>
  ) : (
    <span className="flex items-center gap-1.5 bg-surface-high text-on-surface-variant border border-surface-border/60 px-2.5 py-0.5 rounded-full">
      <span className="material-symbols-outlined text-[12px]">cloud_off</span>
      <span className="font-mono text-[10px] font-bold">Hash Chain Only</span>
    </span>
  );

  const resultTone =
    state.kind === "error"
      ? "bg-amber-500/10 border-amber-500/30 text-amber-300"
      : state.kind === "done" && state.verified
        ? "bg-secondary-container/20 border-secondary/40 text-secondary"
        : "bg-red-500/10 border-red-500/30 text-red-300";

  return (
    <div className="lg:col-span-6 bg-surface border border-surface-border/60 rounded-2xl flex flex-col overflow-hidden shadow-sm">
      <div className="flex items-center justify-between px-4 py-3 bg-surface-high/60 border-b border-surface-border/50">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-[18px] text-secondary">
            verified_user
          </span>
          <span className="font-mono text-xs uppercase text-on-surface font-bold tracking-wider">
            Verification &amp; Provenance
          </span>
        </div>
        <div className="flex items-center gap-1.5">{pinBadge}</div>
      </div>

      <div className="p-4 flex flex-col justify-between flex-1 gap-3">
        <div className="space-y-1.5 font-mono text-[11px]">
          <div className="flex items-center justify-between p-2.5 bg-surface-lowest border border-surface-border/70 rounded-xl">
            <span className="text-on-surface-variant">Dataset Snapshot</span>
            <span className="text-on-surface font-semibold">{provenance.datasetSnapshot}</span>
          </div>

          <div className="flex items-center justify-between p-2.5 bg-surface-lowest border border-surface-border/70 rounded-xl">
            <span className="text-on-surface-variant">Timestamp ISO-8601</span>
            <span className="text-on-surface">{provenance.timestamp}</span>
          </div>

          <div className="flex items-center justify-between p-2.5 bg-surface-lowest border border-surface-border/70 rounded-xl">
            <span className="text-on-surface-variant">Orchestrator Pipeline</span>
            <span className="text-[var(--text-primary)] font-semibold">{provenance.pipeline}</span>
          </div>

          <div className="flex items-center justify-between p-2.5 bg-surface-lowest border border-surface-border/70 rounded-xl">
            <span className="text-on-surface-variant">Blockchain Anchoring</span>
            <span className="text-secondary font-semibold">{provenance.blockchainAnchoring}</span>
          </div>

          {provenance.contentSha256 && (
            <div className="flex items-center justify-between p-2.5 bg-surface-lowest border border-surface-border/70 rounded-xl">
              <span className="text-on-surface-variant">Content SHA-256</span>
              <span className="text-on-surface">
                {provenance.contentSha256.slice(0, 16)}…
              </span>
            </div>
          )}

          {provenance.cid && (
            <div className="flex items-center justify-between p-2.5 bg-surface-lowest border border-surface-border/70 rounded-xl">
              <span className="text-on-surface-variant">IPFS CID</span>
              <span className="text-on-surface" title={provenance.cid}>
                {provenance.cid.slice(0, 16)}…
              </span>
            </div>
          )}
        </div>

        {state.kind !== "idle" && (
          <div className={`p-2.5 rounded-xl border text-xs font-mono ${resultTone}`}>
            {state.message}
            {state.kind === "done" && (
              <div className="mt-1 text-[10px] uppercase opacity-80">
                mode: {state.mode}
                {state.verified ? " · content hash matched" : state.checked ? " · mismatch detected" : " · not checked"}
              </div>
            )}
          </div>
        )}

        <button
          type="button"
          onClick={handleVerify}
          disabled={verifying || (!canVerifyContent && !canVerifyLedger)}
          className="w-full flex items-center justify-center gap-2 bg-surface-high hover:bg-surface-highest border border-surface-border text-[var(--text-primary)] px-4 py-2.5 rounded-xl font-mono text-xs transition-colors font-bold disabled:opacity-50"
        >
          <span className={`material-symbols-outlined text-[16px] ${verifying ? "animate-spin" : ""}`}>
            {verifying ? "progress_activity" : "fingerprint"}
          </span>
          <span>
            {verifying
              ? "Verifying Provenance..."
              : provenance.pinned
                ? "Re-fetch from IPFS & Verify SHA-256"
                : "Verify Against Local Hash Chain"}
          </span>
        </button>
      </div>
    </div>
  );
}
