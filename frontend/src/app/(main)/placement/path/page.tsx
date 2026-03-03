"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

interface Milestone { order: number; title: string; description: string; is_completed: boolean; is_unlocked: boolean; target_score: number; }
interface PathData { name: string; description: string; progress_percentage: number; milestones: Milestone[]; }

export default function LearningPathPage() {
  const [path, setPath] = useState<PathData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/v1/placement/path", { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((d: PathData) => { setPath(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Đang tải...</div>;

  if (!path) return (
    <div style={{ maxWidth: 600, margin: "0 auto", padding: "4rem 1rem", textAlign: "center" }}>
      <div className="text-5xl mb-4">🛤️</div>
      <h1 className="text-xl font-bold mb-3" style={{ color: "var(--text-primary)" }}>Chưa có lộ trình</h1>
      <p className="mb-6" style={{ color: "var(--text-tertiary)" }}>Làm bài placement test để tạo lộ trình cá nhân hóa.</p>
      <Link href="/placement" className="px-8 py-3 rounded-xl font-semibold text-white no-underline inline-block" style={{ background: "#6366f1" }}>Bắt đầu test</Link>
    </div>
  );

  return (
    <div style={{ maxWidth: 768, margin: "0 auto", padding: "2rem 1rem" }}>
      <h1 className="text-2xl font-bold mb-1" style={{ color: "var(--text-primary)" }}>🛤️ {path.name}</h1>
      <p className="text-sm mb-6" style={{ color: "var(--text-secondary)" }}>{path.description}</p>

      {/* Progress bar */}
      <div className="p-4 rounded-xl mb-6" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
        <div className="flex justify-between text-sm mb-2">
          <span style={{ color: "var(--text-secondary)" }}>Tiến độ</span>
          <span className="font-bold" style={{ color: "#6366f1" }}>{path.progress_percentage?.toFixed(0)}%</span>
        </div>
        <div className="h-3 rounded-full overflow-hidden" style={{ background: "var(--border-default)" }}>
          <div className="h-full rounded-full transition-all" style={{ background: "linear-gradient(90deg, #6366f1, #8b5cf6)", width: `${path.progress_percentage}%` }} />
        </div>
      </div>

      {/* Milestones */}
      <div className="space-y-4">
        {path.milestones?.map((m) => (
          <div key={m.order} className="p-5 rounded-2xl transition-all" style={{
            background: m.is_completed ? "rgba(16,185,129,.06)" : m.is_unlocked ? "var(--bg-surface)" : "var(--bg-surface)",
            border: `1px solid ${m.is_completed ? "rgba(16,185,129,.3)" : m.is_unlocked ? "#6366f1" : "var(--border-default)"}`,
            opacity: (m.is_completed || m.is_unlocked) ? 1 : 0.5,
          }}>
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0" style={{
                background: m.is_completed ? "#10b981" : m.is_unlocked ? "#6366f1" : "var(--border-default)",
                color: (m.is_completed || m.is_unlocked) ? "white" : "var(--text-tertiary)",
              }}>{m.is_completed ? "✓" : m.order}</div>
              <div className="flex-1">
                <h3 className="font-semibold text-sm mb-1" style={{ color: "var(--text-primary)" }}>{m.title}</h3>
                {m.description && <p className="text-xs" style={{ color: "var(--text-tertiary)" }}>{m.description}</p>}
                {m.target_score > 0 && <span className="inline-block mt-2 px-3 py-1 rounded-full text-xs font-medium" style={{ background: "rgba(99,102,241,.1)", color: "#6366f1" }}>Target: {m.target_score}</span>}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
