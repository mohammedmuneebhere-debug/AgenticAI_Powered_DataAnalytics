"use client";

import React, { useState } from "react";
import type { DashboardRange, NormalizedDashboardData } from "@/lib/adapter";

interface TrajectoryModuleProps {
  data: NormalizedDashboardData;
  activeRange: DashboardRange;
  onRangeChange: (range: DashboardRange) => void;
}

export default function TrajectoryModule({ data, activeRange, onRangeChange }: TrajectoryModuleProps) {
  const { trajectory } = data;
  const visiblePoints = trajectory.points;
  const maxVolume = Math.max(...visiblePoints.map((point) => point.volume), 1);
  const pointCoordinates = visiblePoints.map((point, index) => ({
    x: visiblePoints.length === 1 ? 350 : 20 + (index / (visiblePoints.length - 1)) * 660,
    y: 160 - (point.volume / maxVolume) * 130,
  }));
  const linePoints = pointCoordinates.map((point) => `${point.x},${point.y}`).join(" ");

  return (
    <div className="lg:col-span-8 bg-surface border border-surface-border/60 rounded-2xl flex flex-col overflow-hidden shadow-sm">
      <div className="flex items-center justify-between px-4 py-3 bg-surface-high/60 border-b border-surface-border/50">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-[18px] text-white">show_chart</span>
          <span className="font-mono text-xs uppercase text-slate-200 font-bold tracking-wider">
            Conversation Volume &amp; Trajectory
          </span>
        </div>
        <div className="flex items-center gap-1 bg-surface-lowest p-1 border border-surface-border rounded-full">
          {(["1H", "24H", "7D", "30D"] as const).map((range) => (
            <button
              key={range}
              onClick={() => onRangeChange(range)}
              type="button"
              className={`px-2.5 py-0.5 font-mono text-[10px] rounded-full transition-colors ${
                activeRange === range
                  ? "bg-white text-slate-950 font-bold"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              {range}
            </button>
          ))}
        </div>
      </div>

      <div className="p-4 flex-1 flex flex-col justify-between">
        <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
          <div className="flex items-center gap-4">
            <div>
              <div className="font-mono text-[10px] uppercase text-slate-500">Peak Volume ({activeRange})</div>
              <div className="font-sans text-lg font-bold text-white">{visiblePoints.length ? `${Math.max(...visiblePoints.map((point) => point.volume))} / period` : "No records"}</div>
            </div>
            <div className="h-6 w-px bg-surface-border" />
            <div>
              <div className="font-mono text-[10px] uppercase text-slate-500">Mean Velocity</div>
              <div className="font-sans text-lg font-bold text-secondary">{visiblePoints.length ? `${(visiblePoints.reduce((sum, point) => sum + point.lineValue, 0) / visiblePoints.length).toFixed(2)} avg` : "No records"}</div>
            </div>
          </div>
          <div className="flex items-center gap-2 bg-surface-lowest px-3 py-1 rounded-full border border-surface-border">
            <span className="w-2 h-2 rounded-full bg-white" />
            <span className="font-sans text-xs text-slate-200 font-medium">
              {visiblePoints.length ? `Records in ${activeRange}: ${visiblePoints.reduce((sum, point) => sum + point.volume, 0)}` : `No records in ${activeRange}`}
            </span>
          </div>
        </div>

        {/* Solid SVG Line & Area (Zero Gradients) */}
        <div className="w-full h-56 relative bg-surface-lowest border border-surface-border/70 rounded-xl p-3 flex flex-col justify-between overflow-hidden">
          <div className="absolute inset-0 grid grid-rows-4 divide-y divide-surface-border/40 pointer-events-none">
            <div /><div /><div /><div />
          </div>

          <svg className="w-full h-full relative z-10" preserveAspectRatio="none" viewBox="0 0 700 180">
            {pointCoordinates.map((point, index) => (
              <rect key={`bar-${index}`} x={point.x - 5} y={point.y} width="10" height={160 - point.y} rx="3" fill={index === pointCoordinates.length - 1 ? "#3b4252" : "#1e222d"} />
            ))}
            {linePoints && <polyline fill="none" stroke="#cbd5e1" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" points={linePoints} />}
            {pointCoordinates.length > 0 && (
              <>
                <line x1={pointCoordinates[pointCoordinates.length - 1].x} y1="180" x2={pointCoordinates[pointCoordinates.length - 1].x} y2={pointCoordinates[pointCoordinates.length - 1].y} stroke="#94a3b8" strokeWidth="1.5" strokeDasharray="3,3" />
                <circle cx={pointCoordinates[pointCoordinates.length - 1].x} cy={pointCoordinates[pointCoordinates.length - 1].y} r="4.5" fill="#13151b" stroke="#ffffff" strokeWidth="2" />
              </>
            )}
          </svg>

          {/* Timeline X-Axis */}
          <div className="flex justify-between font-mono text-[10px] text-slate-500 pt-2 border-t border-surface-border/50 relative z-10">
            {visiblePoints.map((point) => <span key={point.time}>{point.time}</span>)}
          </div>
        </div>
      </div>
    </div>
  );
}
