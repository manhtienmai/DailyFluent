"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth";

interface Activity { type: string; reason: string; estimated_minutes: number; }
interface Milestone { order: number; title: string; is_completed: boolean; is_unlocked: boolean; }
interface DashboardData {
  profile: { estimated_score: number; target_score: number } | null;
  lesson: { target_minutes: number; actual_minutes: number; recommended_activities: Activity[] } | null;
  path: { name: string; progress_percentage: number; milestones: Milestone[] } | null;
}

const ACTIVITY_ICONS: Record<string, string> = { vocab_review: "📚", skill_practice: "🎯", path_vocab: "📖", listening_practice: "🎧" };

export default function PlacementDashboardPage() {
  const { user } = useAuth();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/v1/placement/dashboard", { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((d: DashboardData) => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Đang tải...</div>;

  const name = user?.first_name || user?.username || "bạn";

  return (
    <div style={{ maxWidth: 768, margin: "0 auto", padding: "1.5rem 1rem" }}>
      <h1 className="text-2xl font-bold mb-4" style={{ color: "var(--text-primary)" }}>👋 Chào {name}!</h1>

      {/* Goal card */}
      {data?.profile?.target_score && (
        <div className="rounded-xl p-4 text-white mb-6" style={{ background: "linear-gradient(90deg, #6366f1, #8b5cf6)" }}>
          <div className="flex items-center justify-between">
            <div><p className="text-sm" style={{ color: "rgba(255,255,255,.7)" }}>Mục tiêu</p><p className="text-xl font-bold">{data.profile.estimated_score} → {data.profile.target_score} TOEIC</p></div>
            <p className="text-3xl font-bold">{data.path?.progress_percentage?.toFixed(0) || 0}%</p>
          </div>
          <div className="mt-3 h-2 rounded-full overflow-hidden" style={{ background: "rgba(255,255,255,.2)" }}>
            <div className="h-full rounded-full bg-white" style={{ width: `${data.path?.progress_percentage || 0}%` }} />
          </div>
        </div>
      )}

      {/* Daily lesson */}
      <div className="rounded-2xl p-6 mb-6" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>📋 Bài học hôm nay</h2>
          {data?.lesson && <span className="text-sm" style={{ color: "var(--text-tertiary)" }}>{data.lesson.target_minutes} phút</span>}
        </div>
        {data?.lesson?.recommended_activities?.length ? (
          <div className="space-y-3">
            {data.lesson.recommended_activities.map((a, i) => (
              <div key={i} className="flex items-center gap-4 p-4 rounded-xl" style={{ background: "var(--bg-interactive)" }}>
                <div className="w-10 h-10 rounded-full flex items-center justify-center text-lg" style={{ background: "rgba(99,102,241,.1)" }}>{ACTIVITY_ICONS[a.type] || "📝"}</div>
                <div className="flex-1"><p className="font-medium text-sm" style={{ color: "var(--text-primary)" }}>{a.reason}</p><p className="text-xs" style={{ color: "var(--text-tertiary)" }}>{a.estimated_minutes} phút</p></div>
                <Link href="/vocab/sets?tab=my" className="px-4 py-2 rounded-lg text-xs font-medium text-white no-underline" style={{ background: "#6366f1" }}>Bắt đầu</Link>
              </div>
            ))}
          </div>
        ) : <p className="text-center py-8" style={{ color: "var(--text-tertiary)" }}>Không có bài học được đề xuất hôm nay.</p>}

        {data?.lesson && data.lesson.actual_minutes > 0 && (
          <div className="mt-4 pt-4" style={{ borderTop: "1px solid var(--border-default)" }}>
            <div className="flex justify-between text-sm mb-2">
              <span style={{ color: "var(--text-tertiary)" }}>Tiến độ hôm nay</span>
              <span className="font-medium" style={{ color: "#6366f1" }}>{data.lesson.actual_minutes}/{data.lesson.target_minutes} phút</span>
            </div>
            <div className="h-2 rounded-full overflow-hidden" style={{ background: "var(--border-default)" }}>
              <div className="h-full rounded-full" style={{ background: "#6366f1", width: `${Math.min((data.lesson.actual_minutes / data.lesson.target_minutes) * 100, 100)}%` }} />
            </div>
          </div>
        )}
      </div>

      {/* Learning path preview */}
      {data?.path ? (
        <div className="rounded-2xl p-6 mb-6" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>🛤️ Lộ trình: {data.path.name}</h2>
            <Link href="/placement/path" className="text-sm font-medium no-underline" style={{ color: "#6366f1" }}>Xem chi tiết →</Link>
          </div>
          <div className="space-y-3">
            {data.path.milestones?.slice(0, 3).map((m) => (
              <div key={m.order} className="flex items-center gap-3 p-3 rounded-lg" style={{ background: m.is_completed ? "rgba(16,185,129,.08)" : m.is_unlocked ? "rgba(99,102,241,.08)" : "var(--bg-interactive)", opacity: m.is_unlocked || m.is_completed ? 1 : 0.6 }}>
                <div className="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold" style={{ background: m.is_completed ? "#10b981" : m.is_unlocked ? "#6366f1" : "var(--border-default)", color: (m.is_completed || m.is_unlocked) ? "white" : "var(--text-tertiary)" }}>
                  {m.is_completed ? "✓" : m.order}
                </div>
                <span className="flex-1 text-sm" style={{ color: (m.is_unlocked || m.is_completed) ? "var(--text-primary)" : "var(--text-tertiary)" }}>{m.title}</span>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="rounded-2xl p-6 text-center mb-6" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
          <p className="mb-4" style={{ color: "var(--text-tertiary)" }}>Bạn chưa có lộ trình học tập</p>
          <Link href="/placement" className="px-6 py-3 rounded-xl text-sm font-medium text-white no-underline inline-block" style={{ background: "#6366f1" }}>Làm bài test để tạo lộ trình</Link>
        </div>
      )}

      {/* Quick actions */}
      <div className="grid grid-cols-2 gap-4">
        <Link href="/vocab/sets?tab=my" className="flex items-center gap-3 p-4 rounded-xl no-underline transition-all hover:translate-y-[-2px]" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
          <span className="text-2xl">📚</span><span className="font-medium text-sm" style={{ color: "var(--text-primary)" }}>Ôn từ vựng</span>
        </Link>
        <Link href="/exam" className="flex items-center gap-3 p-4 rounded-xl no-underline transition-all hover:translate-y-[-2px]" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
          <span className="text-2xl">📝</span><span className="font-medium text-sm" style={{ color: "var(--text-primary)" }}>Làm đề thi</span>
        </Link>
      </div>
    </div>
  );
}
