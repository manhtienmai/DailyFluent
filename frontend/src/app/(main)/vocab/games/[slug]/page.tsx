"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

interface GameQuestion {
  id: number;
  word: string;
  reading: string;
  correct_answer: string;
  choices: string[];
  audio_url?: string;
}

type GameSlug = "mcq" | "matching" | "listening" | "fill" | "dictation";

const GAME_META: Record<GameSlug, { title: string; icon: string; color: string }> = {
  mcq: { title: "Trắc nghiệm", icon: "🎯", color: "#6366f1" },
  matching: { title: "Nối từ", icon: "🔗", color: "#10b981" },
  listening: { title: "Nghe và chọn", icon: "🎧", color: "#f59e0b" },
  fill: { title: "Điền từ", icon: "✏️", color: "#ec4899" },
  dictation: { title: "Chính tả", icon: "📝", color: "#14b8a6" },
};

export default function GamePlayPage() {
  const params = useParams();
  const slug = params.slug as GameSlug;
  const meta = GAME_META[slug] || GAME_META.mcq;

  const [questions, setQuestions] = useState<GameQuestion[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [selected, setSelected] = useState<string | null>(null);
  const [answered, setAnswered] = useState(false);
  const [score, setScore] = useState(0);
  const [showResults, setShowResults] = useState(false);
  const [fillInput, setFillInput] = useState("");
  const [lives, setLives] = useState(3);

  const total = questions.length;
  const current = questions[currentIdx] || null;

  useEffect(() => {
    fetch(`/api/v1/vocab/games/${slug}`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d) => { setQuestions(d.questions || []); setLives(d.lives ?? 3); setLoading(false); })
      .catch(() => { setQuestions([]); setLoading(false); });
  }, [slug]);

  const checkAnswer = useCallback((answer: string) => {
    if (answered || !current) return;
    setSelected(answer);
    setAnswered(true);
    const correct = answer.toLowerCase().trim() === current.correct_answer.toLowerCase().trim();
    if (correct) setScore((s) => s + 1);
    else setLives((l) => l - 1);
  }, [answered, current]);

  const next = useCallback(() => {
    if (lives <= 0 || currentIdx >= total - 1) {
      setShowResults(true);
    } else {
      setCurrentIdx((i) => i + 1);
      setSelected(null);
      setAnswered(false);
      setFillInput("");
    }
  }, [lives, currentIdx, total]);

  if (loading) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Đang tải...</div>;

  return (
    <div style={{ padding: "24px", minHeight: "100vh" }}>
      <div className="max-w-lg mx-auto">
        {/* Header */}
        <div className="flex items-center gap-3 mb-5">
          <Link href="/vocab/games" className="p-2 rounded-lg" style={{ color: "var(--text-secondary)" }}>
            <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M15 18l-6-6 6-6" /></svg>
          </Link>
          <div className="flex-1">
            <h1 className="font-bold text-lg" style={{ color: "var(--text-primary)" }}>{meta.icon} {meta.title}</h1>
          </div>
          <div className="flex gap-1">
            {Array.from({ length: 3 }).map((_, i) => (
              <span key={i} className="text-lg">{i < lives ? "❤️" : "🖤"}</span>
            ))}
          </div>
        </div>

        {/* Progress */}
        {!showResults && total > 0 && (
          <div className="mb-5">
            <div className="flex justify-between text-xs mb-1.5" style={{ color: "var(--text-secondary)" }}>
              <span>Câu {currentIdx + 1} / {total}</span>
              <span>{score} đúng</span>
            </div>
            <div className="h-2 rounded-full overflow-hidden" style={{ background: "var(--border-default)" }}>
              <div className="h-full rounded-full transition-all" style={{ width: `${(currentIdx / total) * 100}%`, background: `linear-gradient(90deg, ${meta.color}, ${meta.color}cc)` }} />
            </div>
          </div>
        )}

        {total === 0 && !loading ? (
          <div className="text-center py-16" style={{ color: "var(--text-secondary)" }}>
            <div className="text-5xl mb-4">{meta.icon}</div>
            <p className="text-lg font-medium">Chưa có câu hỏi</p>
            <p className="text-sm mt-1">API endpoint chưa sẵn sàng.</p>
          </div>
        ) : showResults ? (
          /* Results */
          <div className="p-8 rounded-2xl text-center" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
            <div className="text-5xl font-bold mb-2" style={{ color: "var(--text-primary)" }}>{score}/{total}</div>
            <div className="text-lg mb-1" style={{ color: "var(--text-secondary)" }}>{Math.round((score / total) * 100)}%</div>
            <div className="text-xl mb-6">{score === total ? "🎉 Hoàn hảo!" : score >= total * 0.7 ? "👏 Tốt!" : "💪 Cố lên!"}</div>
            <div className="flex justify-center gap-3">
              <button onClick={() => window.location.reload()} className="px-5 py-2.5 rounded-xl text-sm font-semibold" style={{ background: "var(--bg-interactive)", color: "var(--text-primary)", border: "1px solid var(--border-default)" }}>Chơi lại</button>
              <Link href="/vocab/games" className="px-5 py-2.5 rounded-xl text-sm font-semibold text-white" style={{ background: `linear-gradient(135deg, ${meta.color}, ${meta.color}cc)`, textDecoration: "none" }}>Về trang chủ</Link>
            </div>
          </div>
        ) : current && (
          /* Question card */
          <div className="p-6 rounded-2xl" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
            {current.audio_url && slug === "listening" && (
              <div className="mb-4"><audio controls className="w-full" style={{ height: "36px" }}><source src={current.audio_url} type="audio/mpeg" /></audio></div>
            )}

            <p className="text-2xl font-bold text-center mb-6" style={{ fontFamily: "'Noto Sans JP', sans-serif", color: "var(--text-primary)" }}>
              {slug === "fill" ? current.word.replace(/./g, (c, i) => i === 0 ? c : " _") : current.word}
            </p>
            {current.reading && <p className="text-sm text-center mb-4" style={{ fontFamily: "'Noto Sans JP', sans-serif", color: "var(--text-secondary)" }}>{current.reading}</p>}

            {/* Fill mode */}
            {slug === "fill" || slug === "dictation" ? (
              <div className="mb-4">
                <input
                  type="text"
                  value={fillInput}
                  onChange={(e) => setFillInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && !answered && checkAnswer(fillInput)}
                  disabled={answered}
                  placeholder={slug === "dictation" ? "Nghe và viết lại..." : "Điền từ đầy đủ..."}
                  className="w-full p-3 rounded-xl text-sm border outline-none transition-all"
                  style={{ background: "var(--bg-interactive)", borderColor: "var(--border-default)", color: "var(--text-primary)", fontFamily: "'Noto Sans JP', sans-serif" }}
                />
                {!answered && (
                  <button onClick={() => checkAnswer(fillInput)} className="w-full mt-3 py-2.5 rounded-xl text-sm font-semibold text-white" style={{ background: `linear-gradient(135deg, ${meta.color}, ${meta.color}cc)` }}>
                    Xác nhận
                  </button>
                )}
              </div>
            ) : (
              /* MCQ / Listening choices */
              <div className="space-y-2 mb-4">
                {current.choices?.map((c, i) => {
                  const isCorrect = answered && c.toLowerCase().trim() === current.correct_answer.toLowerCase().trim();
                  const isWrong = answered && selected === c && !isCorrect;
                  return (
                    <button key={i} onClick={() => checkAnswer(c)} disabled={answered}
                      className="w-full text-left p-3 rounded-xl border transition-all"
                      style={{
                        background: isCorrect ? "rgba(209,250,229,.7)" : isWrong ? "rgba(254,226,226,.7)" : selected === c ? "var(--bg-interactive)" : "var(--bg-surface)",
                        borderColor: isCorrect ? "#34d399" : isWrong ? "#f87171" : "var(--border-default)",
                        color: "var(--text-primary)",
                        opacity: answered && !isCorrect && selected !== c ? 0.5 : 1,
                      }}
                    >
                      {c}
                    </button>
                  );
                })}
              </div>
            )}

            {/* Feedback + Next */}
            {answered && (
              <div className="mt-4">
                <div className="text-sm font-semibold mb-3" style={{ color: (selected || fillInput).toLowerCase().trim() === current.correct_answer.toLowerCase().trim() ? "#16a34a" : "#dc2626" }}>
                  {(selected || fillInput).toLowerCase().trim() === current.correct_answer.toLowerCase().trim() ? "✅ Chính xác!" : `❌ Đáp án: ${current.correct_answer}`}
                </div>
                <button onClick={next} className="w-full py-2.5 rounded-xl text-sm font-semibold text-white" style={{ background: `linear-gradient(135deg, ${meta.color}, ${meta.color}cc)` }}>
                  {currentIdx < total - 1 && lives > 0 ? "Câu tiếp →" : "Xem kết quả"}
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
