"use client";

import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell,
} from "recharts";
import type { VisualizationSpec } from "@/lib/api";
import InterestByRegion from "./dashboard/InterestByRegion";
import type { GoogleTrendsRegion, GoogleTrendsRelatedItem } from "@/lib/adapter";

const COLORS = ["#6366f1", "#a855f7", "#ec4899", "#22c55e", "#f59e0b"];

interface Props {
  visualizations: VisualizationSpec[];
}

export default function VisualizationPanel({ visualizations }: Props) {
  if (!visualizations.length) return null;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
      {visualizations.map((viz, i) => (
        <div key={i} className="rounded-lg border border-[var(--border)] p-3">
          <p className="text-xs font-medium text-[var(--text-secondary)] mb-2">{viz.title}</p>
          {renderChart(viz)}
        </div>
      ))}
    </div>
  );
}

function renderChart(viz: VisualizationSpec) {
  const data = viz.data;

  if (viz.type === "sentiment_timeline") {
    const chartData = toLabeledValues(data).map(({ label, value }) => ({
      day: label,
      score: value,
    }));
    return (
      <ResponsiveContainer width="100%" height={150}>
        <LineChart data={chartData}>
          <XAxis dataKey="day" tick={{ fill: "var(--text-secondary)", fontSize: 10 }} />
          <YAxis domain={[0, 1]} tick={{ fill: "var(--text-secondary)", fontSize: 10 }} />
          <Tooltip contentStyle={{ background: "var(--bg-elevated)", border: "1px solid var(--bg-elevated)" }} />
          <Line type="monotone" dataKey="score" stroke="#6366f1" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    );
  }

  if (viz.type === "trend_bars") {
    const chartData = toLabeledValues(data).map(({ label, value }) => ({
      topic: label,
      velocity: value,
    }));
    return (
      <ResponsiveContainer width="100%" height={150}>
        <BarChart data={chartData}>
          <XAxis dataKey="topic" tick={{ fill: "var(--text-secondary)", fontSize: 9 }} />
          <YAxis tick={{ fill: "var(--text-secondary)", fontSize: 10 }} />
          <Tooltip contentStyle={{ background: "var(--bg-elevated)", border: "1px solid var(--bg-elevated)" }} />
          <Bar dataKey="velocity" fill="#a855f7" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    );
  }

  if (viz.type === "google_trends_insights") {
    return (
      <InterestByRegion
        regions={toRegions(data.regions)}
        relatedTopics={toRelatedItems(data.related_topics)}
        relatedQueries={toRelatedItems(data.related_queries)}
        compact
      />
    );
  }

  if (viz.type === "source_cards") {
    const items = Array.isArray(data.items)
      ? data.items as { title: string; description?: string; source?: string; url?: string }[]
      : [];
    return (
      <div className="space-y-2">
        {items.map((item, index) => (
          <a
            key={`${item.title}-${index}`}
            href={item.url || undefined}
            target={item.url ? "_blank" : undefined}
            rel={item.url ? "noreferrer" : undefined}
            className="block rounded-md border border-[var(--border)] bg-[var(--bg-elevated)] p-2 hover:border-[var(--accent)] transition-colors"
          >
            <div className="text-xs font-medium text-[var(--text-primary)] line-clamp-2">{item.title}</div>
            <div className="mt-1 text-[10px] text-[var(--text-secondary)] line-clamp-2">{item.description}</div>
            <div className="mt-1 text-[10px] text-[var(--accent)]">{item.source}</div>
          </a>
        ))}
      </div>
    );
  }

  if (viz.type === "demographic_pie") {
    const chartData = toLabeledValues(data).map(({ label, value }) => ({
      name: label,
      value,
    }));
    return (
      <ResponsiveContainer width="100%" height={150}>
        <PieChart>
          <Pie data={chartData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={55}>
            {chartData.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip contentStyle={{ background: "var(--bg-elevated)", border: "1px solid var(--bg-elevated)" }} />
        </PieChart>
      </ResponsiveContainer>
    );
  }

  if (viz.type === "network_graph") {
    const nodes = Array.isArray(data.nodes)
      ? (data.nodes as { id: string; label: string; size?: number }[])
      : [];
    return (
      <div className="flex flex-wrap gap-2">
        {nodes.slice(0, 6).map((n) => (
          <span
            key={n.id}
            className="text-xs px-2 py-1 rounded-full border border-[var(--accent)]"
            style={{ opacity: Math.min(1, 0.4 + (n.size || 0) / 500) }}
          >
            {n.label}
          </span>
        ))}
      </div>
    );
  }

  if (viz.type === "scenario_matrix") {
    const scenarios = Array.isArray(data.scenarios) ? data.scenarios as { name: string; probability: number }[] : [];
    return (
      <ResponsiveContainer width="100%" height={150}>
        <BarChart data={scenarios.map((scenario) => ({ name: scenario.name, probability: scenario.probability * 100 }))}>
          <XAxis dataKey="name" tick={{ fill: "var(--text-secondary)", fontSize: 9 }} />
          <YAxis unit="%" tick={{ fill: "var(--text-secondary)", fontSize: 10 }} />
          <Tooltip contentStyle={{ background: "var(--bg-elevated)", border: "1px solid var(--bg-elevated)" }} />
          <Bar dataKey="probability" fill="#22c55e" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    );
  }

  if (viz.type === "opportunity_matrix") {
    const opportunities = Array.isArray(data.opportunities)
      ? data.opportunities as { product: string; score: number }[]
      : [];
    return (
      <ResponsiveContainer width="100%" height={150}>
        <BarChart data={opportunities.map((item) => ({ name: item.product, score: item.score * 100 }))}>
          <XAxis dataKey="name" tick={{ fill: "var(--text-secondary)", fontSize: 9 }} />
          <YAxis unit="%" tick={{ fill: "var(--text-secondary)", fontSize: 10 }} />
          <Tooltip contentStyle={{ background: "var(--bg-elevated)", border: "1px solid var(--bg-elevated)" }} />
          <Bar dataKey="score" fill="#f59e0b" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    );
  }

  return <p className="text-xs text-[var(--text-secondary)]">Chart: {viz.type}</p>;
}

function toLabeledValues(data: Record<string, unknown>): { label: string; value: number }[] {
  const labels = Array.isArray(data.labels) ? data.labels : [];
  const values = Array.isArray(data.values) ? data.values : [];
  return labels.flatMap((label, index) => {
    const value = Number(values[index]);
    return Number.isFinite(value) ? [{ label: String(label), value }] : [];
  });
}

function toRegions(value: unknown): GoogleTrendsRegion[] {
  return Array.isArray(value)
    ? value.filter((item): item is Record<string, unknown> => !!item && typeof item === "object").map((item) => ({
      location: String(item.location || item.geo || "Unknown region"),
      geo: item.geo ? String(item.geo) : undefined,
      value: Number(item.value) || 0,
      coordinates: item.coordinates as GoogleTrendsRegion["coordinates"],
    }))
    : [];
}

function toRelatedItems(value: unknown): GoogleTrendsRelatedItem[] {
  return Array.isArray(value)
    ? value.filter((item): item is Record<string, unknown> => !!item && typeof item === "object").map((item) => ({
      label: String(item.label || "Related signal"),
      category: String(item.category || "top"),
      value: Number(item.value) || 0,
      valueLabel: item.value_label ? String(item.value_label) : undefined,
      type: item.type ? String(item.type) : undefined,
      url: item.url ? String(item.url) : undefined,
    }))
    : [];
}
