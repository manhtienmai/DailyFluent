"use client";

import { useState, useEffect } from "react";

interface StatusData { today: number; this_week: number; total_reviewed: number; due_today: number; words_by_level: { level: string; count: number; }[]; }

export default function StudyStatusPage() {
  const [data, setData] = useState<StatusData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/v1/vocab/study-status", { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((d: StatusData) => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Đang tải...</div>;
  if (!data) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Không có dữ liệu.</div>;

  return (
    <div style={{ maxWidth: 700, margin: "0 auto", padding: "2rem 1rem" }}>
      <h1 className="text-2xl font-bold mb-6" style={{ color: "var(--text-primary)" }}>📈 Trạng thái học</h1>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "1rem" }} className="mb-6">
        {[
          { label: "Hôm nay", value: data.today, color: "#6366f1" },
          { label: "Tuần này", value: data.this_week, color: "#8b5cf6" },
          { label: "Tổng ôn tập", value: data.total_reviewed, color: "#10b981" },
          { label: "Cần ôn hôm nay", value: data.due_today, color: "#f59e0b" },
        ].map((s) => (
          <div key={s.label} className="p-5 rounded-2xl text-center" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
            <div className="text-3xl font-bold mb-1" style={{ color: s.color }}>{s.value}</div>
            <div className="text-xs" style={{ color: "var(--text-tertiary)" }}>{s.label}</div>
          </div>
        ))}
      </div>

      {data.words_by_level?.length > 0 && (
        <div className="p-5 rounded-2xl" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
          <h2 className="font-bold text-sm mb-4" style={{ color: "var(--text-primary)" }}>Phân bố theo cấp độ</h2>
          <div className="space-y-3">
            {data.words_by_level.map((l) => (
              <div key={l.level} className="flex items-center gap-3">
                <span className="text-sm font-medium w-20" style={{ color: "var(--text-secondary)" }}>{l.level}</span>
                <div className="flex-1 h-6 rounded-full overflow-hidden" style={{ background: "var(--border-default)" }}>
                  <div className="h-full rounded-full flex items-center justify-end pr-2 text-xs font-bold text-white" style={{ background: "#6366f1", width: `${Math.max(l.count * 2, 10)}%`, minWidth: "40px" }}>{l.count}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
