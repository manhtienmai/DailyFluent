"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

interface ExamDetail {
  slug: string;
  title: string;
  description: string;
  question_count: number;
  duration_minutes: number;
  category: string;
  attempts: { id: number; score: number; total: number; created_at: string }[];
}

export default function ExamDetailPage() {
  const params = useParams();
  const slug = params.slug as string;

  const [data, setData] = useState<ExamDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/v1/exam/${slug}`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d: ExamDetail) => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, [slug]);

  if (loading) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Đang tải...</div>;
  if (!data) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Không tìm thấy đề thi. API chưa sẵn sàng.</div>;

  return (
    <div style={{ padding: "24px", minHeight: "100vh" }}>
      <div className="max-w-3xl mx-auto">
        <nav className="mb-5 flex items-center gap-2 text-sm" style={{ color: "var(--text-tertiary)" }}>
          <Link href="/exam" className="hover:underline">Luyện thi</Link>
          <span>/</span>
          <span style={{ color: "var(--text-primary)" }}>{data.title}</span>
        </nav>

        <div className="p-6 rounded-2xl mb-6" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
          <h1 className="text-2xl font-bold mb-2" style={{ color: "var(--text-primary)" }}>{data.title}</h1>
          {data.description && <p className="text-sm mb-4" style={{ color: "var(--text-secondary)" }}>{data.description}</p>}

          <div className="flex items-center gap-4 mb-6 text-sm" style={{ color: "var(--text-tertiary)" }}>
            <div className="flex items-center gap-1.5">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" /></svg>
              {data.question_count} câu
            </div>
            {data.duration_minutes > 0 && (
              <div className="flex items-center gap-1.5">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                {data.duration_minutes} phút
              </div>
            )}
          </div>

          <Link
            href={`/exam/${slug}/start`}
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl text-base font-semibold text-white"
            style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6)", textDecoration: "none", boxShadow: "0 4px 16px rgba(99,102,241,.35)" }}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" /><path strokeLinecap="round" strokeLinejoin="round" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            Bắt đầu làm bài
          </Link>
        </div>

        {/* Past attempts */}
        {data.attempts?.length > 0 && (
          <div className="p-5 rounded-2xl" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
            <h2 className="text-sm font-bold mb-4" style={{ color: "var(--text-primary)" }}>Lịch sử làm bài</h2>
            <div className="space-y-2">
              {data.attempts.map((a) => (
                <Link
                  key={a.id}
                  href={`/exam/session/${a.id}/result`}
                  className="flex items-center justify-between p-3 rounded-xl transition-all no-underline"
                  style={{ background: "var(--bg-interactive)", border: "1px solid var(--border-subtle)" }}
                >
                  <div>
                    <span className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{a.score}/{a.total}</span>
                    <span className="text-xs ml-2" style={{ color: "var(--text-tertiary)" }}>({Math.round(a.score / a.total * 100)}%)</span>
                  </div>
                  <span className="text-xs" style={{ color: "var(--text-tertiary)" }}>{new Date(a.created_at).toLocaleDateString("vi-VN")}</span>
                </Link>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
