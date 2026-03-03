"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

interface QuizQuestion {
  id: number;
  word: string;
  reading: string;
  choices: string[];
  correct_answer: string;
}

export default function CourseQuizPage() {
  const params = useParams();
  const slug = params.slug as string;
  const setNumber = params.setNumber as string;

  const [questions, setQuestions] = useState<QuizQuestion[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [selected, setSelected] = useState<string | null>(null);
  const [answered, setAnswered] = useState(false);
  const [score, setScore] = useState(0);
  const [done, setDone] = useState(false);

  const total = questions.length;
  const current = questions[currentIdx] || null;

  useEffect(() => {
    fetch(`/api/v1/vocab/courses/${slug}/set/${setNumber}/quiz`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d) => { setQuestions(d.questions || []); setLoading(false); })
      .catch(() => { setQuestions([]); setLoading(false); });
  }, [slug, setNumber]);

  const check = useCallback((choice: string) => {
    if (answered || !current) return;
    setSelected(choice);
    setAnswered(true);
    if (choice === current.correct_answer) setScore((s) => s + 1);
  }, [answered, current]);

  const next = useCallback(() => {
    if (currentIdx < total - 1) {
      setCurrentIdx((i) => i + 1);
      setSelected(null);
      setAnswered(false);
    } else {
      fetch("/vocab/api/courses/quiz-result/", {
        method: "POST", headers: { "Content-Type": "application/json" }, credentials: "include",
        body: JSON.stringify({ course_slug: slug, set_number: setNumber, score, total }),
      }).catch(() => {});
      setDone(true);
    }
  }, [currentIdx, total, slug, setNumber, score]);

  if (loading) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Đang tải...</div>;

  return (
    <div style={{ padding: "24px", minHeight: "100vh" }}>
      <div className="max-w-lg mx-auto">
        <div className="flex items-center gap-3 mb-5">
          <Link href={`/vocab/courses/${slug}`} className="p-2 rounded-lg" style={{ color: "var(--text-secondary)" }}>
            <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M15 18l-6-6 6-6" /></svg>
          </Link>
          <h1 className="font-bold text-lg flex-1" style={{ color: "var(--text-primary)" }}>🧪 Quiz Set {setNumber}</h1>
          {!done && <span className="text-xs" style={{ color: "var(--text-tertiary)" }}>{currentIdx + 1}/{total}</span>}
        </div>

        {!done && total > 0 && (
          <div className="h-1.5 rounded-full mb-5 overflow-hidden" style={{ background: "var(--border-default)" }}>
            <div className="h-full rounded-full transition-all" style={{ width: `${(currentIdx / total) * 100}%`, background: "linear-gradient(90deg, #10b981, #34d399)" }} />
          </div>
        )}

        {total === 0 ? (
          <div className="text-center py-16" style={{ color: "var(--text-secondary)" }}>Chưa có câu hỏi.</div>
        ) : done ? (
          <div className="p-8 rounded-2xl text-center" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
            <div className="text-5xl font-bold mb-2" style={{ color: "var(--text-primary)" }}>{score}/{total}</div>
            <div className="text-lg mb-1" style={{ color: "var(--text-secondary)" }}>{Math.round((score / total) * 100)}%</div>
            <div className="text-xl mb-6">{score === total ? "🎉 Hoàn hảo!" : score >= total * 0.7 ? "👏 Tốt!" : "💪 Cố lên!"}</div>
            <Link href={`/vocab/courses/${slug}`} className="px-5 py-2.5 rounded-xl text-sm font-semibold text-white" style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6)", textDecoration: "none" }}>Quay lại</Link>
          </div>
        ) : current && (
          <div className="p-6 rounded-2xl" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
            <div className="text-2xl font-bold text-center mb-2" style={{ fontFamily: "'Noto Sans JP', sans-serif", color: "var(--text-primary)" }}>{current.word}</div>
            {current.reading && <div className="text-sm text-center mb-6" style={{ fontFamily: "'Noto Sans JP', sans-serif", color: "var(--text-secondary)" }}>{current.reading}</div>}
            <div className="space-y-2 mb-4">
              {current.choices?.map((c, i) => {
                const isCorrect = answered && c === current.correct_answer;
                const isWrong = answered && selected === c && c !== current.correct_answer;
                return (
                  <button key={i} onClick={() => check(c)} disabled={answered} className="w-full text-left p-3 rounded-xl border transition-all" style={{
                    background: isCorrect ? "rgba(209,250,229,.7)" : isWrong ? "rgba(254,226,226,.7)" : selected === c ? "var(--bg-interactive)" : "var(--bg-surface)",
                    borderColor: isCorrect ? "#34d399" : isWrong ? "#f87171" : "var(--border-default)",
                    color: "var(--text-primary)", opacity: answered && !isCorrect && selected !== c ? 0.5 : 1,
                  }}>
                    {c}
                  </button>
                );
              })}
            </div>
            {answered && (
              <button onClick={next} className="w-full py-2.5 rounded-xl text-sm font-semibold text-white" style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6)" }}>
                {currentIdx < total - 1 ? "Tiếp →" : "Xem kết quả"}
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
