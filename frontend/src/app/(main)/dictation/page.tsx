"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

interface Exercise { slug: string; title: string; description: string; difficulty: string; }

export default function DictationListPage() {
  const [exercises, setExercises] = useState<Exercise[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/v1/dictation", { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((d: Exercise[]) => { setExercises(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Đang tải...</div>;

  const diffColors: Record<string, string> = { easy: "#10b981", medium: "#f59e0b", hard: "#ef4444" };

  return (
    <div style={{ maxWidth: 900, margin: "0 auto", padding: "2rem 1rem" }}>
      <h1 className="text-2xl font-bold mb-6" style={{ color: "var(--text-primary)" }}>🎧 Dictation</h1>
      <div className="space-y-3">
        {exercises.map((e) => (
          <Link key={e.slug} href={`/dictation/${e.slug}`} className="flex items-center gap-4 p-5 rounded-2xl no-underline transition-all hover:translate-y-[-2px]" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
            <div className="w-12 h-12 rounded-xl flex items-center justify-center text-2xl" style={{ background: "rgba(99,102,241,.1)" }}>🎧</div>
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-sm truncate" style={{ color: "var(--text-primary)" }}>{e.title}</h3>
              <p className="text-xs" style={{ color: "var(--text-tertiary)" }}>{e.description}</p>
            </div>
            {e.difficulty && <span className="text-xs font-semibold px-3 py-1 rounded-full" style={{ background: `${diffColors[e.difficulty] || "#6b7280"}20`, color: diffColors[e.difficulty] || "#6b7280" }}>{e.difficulty}</span>}
          </Link>
        ))}
        {!exercises.length && <p className="text-center py-8" style={{ color: "var(--text-tertiary)" }}>Chưa có bài dictation nào.</p>}
      </div>
    </div>
  );
}
