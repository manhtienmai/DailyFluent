"use client";

import { useState, useEffect } from "react";

interface ProgressData { total_words: number; learned: number; mastered: number; accuracy: number; streak_days: number; categories: { name: string; learned: number; total: number; }[]; }

export default function VocabProgressPage() {
  const [data, setData] = useState<ProgressData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/v1/vocab/progress", { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((d: ProgressData) => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Đang tải...</div>;
  if (!data) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Không có dữ liệu.</div>;

  const pct = data.total_words ? Math.round((data.learned / data.total_words) * 100) : 0;

  return (
    <div style={{ maxWidth: 700, margin: "0 auto", padding: "2rem 1rem" }}>
      <h1 className="text-2xl font-bold mb-6" style={{ color: "var(--text-primary)" }}>📊 Tiến độ từ vựng</h1>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: "1rem" }} className="mb-6">
        {[
          { label: "Đã học", value: data.learned, icon: "📖", color: "#6366f1" },
          { label: "Thành thạo", value: data.mastered, icon: "⭐", color: "#10b981" },
          { label: "Tổng từ", value: data.total_words, icon: "📚", color: "#f59e0b" },
          { label: "Độ chính xác", value: `${data.accuracy}%`, icon: "🎯", color: "#8b5cf6" },
        ].map((s) => (
          <div key={s.label} className="p-4 rounded-2xl text-center" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
            <div className="text-2xl mb-1">{s.icon}</div>
            <div className="text-xl font-bold" style={{ color: s.color }}>{s.value}</div>
            <div className="text-xs" style={{ color: "var(--text-tertiary)" }}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* Overall progress */}
      <div className="p-5 rounded-2xl mb-6" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
        <div className="flex justify-between text-sm mb-2">
          <span style={{ color: "var(--text-secondary)" }}>Tổng tiến độ</span>
          <span className="font-bold" style={{ color: "#6366f1" }}>{pct}%</span>
        </div>
        <div className="h-3 rounded-full overflow-hidden" style={{ background: "var(--border-default)" }}>
          <div className="h-full rounded-full" style={{ background: "linear-gradient(90deg, #6366f1, #8b5cf6)", width: `${pct}%`, transition: "width 0.5s" }} />
        </div>
      </div>

      {/* Categories */}
      {data.categories?.length > 0 && (
        <div className="space-y-3">
          <h2 className="font-bold text-sm" style={{ color: "var(--text-primary)" }}>Theo chủ đề</h2>
          {data.categories.map((c) => (
            <div key={c.name} className="p-4 rounded-xl" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
              <div className="flex justify-between text-sm mb-1">
                <span style={{ color: "var(--text-primary)" }}>{c.name}</span>
                <span style={{ color: "var(--text-tertiary)" }}>{c.learned}/{c.total}</span>
              </div>
              <div className="h-2 rounded-full overflow-hidden" style={{ background: "var(--border-default)" }}>
                <div className="h-full rounded-full" style={{ background: "#10b981", width: `${c.total ? (c.learned / c.total * 100) : 0}%` }} />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
