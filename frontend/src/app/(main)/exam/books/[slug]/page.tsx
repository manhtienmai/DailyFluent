"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

interface BookExam {
  slug: string;
  title: string;
  question_count: number;
  duration_minutes: number;
  completed: boolean;
  best_score: number;
}

interface BookData {
  slug: string;
  title: string;
  description: string;
  level: string;
  exams: BookExam[];
}

export default function ExamBookDetailPage() {
  const params = useParams();
  const slug = params.slug as string;

  const [book, setBook] = useState<BookData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/v1/exam/books/${slug}`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d: BookData) => { setBook(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, [slug]);

  if (loading) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Đang tải...</div>;
  if (!book) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Không tìm thấy. API chưa sẵn sàng.</div>;

  return (
    <div style={{ padding: "24px", minHeight: "100vh" }}>
      <div className="max-w-4xl mx-auto">
        <nav className="mb-5 flex items-center gap-2 text-sm" style={{ color: "var(--text-tertiary)" }}>
          <Link href="/exam" className="hover:underline">Luyện thi</Link>
          <span>/</span>
          <Link href="/exam/books" className="hover:underline">Sách đề</Link>
          <span>/</span>
          <span style={{ color: "var(--text-primary)" }}>{book.title}</span>
        </nav>

        <div className="mb-6">
          <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>{book.title}</h1>
          {book.description && <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>{book.description}</p>}
        </div>

        <div className="space-y-2">
          {book.exams?.map((e, i) => (
            <Link key={e.slug} href={`/exam/${e.slug}`} className="flex items-center gap-4 p-4 rounded-xl transition-all hover:translate-y-[-2px] no-underline" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
              <span className="w-10 h-10 rounded-xl flex items-center justify-center font-bold text-sm flex-shrink-0" style={{
                background: e.completed ? "rgba(16,185,129,.12)" : "var(--bg-interactive)",
                color: e.completed ? "#059669" : "var(--text-secondary)",
                border: `1px solid ${e.completed ? "rgba(16,185,129,.25)" : "var(--border-default)"}`,
              }}>{e.completed ? "✓" : i + 1}</span>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-semibold truncate" style={{ color: "var(--text-primary)" }}>{e.title}</div>
                <div className="text-xs" style={{ color: "var(--text-tertiary)" }}>{e.question_count} câu{e.duration_minutes > 0 && ` · ${e.duration_minutes} phút`}</div>
              </div>
              {e.best_score > 0 && <span className="text-xs font-bold" style={{ color: "#6366f1" }}>{e.best_score}%</span>}
            </Link>
          ))}
          {(!book.exams || book.exams.length === 0) && (
            <div className="text-center py-12" style={{ color: "var(--text-tertiary)" }}>Chưa có đề thi.</div>
          )}
        </div>
      </div>
    </div>
  );
}
