"use client";

import React, { useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { GoogleTrendsRegion, GoogleTrendsRelatedItem } from "@/lib/adapter";

type InterestCategory = "regions" | "topics" | "queries";

interface InterestByRegionProps {
  regions: GoogleTrendsRegion[];
  relatedTopics: GoogleTrendsRelatedItem[];
  relatedQueries: GoogleTrendsRelatedItem[];
  compact?: boolean;
}

const categoryLabels: Array<{ key: InterestCategory; label: string }> = [
  { key: "regions", label: "Regions" },
  { key: "topics", label: "Related Topics" },
  { key: "queries", label: "Related Queries" },
];

export default function InterestByRegion({
  regions,
  relatedTopics,
  relatedQueries,
  compact = false,
}: InterestByRegionProps) {
  const [activeCategory, setActiveCategory] = useState<InterestCategory>("regions");

  const counts = {
    regions: regions.length,
    topics: relatedTopics.length,
    queries: relatedQueries.length,
  };
  const selectedCategory = counts[activeCategory]
    ? activeCategory
    : categoryLabels.find(({ key }) => counts[key] > 0)?.key || activeCategory;

  const chartData = useMemo(() => {
    if (selectedCategory === "regions") {
      return regions.slice(0, 8).map((item) => ({
        label: item.location,
        value: item.value,
        displayValue: `${item.value}`,
      }));
    }

    const items = selectedCategory === "topics" ? relatedTopics : relatedQueries;
    return items.slice(0, 8).map((item) => ({
      label: item.label,
      value: item.value,
      displayValue: item.valueLabel || `${item.value}`,
    }));
  }, [regions, relatedQueries, relatedTopics, selectedCategory]);

  const hasAnyData = Object.values(counts).some((count) => count > 0);
  if (!hasAnyData) return null;

  return (
    <div className={compact ? "p-0" : "rounded-xl border border-surface-border/70 bg-surface-lowest p-3"}>
      <div className="flex items-center justify-between gap-2 flex-wrap mb-2">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-wider text-slate-300 font-bold">
            Interest by Region & Related Signals
          </div>
          <div className="font-sans text-[11px] text-slate-500 mt-0.5">
            Relative search interest, not search volume
          </div>
        </div>
        <div className="flex items-center gap-1 rounded-full bg-surface-high p-1 border border-surface-border">
          {categoryLabels.map(({ key, label }) => (
            <button
              key={key}
              type="button"
              disabled={!counts[key]}
              onClick={() => setActiveCategory(key)}
              className={`px-2 py-1 rounded-full font-mono text-[9px] uppercase tracking-wide transition-colors ${
                selectedCategory === key
                  ? "bg-white text-slate-950 font-bold"
                  : counts[key]
                    ? "text-slate-400 hover:text-white"
                    : "text-slate-600 cursor-not-allowed"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {chartData.length ? (
        <div className="h-52 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={chartData}
              layout="vertical"
              margin={{ top: 4, right: 8, left: 4, bottom: 4 }}
            >
              <CartesianGrid horizontal={false} stroke="#292e3a" />
              <XAxis
                type="number"
                domain={[0, "auto"]}
                tick={{ fill: "#64748b", fontSize: 9 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                type="category"
                dataKey="label"
                width={92}
                tick={{ fill: "#cbd5e1", fontSize: 9 }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip
                cursor={{ fill: "#1e222d" }}
                contentStyle={{ background: "#1a1a24", border: "1px solid #2a2a3a", borderRadius: 8 }}
                formatter={(value: number, _name: string, item: { payload?: { displayValue?: string } }) => [
                  item.payload?.displayValue || value,
                  "Interest",
                ]}
              />
              <Bar dataKey="value" fill="#a855f7" radius={[0, 4, 4, 0]} barSize={14} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <p className="py-8 text-center text-xs text-slate-500">No data for this category.</p>
      )}
    </div>
  );
}
