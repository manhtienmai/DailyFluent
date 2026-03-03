"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

interface LearnWord {
  id: number;
  word: string;
  reading: string;
  meaning: string;
  example: string;
  example_translation: string;
  audio_url: string;
}

export default function CourseLearnPage() {
  const params = useParams();
  const slug = params.slug as string;
  const setNumber = params.setNumber as string;

  const [words, setWords] = useState<LearnWord[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [phase, setPhase] = useState<"show" | "test">("show");
  const [userInput, setUserInput] = useState("");
  const [showResult, setShowResult] = useState(false);
  const [correct, setCorrect] = useState(false);
  const [score, setScore] = useState(0);
  const [done, setDone] = useState(false);

  const total = words.length;
  const current = words[currentIdx] || null;

  useEffect(() => {
    fetch(`/api/v1/vocab/courses/${slug}/set/${setNumber}/learn`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d) => { setWords(d.words || []); setLoading(false); })
      .catch(() => { setWords([]); setLoading(false); });
  }, [slug, setNumber]);

  const checkAnswer = useCallback(() => {
    if (!current) return;
    const isCorrect = userInput.trim().toLowerCase() === current.meaning.trim().toLowerCase();
    setCorrect(isCorrect);
    if (isCorrect) setScore((s) => s + 1);
    setShowResult(true);
  }, [current, userInput]);

  const next = useCallback(() => {
    if (currentIdx < total - 1) {
      setCurrentIdx((i) => i + 1);
      if (phase === "show") {
        // Stay in show phase
      } else {
        setUserInput("");
        setShowResult(false);
      }
    } else if (phase === "show") {
      setPhase("test");
      setCurrentIdx(0);
    } else {
      // Submit results
      fetch("/vocab/api/courses/learn-result/", {
        method: "POST", headers: { "Content-Type": "application/json" }, credentials: "include",
        body: JSON.stringify({ course_slug: slug, set_number: setNumber, score, total }),
      }).catch(() => {});
      setDone(true);
    }
  }, [currentIdx, total, phase, slug, setNumber, score]);

  if (loading) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Đang tải...</div>;

  return (
    <div style={{ padding: "24px", minHeight: "100vh" }}>
      <div className="max-w-lg mx-auto">
        <div className="flex items-center gap-3 mb-5">
          <Link href={`/vocab/courses/${slug}`} className="p-2 rounded-lg" style={{ color: "var(--text-secondary)" }}>
            <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M15 18l-6-6 6-6" /></svg>
          </Link>
          <div className="flex-1">
            <h1 className="font-bold text-lg" style={{ color: "var(--text-primary)" }}>{phase === "show" ? "📖 Học từ mới" : "📝 Kiểm tra"}</h1>
            <p className="text-xs" style={{ color: "var(--text-tertiary)" }}>Set {setNumber} • {currentIdx + 1}/{total}</p>
          </div>
        </div>

        {total > 0 && !done && (
          <div className="h-1.5 rounded-full mb-5 overflow-hidden" style={{ background: "var(--border-default)" }}>
            <div className="h-full rounded-full transition-all" style={{ width: `${((currentIdx + 1) / total) * 100}%`, background: phase === "show" ? "linear-gradient(90deg, #6366f1, #8b5cf6)" : "linear-gradient(90deg, #f59e0b, #d97706)" }} />
          </div>
        )}

        {total === 0 ? (
          <div className="text-center py-16" style={{ color: "var(--text-secondary)" }}>Chưa có từ.</div>
        ) : done ? (
          <div className="p-8 rounded-2xl text-center" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
            <div className="text-5xl mb-3">🎉</div>
            <h2 className="text-xl font-bold mb-2" style={{ color: "var(--text-primary)" }}>Hoàn thành!</h2>
            <div className="text-3xl font-bold mb-4" style={{ color: "var(--action-primary)" }}>{score}/{total}</div>
            <Link href={`/vocab/courses/${slug}`} className="px-5 py-2.5 rounded-xl text-sm font-semibold text-white" style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6)", textDecoration: "none" }}>Quay lại khóa học</Link>
          </div>
        ) : current && (
          <div className="p-6 rounded-2xl" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
            {phase === "show" ? (
              <>
                <div className="text-center mb-4">
                  <div className="text-3xl font-bold" style={{ fontFamily: "'Noto Sans JP', sans-serif", color: "var(--text-primary)" }}>{current.word}</div>
                  {current.reading && <div className="text-sm mt-1" style={{ fontFamily: "'Noto Sans JP', sans-serif", color: "var(--text-secondary)" }}>{current.reading}</div>}
                </div>
                <div className="text-base font-medium text-center mb-4" style={{ color: "var(--text-primary)" }}>{current.meaning}</div>
                {current.example && (
                  <div className="p-3 rounded-xl mb-4" style={{ background: "var(--bg-interactive)", border: "1px solid var(--border-subtle)" }}>
                    <div className="text-sm" style={{ fontFamily: "'Noto Sans JP', sans-serif", color: "var(--text-primary)" }}>{current.example}</div>
                    {current.example_translation && <div className="text-xs mt-1" style={{ color: "var(--text-secondary)" }}>{current.example_translation}</div>}
                  </div>
                )}
                <button onClick={next} className="w-full py-3 rounded-xl text-sm font-semibold text-white" style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6)" }}>
                  {currentIdx < total - 1 ? "Tiếp →" : "Bắt đầu kiểm tra →"}
                </button>
              </>
            ) : (
              <>
                <div className="text-2xl font-bold text-center mb-6" style={{ fontFamily: "'Noto Sans JP', sans-serif", color: "var(--text-primary)" }}>{current.word}</div>
                {!showResult ? (
                  <>
                    <input type="text" value={userInput} onChange={(e) => setUserInput(e.target.value)} onKeyDown={(e) => e.key === "Enter" && checkAnswer()} placeholder="Nhập nghĩa..." className="w-full p-3 rounded-xl text-sm border outline-none mb-3" style={{ background: "var(--bg-interactive)", borderColor: "var(--border-default)", color: "var(--text-primary)" }} />
                    <button onClick={checkAnswer} className="w-full py-2.5 rounded-xl text-sm font-semibold text-white" style={{ background: "linear-gradient(135deg, #f59e0b, #d97706)" }}>Xác nhận</button>
                  </>
                ) : (
                  <>
                    <div className="text-center mb-4">
                      <div className="text-lg font-semibold" style={{ color: correct ? "#16a34a" : "#dc2626" }}>{correct ? "✅ Chính xác!" : "❌ Chưa đúng"}</div>
                      {!correct && <div className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>Đáp án: {current.meaning}</div>}
                    </div>
                    <button onClick={next} className="w-full py-2.5 rounded-xl text-sm font-semibold text-white" style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6)" }}>
                      {currentIdx < total - 1 ? "Tiếp →" : "Xem kết quả"}
                    </button>
                  </>
                )}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
