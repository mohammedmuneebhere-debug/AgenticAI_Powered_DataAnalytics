"use client";

import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell,
} from "recharts";
import type { VisualizationSpec } from "@/lib/api";

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
    const chartData = (data.labels as string[]).map((label, i) => ({
      day: label,
      score: (data.values as number[])[i],
    }));
    return (
      <ResponsiveContainer width="100%" height={150}>
        <LineChart data={chartData}>
          <XAxis dataKey="day" tick={{ fill: "#9090a0", fontSize: 10 }} />
          <YAxis domain={[0, 1]} tick={{ fill: "#9090a0", fontSize: 10 }} />
          <Tooltip contentStyle={{ background: "#1a1a24", border: "1px solid #2a2a3a" }} />
          <Line type="monotone" dataKey="score" stroke="#6366f1" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    );
  }

  if (viz.type === "trend_bars") {
    const chartData = (data.labels as string[]).map((label, i) => ({
      topic: label,
      velocity: (data.values as number[])[i],
    }));
    return (
      <ResponsiveContainer width="100%" height={150}>
        <BarChart data={chartData}>
          <XAxis dataKey="topic" tick={{ fill: "#9090a0", fontSize: 9 }} />
          <YAxis tick={{ fill: "#9090a0", fontSize: 10 }} />
          <Tooltip contentStyle={{ background: "#1a1a24", border: "1px solid #2a2a3a" }} />
          <Bar dataKey="velocity" fill="#a855f7" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    );
  }

  if (viz.type === "demographic_pie") {
    const chartData = (data.labels as string[]).map((label, i) => ({
      name: label,
      value: (data.values as number[])[i],
    }));
    return (
      <ResponsiveContainer width="100%" height={150}>
        <PieChart>
          <Pie data={chartData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={55}>
            {chartData.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip contentStyle={{ background: "#1a1a24", border: "1px solid #2a2a3a" }} />
        </PieChart>
      </ResponsiveContainer>
    );
  }

  if (viz.type === "network_graph") {
    const nodes = data.nodes as { id: string; label: string; size: number }[];
    return (
      <div className="flex flex-wrap gap-2">
        {nodes.slice(0, 6).map((n) => (
          <span
            key={n.id}
            className="text-xs px-2 py-1 rounded-full border border-[var(--accent)]"
            style={{ opacity: Math.min(1, 0.4 + n.size / 500) }}
          >
            {n.label}
          </span>
        ))}
      </div>
    );
  }

  return <p className="text-xs text-[var(--text-secondary)]">Chart: {viz.type}</p>;
}
