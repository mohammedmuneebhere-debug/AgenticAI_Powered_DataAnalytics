"use client";

import React, { useMemo, useState } from "react";
import type { NormalizedDashboardData, RelevantPostItem } from "@/lib/adapter";
import { apiFetch } from "@/lib/api";

interface RelevantPostsModuleProps {
  data: NormalizedDashboardData;
}

// Abstract grey SVG logos for each platform
const PlatformLogo = ({ platform, size = 14 }: { platform: string; size?: number }) => {
  const s = size;
  switch (platform) {
    case "x":
    case "x_scraper":
      return (
        <svg width={s} height={s} viewBox="0 0 24 24" fill="currentColor">
          <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231-5.401 6.231H2.744l7.73-8.835L1.254 2.25H8.08l4.253 5.622zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
        </svg>
      );
    case "instagram":
      return (
        <svg width={s} height={s} viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z" />
        </svg>
      );
    case "linkedin":
      return (
        <svg width={s} height={s} viewBox="0 0 24 24" fill="currentColor">
          <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
        </svg>
      );
    case "youtube":
      return (
        <svg width={s} height={s} viewBox="0 0 24 24" fill="currentColor">
          <path d="M23.498 6.186a3.016 3.016 0 00-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 00.502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 002.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 002.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" />
        </svg>
      );
    case "tiktok":
      return (
        <svg width={s} height={s} viewBox="0 0 24 24" fill="currentColor">
          <path d="M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.15 1.07-.14 1.61.24 1.64 1.82 3.02 3.5 2.87 1.12-.01 2.19-.66 2.77-1.61.19-.33.4-.67.41-1.06.1-1.79.06-3.57.07-5.36.01-4.03-.01-8.05.02-12.07z" />
        </svg>
      );
    case "facebook":
      return (
        <svg width={s} height={s} viewBox="0 0 24 24" fill="currentColor">
          <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
        </svg>
      );
    case "threads":
      return (
        <svg width={s} height={s} viewBox="0 0 24 24" fill="currentColor">
          <path d="M12.186 24h-.007c-3.581-.024-6.334-1.205-8.184-3.509C2.35 18.44 1.5 15.586 1.472 12.01v-.017c.03-3.579.879-6.43 2.525-8.482C5.845 1.205 8.6.024 12.18 0h.014c2.746.02 5.043.725 6.826 2.098 1.677 1.29 2.859 3.13 3.513 5.474l-2.495.684c-1.101-4.01-3.828-6.013-8.845-6.044-2.909.016-5.11.753-6.539 2.18-1.544 1.54-2.325 3.915-2.348 7.059.023 3.143.804 5.52 2.348 7.058 1.428 1.428 3.63 2.166 6.54 2.181 2.619-.016 4.334-.664 5.556-2.081 1.357-1.579 1.802-3.908 1.357-7.109-.114-.815-.297-1.478-.534-1.977a3.5 3.5 0 00-1.017-1.349c-.17 1.091-.427 2.027-.799 2.786-.65 1.325-1.641 2.065-2.966 2.215-1.082.122-2.067-.174-2.794-.847-.75-.694-1.144-1.69-1.112-2.796.06-2.047 1.469-3.667 3.617-4.192.79-.194 1.65-.24 2.525-.14.077.009.15.02.224.032.207-.79.24-1.632.098-2.531-.178-1.11-.647-1.936-1.405-2.476-.771-.55-1.778-.82-2.978-.82-.064 0-.127.001-.19.002-2.047.021-3.598.723-4.705 2.143-.842 1.09-1.259 2.582-1.259 4.476 0 4.048 1.897 6.455 5.647 6.455 1.283 0 2.302-.336 3.11-.997.826-.68 1.355-1.671 1.611-2.99l2.478.475c-.367 1.924-1.218 3.404-2.51 4.406-1.266.98-2.895 1.491-4.689 1.491z" />
        </svg>
      );
    case "reddit":
      return (
        <svg width={s} height={s} viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0zm5.01 4.744c.688 0 1.25.561 1.25 1.249a1.25 1.25 0 0 1-2.498.056l-2.597-.547-.8 3.747c1.824.07 3.48.632 4.674 1.488.308-.309.73-.491 1.207-.491.968 0 1.754.786 1.754 1.754 0 .716-.435 1.333-1.01 1.614a3.111 3.111 0 0 1 .042.52c0 2.694-3.13 4.87-7.004 4.87-3.874 0-7.004-2.176-7.004-4.87 0-.183.015-.366.043-.534A1.748 1.748 0 0 1 4.028 12c0-.968.786-1.754 1.754-1.754.463 0 .898.196 1.207.49 1.207-.883 2.878-1.43 4.744-1.487l.885-4.182a.342.342 0 0 1 .14-.197.35.35 0 0 1 .238-.042l2.906.617a1.214 1.214 0 0 1 1.108-.701zM9.25 12C8.561 12 8 12.562 8 13.25c0 .687.561 1.248 1.25 1.248.687 0 1.248-.561 1.248-1.249 0-.688-.561-1.249-1.249-1.249zm5.5 0c-.687 0-1.248.561-1.248 1.25 0 .687.561 1.248 1.249 1.248.688 0 1.249-.561 1.249-1.249 0-.687-.562-1.249-1.25-1.249zm-5.466 3.99a.327.327 0 0 0-.231.094.33.33 0 0 0 0 .463c.842.842 2.484.913 2.961.913.477 0 2.105-.056 2.961-.913a.361.361 0 0 0 .029-.463.33.33 0 0 0-.464 0c-.547.533-1.684.73-2.512.73-.828 0-1.979-.196-2.512-.73a.326.326 0 0 0-.232-.095z" />
        </svg>
      );
    case "telegram":
      return (
        <svg width={s} height={s} viewBox="0 0 24 24" fill="currentColor">
          <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.96 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z" />
        </svg>
      );
    case "pinterest":
      return (
        <svg width={s} height={s} viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 0C5.373 0 0 5.372 0 12c0 5.084 3.163 9.426 7.627 11.174-.105-.949-.2-2.405.042-3.441.218-.937 1.407-5.965 1.407-5.965s-.359-.719-.359-1.782c0-1.668.967-2.914 2.171-2.914 1.023 0 1.518.769 1.518 1.69 0 1.029-.655 2.568-.994 3.995-.283 1.194.599 2.169 1.777 2.169 2.133 0 3.772-2.249 3.772-5.495 0-2.873-2.064-4.882-5.012-4.882-3.414 0-5.418 2.561-5.418 5.207 0 1.031.397 2.138.893 2.738a.36.36 0 0 1 .083.345l-.333 1.36c-.053.22-.174.267-.402.161-1.499-.698-2.436-2.889-2.436-4.649 0-3.785 2.75-7.262 7.929-7.262 4.163 0 7.398 2.967 7.398 6.931 0 4.136-2.607 7.464-6.227 7.464-1.216 0-2.359-.632-2.75-1.378l-.748 2.853c-.271 1.043-1.002 2.35-1.492 3.146C9.57 23.812 10.763 24 12 24c6.627 0 12-5.373 12-12S18.627 0 12 0z" />
        </svg>
      );
    default:
      return (
        <svg width={s} height={s} viewBox="0 0 24 24" fill="currentColor">
          <circle cx="12" cy="12" r="10" strokeWidth="1.5" stroke="currentColor" fill="none"/>
          <line x1="12" y1="2" x2="12" y2="22" stroke="currentColor" strokeWidth="1.5"/>
          <line x1="2" y1="12" x2="22" y2="12" stroke="currentColor" strokeWidth="1.5"/>
        </svg>
      );
  }
};

const PLATFORM_META: Record<string, { label: string }> = {
  x: { label: "X / Twitter" },
  x_scraper: { label: "X / Twitter" },
  instagram: { label: "Instagram" },
  linkedin: { label: "LinkedIn" },
  youtube: { label: "YouTube" },
  tiktok: { label: "TikTok" },
  facebook: { label: "Facebook" },
  threads: { label: "Threads" },
  pinterest: { label: "Pinterest" },
  reddit: { label: "Reddit" },
  telegram: { label: "Telegram" },
  synthetic: { label: "Simulated" },
};

const PLATFORM_ORDER = [
  "x", "x_scraper", "instagram", "linkedin", "youtube",
  "tiktok", "facebook", "threads", "reddit", "telegram", "pinterest",
];

interface PlatformTab {
  key: string;
  label: string;
  sourcePlatforms: string[];
}

export default function RelevantPostsModule({ data }: RelevantPostsModuleProps) {
  const { relevantPosts } = data;
  const [generating, setGenerating] = useState(false);
  const [generated, setGenerated] = useState<RelevantPostItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeKey, setActiveKey] = useState<string | null>(null);

  const realPosts = useMemo(() => relevantPosts.filter((post) => !post.synthetic), [relevantPosts]);
  const syntheticPosts = useMemo(
    () => [...(generated ?? []), ...relevantPosts.filter((post) => post.synthetic)],
    [relevantPosts, generated]
  );

  const tabs = useMemo<PlatformTab[]>(() => {
    const present = new Set(realPosts.map((post) => post.platform));
    const ordered = [
      ...PLATFORM_ORDER.filter((platform) => present.has(platform)),
      ...Array.from(present).filter((platform) => !PLATFORM_ORDER.includes(platform)).sort(),
    ];
    const result: PlatformTab[] = [];
    for (const platform of ordered) {
      const meta = PLATFORM_META[platform] ?? { label: platform };
      const existing = result.find((tab) => tab.label === meta.label);
      if (existing) {
        existing.sourcePlatforms.push(platform);
        continue;
      }
      result.push({
        key: platform === "x_scraper" ? "x" : platform,
        label: meta.label,
        sourcePlatforms: [platform],
      });
    }
    result.push({ key: "synthetic", label: "Simulated", sourcePlatforms: ["synthetic"] });
    return result;
  }, [realPosts]);

  const effectiveKey =
    activeKey && tabs.some((tab) => tab.key === activeKey) ? activeKey : tabs[0]?.key ?? null;
  const activeTab = tabs.find((tab) => tab.key === effectiveKey) ?? null;

  const visiblePosts = useMemo(() => {
    if (!activeTab) return [];
    if (activeTab.key === "synthetic") return syntheticPosts;
    return realPosts.filter((post) => activeTab.sourcePlatforms.includes(post.platform));
  }, [activeTab, realPosts, syntheticPosts]);

  const handleGenerate = async () => {
    setGenerating(true);
    setError(null);
    try {
      const response = await apiFetch<{ synthetic_posts: Array<Record<string, unknown>> }>("/synthetic-posts", {
        method: "POST",
        body: JSON.stringify({ query: data.topic, count: 5 }),
      });
      const posts: RelevantPostItem[] = (response.synthetic_posts || []).map((post, index) => ({
        rank: Number(post.rank) || index + 1,
        text: String(post.text || ""),
        author: String(post.author || "unknown"),
        platform: "synthetic",
        url: undefined,
        engagementTotal: Number(post.engagement_total) || 0,
        synthetic: true,
      }));
      setGenerated(posts);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate simulated posts");
    } finally {
      setGenerating(false);
    }
  };

  const showGenerateCta = activeTab?.key === "synthetic" && syntheticPosts.length === 0;

  return (
    <div
      className="lg:col-span-6 bg-surface border border-surface-border/60 rounded-2xl flex flex-col overflow-hidden shadow-sm"
      style={{ height: "420px" }}
    >
      {/* Card Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-surface-high/60 border-b border-surface-border/50 shrink-0">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-[18px] text-secondary">forum</span>
          <span className="font-mono text-xs uppercase text-on-surface font-bold tracking-wider">
            Most Relevant Posts
          </span>
        </div>
        <span className="font-mono text-[10px] text-tertiary uppercase tracking-wider">
          {activeTab?.label ?? "None"}
        </span>
      </div>

      {/* Platform Tabs — horizontally scrollable */}
      <div className="flex items-center gap-1.5 px-4 py-2 border-b border-surface-border/50 overflow-x-auto no-scrollbar shrink-0">
        {tabs.map((tab) => {
          const isActive = tab.key === effectiveKey;
          const isEmpty = tab.key === "synthetic" && syntheticPosts.length === 0;
          return (
            <button
              key={tab.key}
              type="button"
              onClick={() => setActiveKey(tab.key)}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg font-mono text-[10px] uppercase tracking-wider border transition-colors whitespace-nowrap ${
                isActive
                  ? "bg-secondary-container/30 text-secondary border-secondary/40 font-bold"
                  : "text-on-surface-variant border-surface-border/60 hover:border-secondary/40 hover:text-secondary"
              }`}
            >
              <span className={isActive ? "text-secondary" : "text-on-surface-variant opacity-60"}>
                {tab.key === "synthetic" ? (
                  <span className="material-symbols-outlined text-[13px]">auto_awesome</span>
                ) : (
                  <PlatformLogo platform={tab.key} size={13} />
                )}
              </span>
              {tab.label}
              {isEmpty && !isActive && <span className="text-tertiary">+</span>}
            </button>
          );
        })}
        {generating && (
          <span className="ml-auto flex items-center gap-1 font-mono text-[10px] uppercase tracking-wider text-tertiary whitespace-nowrap">
            <span className="material-symbols-outlined text-[13px] animate-spin">progress_activity</span>
            Generating...
          </span>
        )}
      </div>

      {/* Scrollable Posts Area — fixed height, never grows beyond card */}
      <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-3 min-h-0">
        {visiblePosts.length ? (
          visiblePosts.map((post) => (
            <div
              key={`${post.rank}-${post.author}-${post.text.slice(0, 16)}`}
              className="rounded-xl border border-surface-border/70 bg-surface-lowest p-3 flex flex-col gap-1.5 shrink-0"
            >
              <div className="flex items-center justify-between gap-2">
                <span className="font-mono text-[11px] font-bold text-on-surface truncate">
                  @{post.author.replace(/^@/, "")}
                </span>
                <span className="flex items-center gap-2 shrink-0">
                  {post.synthetic && (
                    <span className="font-mono text-[9px] uppercase tracking-wider text-tertiary border border-tertiary/40 bg-tertiary/10 px-1.5 py-0.5 rounded-full">
                      Simulated
                    </span>
                  )}
                  <span className="flex items-center gap-1 font-mono text-[10px] text-on-surface-variant">
                    <span className="material-symbols-outlined text-[13px] text-secondary">favorite</span>
                    {post.engagementTotal.toLocaleString()}
                  </span>
                </span>
              </div>
              <p className="font-sans text-xs text-on-surface-variant leading-relaxed line-clamp-3">
                {post.text}
              </p>
              {post.url && (
                <a
                  href={post.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-mono text-[10px] text-secondary hover:underline flex items-center gap-1 w-fit"
                >
                  View post
                  <span className="material-symbols-outlined text-[12px]">open_in_new</span>
                </a>
              )}
            </div>
          ))
        ) : showGenerateCta ? (
          <div className="flex flex-col items-center justify-center py-8 gap-2">
            <span className="material-symbols-outlined text-3xl text-outline">auto_awesome</span>
            <p className="text-sm font-medium text-on-surface">No simulated posts yet</p>
            <p className="text-xs text-on-surface-variant max-w-xs text-center">
              No posts were retrieved for this query. Generate LLM-simulated posts grounded in the
              retrieved context - they are clearly badged, never presented as real.
            </p>
            {error && <p className="text-xs text-error">{error}</p>}
            <button
              type="button"
              onClick={handleGenerate}
              disabled={generating}
              className="mt-2 flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-mono text-[11px] uppercase tracking-wider
                         bg-secondary-container/30 text-secondary border border-secondary/40 hover:bg-secondary-container/50
                         disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <span className="material-symbols-outlined text-[15px]">auto_awesome</span>
              {generating ? "Generating..." : "Generate simulated posts"}
            </button>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-6 gap-2">
            <span className="material-symbols-outlined text-2xl text-outline">rule</span>
            <p className="text-xs text-on-surface-variant">
              No {activeTab?.label ?? "platform"} posts retrieved for this query - switch tabs above.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
