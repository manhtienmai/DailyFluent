"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

interface ToeicExam {
  slug: string;
  title: string;
  question_count: number;
  duration_minutes: number;
  category: string;
  best_score: number;
}

export default function ToeicListPage() {
  const [exams, setExams] = useState<ToeicExam[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/v1/exam/toeic", { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d) => { setExams(Array.isArray(d) ? d : []); setLoading(false); })
      .catch(() => { setExams([]); setLoading(false); });
  }, []);

  return (
    <div style={{ padding: "24px", minHeight: "100vh" }}>
      <div className="max-w-5xl mx-auto">
        <nav className="mb-5 flex items-center gap-2 text-sm" style={{ color: "var(--text-tertiary)" }}>
          <Link href="/exam" className="hover:underline">Luyện thi</Link>
          <span>/</span>
          <span style={{ color: "var(--text-primary)" }}>TOEIC</span>
        </nav>

        <div className="mb-6">
          <h1 className="text-2xl font-bold mb-1" style={{ color: "var(--text-primary)" }}>📝 TOEIC Practice</h1>
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>Luyện đề TOEIC Reading & Listening</p>
        </div>

        {loading ? (
          <div className="text-center py-16" style={{ color: "var(--text-tertiary)" }}>Đang tải...</div>
        ) : exams.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {exams.map((e) => (
              <Link key={e.slug} href={`/exam/${e.slug}`} className="block p-5 rounded-2xl transition-all hover:translate-y-[-3px] no-underline" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
                <h3 className="text-sm font-bold mb-1" style={{ color: "var(--text-primary)" }}>{e.title}</h3>
                <div className="flex items-center gap-3 text-xs" style={{ color: "var(--text-tertiary)" }}>
                  <span>{e.question_count} câu</span>
                  {e.duration_minutes > 0 && <span>{e.duration_minutes} phút</span>}
                  {e.best_score > 0 && <span style={{ color: "#6366f1", fontWeight: 700 }}>Best: {e.best_score}%</span>}
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <div className="text-center py-16" style={{ color: "var(--text-secondary)" }}>
            <div className="text-5xl mb-4">📝</div>
            <p>Chưa có đề TOEIC.</p>
          </div>
        )}
      </div>
    </div>
  );
}
