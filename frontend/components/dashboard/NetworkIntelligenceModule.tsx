"use client";

import React from "react";
import type { NormalizedDashboardData } from "@/lib/adapter";

interface NetworkIntelligenceModuleProps {
  data: NormalizedDashboardData;
}

interface SatelliteNode {
  id: string;
  label: string;
  value: number; // 0-100 interest / relevance, drives node size
  angle: number; // radians, deterministic per label
  ring: number; // 0 inner, 1 outer
}

const NODE_COLORS = ["#34D399", "#FBBF24", "#A78BFA", "#60A5FA"];

/** Deterministic hash so the same label always lands on the same spot. */
function hashLabel(label: string): number {
  let hash = 0;
  for (let index = 0; index < label.length; index += 1) {
    hash = (hash * 31 + label.charCodeAt(index)) % 100000;
  }
  return hash;
}

/**
 * Bacteria-style clustering: the searched topic sits at the center of the
 * petri dish and related topics cluster around it as organic satellite
 * colonies (two jittered rings, sized by interest value).
 */
function ClusterGraph({
  topic,
  satellites,
  large,
}: {
  topic: string;
  satellites: SatelliteNode[];
  large: boolean;
}) {
  const width = large ? 760 : 400;
  const height = large ? 520 : 160;
  const centerX = width / 2;
  const centerY = height / 2;
  const coreRadius = large ? 52 : 26;
  const innerRing = large ? 150 : 62;
  const outerRing = large ? 225 : 92;

  const placed = satellites.map((satellite) => {
    const jitterSource = hashLabel(satellite.id + satellite.label);
    const jitter = ((jitterSource % 100) / 100 - 0.5) * (large ? 0.55 : 0.7);
    const radialJitter = ((jitterSource % 37) / 37 - 0.5) * (large ? 26 : 12);
    const ringRadius = (satellite.ring === 0 ? innerRing : outerRing) + radialJitter;
    const angle = satellite.angle + jitter;
    const nodeRadius = large ? 10 + (satellite.value / 100) * 16 : 6 + (satellite.value / 100) * 8;
    return {
      ...satellite,
      x: centerX + Math.cos(angle) * ringRadius,
      y: centerY + Math.sin(angle) * ringRadius,
      radius: nodeRadius,
      color: NODE_COLORS[hashLabel(satellite.label) % NODE_COLORS.length],
    };
  });

  return (
    <svg className="w-full h-full" viewBox={`0 0 ${width} ${height}`} role="img" aria-label={`Cluster graph of ${topic}`}>
      {/* Petri-dish rings */}
      {[outerRing + (large ? 30 : 14), outerRing, innerRing].map((ring, index) => (
        <circle
          key={`ring-${index}`}
          cx={centerX}
          cy={centerY}
          r={ring}
          fill="none"
          stroke="var(--border)"
          strokeWidth={index === 0 ? 1 : 0.75}
          strokeDasharray={index === 0 ? "none" : "3 4"}
          opacity={0.55 - index * 0.12}
        />
      ))}

      {/* tendrils: center to each satellite, satellites to nearest inner neighbor */}
      {placed.map((node, index) => {
        const anchor = node.ring === 1
          ? placed.find((candidate, candidateIndex) => candidate.ring === 0 && candidateIndex !== index) ?? null
          : null;
        const targetX = anchor ? anchor.x : centerX;
        const targetY = anchor ? anchor.y : centerY;
        const mx = (node.x + targetX) / 2 + Math.sin(hashLabel(node.id) % 7) * 8;
        const my = (node.y + targetY) / 2 + Math.cos(hashLabel(node.id) % 5) * 8;
        return (
          <path
            key={`tendril-${node.id}`}
            d={`M ${centerX} ${centerY} Q ${mx} ${my} ${node.x} ${node.y}`}
            fill="none"
            stroke={node.color}
            strokeWidth={0.8}
            opacity={0.35}
          />
        );
      })}

      {/* satellite colonies */}
      {placed.map((node) => (
        <g key={node.id}>
          <circle cx={node.x} cy={node.y} r={node.radius + 3} fill={node.color} opacity={0.16} />
          <circle cx={node.x} cy={node.y} r={node.radius} fill="var(--bg-surface)" stroke={node.color} strokeWidth={1.5} />
          <text
            x={node.x}
            y={node.y + (large ? 4 : 3)}
            fill="var(--text-primary)"
            fontSize={large ? 10 : 7}
            fontWeight={700}
            textAnchor="middle"
          >
            {node.label.slice(0, large ? 14 : 10).toUpperCase()}
          </text>
          {large && (
            <text x={node.x} y={node.y + 18} fill="var(--text-secondary)" fontSize={9} textAnchor="middle">
              {Math.round(node.value)}
            </text>
          )}
        </g>
      ))}

      {/* core: the searched topic */}
      <circle cx={centerX} cy={centerY} r={coreRadius + 8} fill="#34D399" opacity={0.12} />
      <circle cx={centerX} cy={centerY} r={coreRadius} fill="var(--bg-elevated)" stroke="#ffffff" strokeWidth={2} />
      <text
        x={centerX}
        y={centerY - 2}
        fill="var(--text-primary)"
        fontSize={large ? 13 : 8}
        fontWeight={700}
        textAnchor="middle"
      >
        {topic.slice(0, large ? 18 : 12).toUpperCase()}
      </text>
      <text x={centerX} y={centerY + (large ? 14 : 10)} fill="var(--text-secondary)" fontSize={large ? 9 : 6} textAnchor="middle">
        SEARCH TOPIC
      </text>
    </svg>
  );
}

/** Build satellite nodes from real Google Trends related topics/queries, falling back to trend topics and finally the top trend. */
export function buildSatellites(
  data: NormalizedDashboardData,
  maxInner = 5,
  maxOuter = 5
): SatelliteNode[] {
  const satellites: SatelliteNode[] = [];
  const seen = new Set<string>();
  const push = (label: string, value: number, ring: number, index: number) => {
    const id = `${ring}-${label.toLowerCase()}`;
    if (!label || seen.has(id) || satellites.length >= maxInner + maxOuter) return;
    seen.add(id);
    // Even angular spacing per ring with deterministic offset
    const ringCount = satellites.filter((s) => s.ring === ring).length;
    const angle = (ringCount / (ring === 0 ? maxInner : maxOuter)) * Math.PI * 2 + (ring === 0 ? 0 : Math.PI / maxOuter);
    satellites.push({ id: `${id}-${index}`, label, value, angle, ring });
  };

  data.googleTrends.relatedTopics.slice(0, maxInner).forEach((item, index) => push(item.label, item.value, 0, index));
  data.googleTrends.relatedQueries.slice(0, maxInner).forEach((item, index) => push(item.label, item.value, 0, 100 + index));
  data.trendDrivers.slice(0, maxOuter).forEach((item, index) => push(item.title, 60 + index * 5, 1, index));
  data.narratives.slice(0, maxOuter).forEach((item, index) => push(item.title, 55 + index * 5, 1, 200 + index));

  // Absolute fallback: the topic itself is the only signal — give it one satellite
  if (!satellites.length) {
    satellites.push({ id: "fallback-satellite", label: data.topic || "signal", value: 50, angle: 0.8, ring: 0 });
  }
  return satellites;
}

export default function NetworkIntelligenceModule({ data }: NetworkIntelligenceModuleProps) {
  const { networkIntelligence } = data;
  const satellites = buildSatellites(data);

  return (
    <div className="lg:col-span-6 bg-surface border border-surface-border/60 rounded-2xl flex flex-col overflow-hidden shadow-sm h-full">
      <div className="flex items-center justify-between px-4 py-3 bg-surface-high/60 border-b border-surface-border/50">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-[18px] text-secondary">hub</span>
          <span className="font-mono text-xs uppercase text-on-surface font-bold tracking-wider">
            Network Intelligence
          </span>
        </div>
        <span className="font-mono text-[10px] text-on-surface">
          Graph Density: {networkIntelligence.graphDensity}
        </span>
      </div>

      <div className="p-4 flex flex-col justify-between flex-1 gap-3">
        {/* Bacteria-style clustering graph (center = searched topic) */}
        <div className="w-full h-44 bg-surface-lowest border border-surface-border/70 rounded-xl relative overflow-hidden">
          <ClusterGraph topic={data.topic} satellites={satellites} large={false} />
        </div>

        {/* Quick Stats Strip */}
        <div className="grid grid-cols-3 gap-2">
          <div className="bg-surface-lowest p-2.5 border border-surface-border/70 rounded-xl">
            <span className="font-mono text-[9px] uppercase text-outline block">Top Community</span>
            <span className="font-sans text-xs text-[var(--text-primary)] font-semibold truncate block">
              {networkIntelligence.topCommunity}
            </span>
          </div>

          <div className="bg-surface-lowest p-2.5 border border-surface-border/70 rounded-xl">
            <span className="font-mono text-[9px] uppercase text-outline block">Fastest Growing</span>
            <span className="font-sans text-xs text-secondary font-semibold truncate block">
              {networkIntelligence.fastestGrowing}
            </span>
          </div>

          <div className="bg-surface-lowest p-2.5 border border-surface-border/70 rounded-xl">
            <span className="font-mono text-[9px] uppercase text-outline block">Top Influencer</span>
            <span className="font-sans text-xs text-tertiary font-semibold truncate block">
              {networkIntelligence.topInfluencer}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

/** Enlarged variant rendered inside the ExpandableCard modal. */
export function NetworkIntelligenceExpanded({ data }: NetworkIntelligenceModuleProps) {
  const satellites = buildSatellites(data, 7, 8);
  return (
    <div className="w-full h-[560px] bg-surface-lowest border border-surface-border/70 rounded-xl overflow-hidden">
      <ClusterGraph topic={data.topic} satellites={satellites} large />
    </div>
  );
}
