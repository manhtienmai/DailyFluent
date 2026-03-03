"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

interface ResultQuestion {
  id: number;
  text: string;
  user_answer: string;
  correct_answer: string;
  is_correct: boolean;
  explanation: string;
  choices: { key: string; text: string }[];
}

interface ResultData {
  session_id: number;
  exam_title: string;
  score: number;
  total: number;
  percentage: number;
  questions: ResultQuestion[];
}

export default function ExamResultPage() {
  const params = useParams();
  const sessionId = params.sessionId as string;

  const [data, setData] = useState<ResultData | null>(null);
  const [loading, setLoading] = useState(true);
  const [showWrong, setShowWrong] = useState(false);

  useEffect(() => {
    fetch(`/api/v1/exam/session/${sessionId}/result`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d: ResultData) => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, [sessionId]);

  if (loading) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Đang tải kết quả...</div>;
  if (!data) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Không tìm thấy. API chưa sẵn sàng.</div>;

  const rating = data.percentage >= 90 ? "🎉 Xuất sắc!" : data.percentage >= 70 ? "👏 Tốt lắm!" : data.percentage >= 50 ? "💪 Khá!" : "📖 Cần ôn lại!";
  const filtered = showWrong ? data.questions.filter((q) => !q.is_correct) : data.questions;

  return (
    <div style={{ padding: "24px", minHeight: "100vh" }}>
      <div className="max-w-3xl mx-auto">
        <nav className="mb-5 flex items-center gap-2 text-sm" style={{ color: "var(--text-tertiary)" }}>
          <Link href="/exam" className="hover:underline">Luyện thi</Link>
          <span>/</span>
          <span style={{ color: "var(--text-primary)" }}>Kết quả</span>
        </nav>

        {/* Score card */}
        <div className="p-6 rounded-2xl mb-6 text-center" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
          <h1 className="text-lg font-bold mb-4" style={{ color: "var(--text-primary)" }}>{data.exam_title}</h1>
          <div className="text-5xl font-extrabold mb-1" style={{ color: data.percentage >= 70 ? "#10b981" : data.percentage >= 50 ? "#f59e0b" : "#ef4444" }}>{data.percentage}%</div>
          <div className="text-sm mb-2" style={{ color: "var(--text-secondary)" }}>{data.score} / {data.total} câu đúng</div>
          <div className="h-2.5 rounded-full mx-auto mb-4 max-w-xs overflow-hidden" style={{ background: "var(--border-default)" }}>
            <div className="h-full rounded-full transition-all" style={{ width: `${data.percentage}%`, background: data.percentage >= 70 ? "#10b981" : data.percentage >= 50 ? "#f59e0b" : "#ef4444" }} />
          </div>
          <div className="text-xl mb-4">{rating}</div>
          <div className="flex justify-center gap-3">
            <Link href="/exam" className="px-4 py-2 rounded-xl text-sm font-semibold" style={{ background: "var(--bg-interactive)", color: "var(--text-primary)", border: "1px solid var(--border-default)", textDecoration: "none" }}>Về trang thi</Link>
            {data.questions.some((q) => !q.is_correct) && (
              <Link href={`/exam/session/${sessionId}/redo`} className="px-4 py-2 rounded-xl text-sm font-semibold text-white" style={{ background: "linear-gradient(135deg, #f59e0b, #d97706)", textDecoration: "none" }}>Làm lại câu sai</Link>
            )}
          </div>
        </div>

        {/* Filter */}
        <div className="flex gap-2 mb-4">
          <button onClick={() => setShowWrong(false)} className="px-3 py-1.5 rounded-lg text-xs font-semibold" style={{
            background: !showWrong ? "linear-gradient(135deg, #6366f1, #8b5cf6)" : "var(--bg-interactive)",
            color: !showWrong ? "#fff" : "var(--text-secondary)",
            border: !showWrong ? "none" : "1px solid var(--border-default)",
          }}>Tất cả ({data.total})</button>
          <button onClick={() => setShowWrong(true)} className="px-3 py-1.5 rounded-lg text-xs font-semibold" style={{
            background: showWrong ? "linear-gradient(135deg, #ef4444, #f87171)" : "var(--bg-interactive)",
            color: showWrong ? "#fff" : "var(--text-secondary)",
            border: showWrong ? "none" : "1px solid var(--border-default)",
          }}>Sai ({data.total - data.score})</button>
        </div>

        {/* Questions review */}
        <div className="space-y-3">
          {filtered.map((q, i) => (
            <div key={q.id} className="p-4 rounded-2xl" style={{ background: "var(--bg-surface)", border: `1px solid ${q.is_correct ? "rgba(16,185,129,.25)" : "rgba(239,68,68,.25)"}` }}>
              <div className="flex items-start gap-2 mb-3">
                <span className="text-sm">{q.is_correct ? "✅" : "❌"}</span>
                <p className="text-sm flex-1" style={{ color: "var(--text-primary)" }}>{q.text}</p>
              </div>
              <div className="space-y-1.5 mb-2">
                {q.choices?.map((c) => (
                  <div key={c.key} className="flex items-center gap-2 text-xs p-2 rounded-lg" style={{
                    background: c.key === q.correct_answer ? "rgba(209,250,229,.5)" : c.key === q.user_answer && !q.is_correct ? "rgba(254,226,226,.5)" : "transparent",
                    color: "var(--text-primary)",
                  }}>
                    <span className="font-bold w-5">{c.key}</span>
                    <span>{c.text}</span>
                    {c.key === q.correct_answer && <span className="ml-auto text-[10px] font-bold" style={{ color: "#16a34a" }}>✓</span>}
                    {c.key === q.user_answer && c.key !== q.correct_answer && <span className="ml-auto text-[10px] font-bold" style={{ color: "#dc2626" }}>✗</span>}
                  </div>
                ))}
              </div>
              {q.explanation && <div className="text-xs p-2 rounded-lg" style={{ background: "var(--bg-interactive)", color: "var(--text-secondary)" }}>{q.explanation}</div>}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
