"use client";

const DEMO_QUERIES = [
  "Analyze coffee trends and tell me what product I should launch this winter.",
  "Why is BTC volatile today and what scenarios should I prepare for?",
  "What's trending in coffee among young consumers?",
];

interface Props {
  onSelect?: (query: string) => void;
}

export default function DemoQueries({ onSelect }: Props) {
  return (
    <div className="flex flex-wrap gap-2">
      {DEMO_QUERIES.map((q) => (
        <button
          key={q}
          onClick={() => onSelect?.(q)}
          className="text-xs px-3 py-1.5 rounded-full border border-[var(--border)] text-[var(--text-secondary)] hover:border-[var(--accent)] hover:text-[var(--text-primary)] transition-colors"
        >
          {q.length > 60 ? q.slice(0, 60) + "…" : q}
        </button>
      ))}
    </div>
  );
}
