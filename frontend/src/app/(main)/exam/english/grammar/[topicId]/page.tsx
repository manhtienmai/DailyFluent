"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { submitQuizResult, getLatestResult, type QuizResultResponse } from "@/lib/api-quiz-result";
import { getUserPref, setUserPref } from "@/lib/user-prefs";

/* ─── TYPES ────────────────────────────────────────────── */
interface GrammarLesson {
  title: string;
  title_vi: string;
  emoji: string;
  sections: { heading: string; content: string }[];
  formulas: { name: string; formula: string; example: string; exampleVi: string }[];
  exercises: { question: string; options: string[]; correct: number; explanation: string; audio_urls?: Record<string, string> }[];
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

/* ═══════════════════════════════════════════════════════ */
export default function GrammarDetailPage() {
  const params = useParams();
  const topicId = params.topicId as string;

  const [lesson, setLesson] = useState<GrammarLesson | null>(null);
  const [loading, setLoading] = useState(true);
  const [showExercise, setShowExercise] = useState(false);
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [revealed, setRevealed] = useState<Set<number>>(new Set());
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [lastResult, setLastResult] = useState<QuizResultResponse | null>(null);

  // TTS audio playback (must be before any early returns)
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [playingWord, setPlayingWord] = useState<string | null>(null);

  // Load lesson from API
  useEffect(() => {
    setLoading(true);
    fetch(`${API_BASE}/api/v1/exam/english/grammar-topics/${topicId}`)
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (data) {
          setLesson({
            title: data.title,
            title_vi: data.title_vi,
            emoji: data.emoji,
            sections: data.sections || [],
            formulas: data.formulas || [],
            exercises: data.exercises || [],
          });
          // Track visited grammar topics via API
          getUserPref<string[]>("grammar_visited").then(async (arr) => {
            const visited: string[] = Array.isArray(arr) ? arr : [];
            if (!visited.includes(topicId)) {
              visited.push(topicId);
              await setUserPref("grammar_visited", visited);
            }
          }).catch(() => {});
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [topicId]);

  // Load latest result on mount
  useEffect(() => {
    getLatestResult("grammar", topicId).then(r => setLastResult(r));
  }, [topicId]);

  // Auto-submit when all questions answered
  const allAnswered = lesson ? Object.keys(answers).length === lesson.exercises.length && revealed.size === lesson.exercises.length : false;
  useEffect(() => {
    if (!allAnswered || !lesson || saved) return;
    (async () => {
      setSaving(true);
      const cc = lesson.exercises.filter((ex, i) => answers[i] === ex.correct).length;
      const s10 = lesson.exercises.length > 0 ? Math.round(cc / lesson.exercises.length * 100) / 10 : 0;
      const detail = lesson.exercises.map((ex, i) => ({
        q: i, selected: answers[i] ?? -1, correct: ex.correct, is_correct: answers[i] === ex.correct,
      }));
      const res = await submitQuizResult({
        quiz_type: "grammar", quiz_id: topicId,
        total_questions: lesson.exercises.length, correct_count: cc,
        score: s10, answers_detail: detail,
      });
      setSaving(false);
      if (res) { setSaved(true); setLastResult(res); }
    })();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [allAnswered]);

  if (loading) {
    return (
      <div className="gd-page" style={{ textAlign: "center", paddingTop: 48 }}>
        <div style={{ fontSize: 48, marginBottom: 16 }}>⏳</div>
        <p style={{ fontSize: 14, color: "var(--text-tertiary)" }}>Đang tải...</p>
      </div>
    );
  }

  if (!lesson) {
    return (
      <div className="gd-page" style={{ textAlign: "center", paddingTop: 48 }}>
        <div style={{ fontSize: 48, marginBottom: 16 }}>📚</div>
        <h2 style={{ fontSize: 20, fontWeight: 700, color: "var(--text-primary)", marginBottom: 8 }}>Chủ đề đang được xây dựng</h2>
        <p style={{ fontSize: 14, color: "var(--text-tertiary)", marginBottom: 16 }}>Chủ đề &quot;{topicId}&quot; sẽ sớm được cập nhật.</p>
        <Link href="/exam/english/grammar" style={{ color: "var(--action-primary)", fontSize: 14 }}>← Quay lại danh sách</Link>
      </div>
    );
  }

  const answeredCount = Object.keys(answers).length;
  const correctCount = lesson.exercises.filter((ex, i) => answers[i] === ex.correct).length;
  const score10 = lesson.exercises.length > 0 ? Math.round(correctCount / lesson.exercises.length * 100) / 10 : 0;

  const handleSelectAnswer = (qIdx: number, optIdx: number) => {
    if (revealed.has(qIdx)) return; // already answered
    setAnswers(prev => ({ ...prev, [qIdx]: optIdx }));
    setRevealed(prev => new Set(prev).add(qIdx));
  };

  // TTS audio playback helper
  const playAudio = (url: string, word: string) => {
    if (audioRef.current) { audioRef.current.pause(); }
    const audio = new Audio(url);
    audioRef.current = audio;
    setPlayingWord(word);
    audio.onended = () => setPlayingWord(null);
    audio.onerror = () => setPlayingWord(null);
    audio.play();
  };

  return (
    <div className="gd-page">
      <nav className="gd-breadcrumb">
        <Link href="/exam/english">English Lớp 10</Link>
        <span>/</span>
        <Link href="/exam/english/grammar">Ngữ pháp</Link>
        <span>/</span>
        <span>{lesson.title}</span>
      </nav>

      <div style={{ marginBottom: 24 }}>
        <h1 className="gd-title" style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ fontSize: 24 }}>{lesson.emoji}</span>
          {lesson.title}
        </h1>
        <p style={{ fontSize: 14, color: "var(--text-secondary)", margin: 0 }}>{lesson.title_vi}</p>
      </div>

      {/* Theory — seamless flow */}
      <div className="gd-content">
        {lesson.sections.map((sec, i) => (
          <div key={i} className="gd-section">
            <h2 className="gd-section-heading">
              <span className="gd-accent-bar" />
              {sec.heading}
            </h2>
            <div className="gd-section-body">
              {sec.content.split(/(\*\*.*?\*\*)/).map((part, j) =>
                part.startsWith("**") && part.endsWith("**")
                  ? <strong key={j} style={{ fontWeight: 700, color: "var(--text-primary)" }}>{part.slice(2, -2)}</strong>
                  : part
              )}
            </div>
          </div>
        ))}

        {/* Formulas inline */}
        {lesson.formulas.length > 0 && (
          <div className="gd-section">
            <h2 className="gd-section-heading">
              <span className="gd-accent-bar" />
              📐 Công thức tóm tắt
            </h2>
            <div className="gd-formulas">
              {lesson.formulas.map((f, i) => (
                <div key={i} className="gd-formula-card">
                  <p className="gd-formula-name">{f.name}</p>
                  <p className="gd-formula-text">{f.formula}</p>
                  <p style={{ fontSize: 12, color: "var(--text-secondary)", fontStyle: "italic", margin: "8px 0 0" }}>✏️ {f.example}</p>
                  <p style={{ fontSize: 11, color: "var(--text-tertiary)", margin: "2px 0 0" }}>→ {f.exampleVi}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Exercise toggle */}
      {!showExercise ? (
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <button className="gd-start-btn" onClick={() => setShowExercise(true)}>
            ✍️ Làm bài tập ({lesson.exercises.length} câu)
          </button>
          {lastResult && (
            <span style={{ fontSize: 12, color: "var(--text-tertiary)" }}>
              Lần trước: <b style={{ color: lastResult.score >= 8 ? "#16a34a" : lastResult.score >= 6 ? "#d97706" : "#dc2626" }}>{lastResult.score}/10</b>
              <span style={{ marginLeft: 4 }}>({lastResult.correct_count}/{lastResult.total_questions})</span>
            </span>
          )}
        </div>
      ) : (
        <div>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
            <h2 style={{ fontSize: 18, fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>✍️ Bài tập</h2>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              {answeredCount > 0 && (
                <span style={{ fontSize: 12, color: "var(--text-tertiary)" }}>
                  {correctCount}/{answeredCount} đúng
                </span>
              )}
              <button className="gd-hide-btn" onClick={() => setShowExercise(false)}>Ẩn bài tập</button>
            </div>
          </div>

          {/* Score box when all done */}
          {allAnswered && (
            <div className="gd-score-box">
              <div className="gd-score-num" style={{ color: score10 >= 8 ? "#10b981" : score10 >= 6 ? "#f59e0b" : "#ef4444" }}>
                {score10}<span style={{ fontSize: 20, color: "var(--text-tertiary)" }}>/10</span>
              </div>
              <p style={{ fontSize: 13, color: "var(--text-secondary)", margin: 0 }}>{correctCount}/{lesson.exercises.length} câu đúng</p>
            </div>
          )}

          <div className="gd-content">
            {lesson.exercises.map((ex, i) => {
              const selected = answers[i];
              const isRevealed = revealed.has(i);
              const isCorrect = selected === ex.correct;
              return (
                <div key={i} className="gd-ex-item">
                  <div className="gd-ex-header">
                    <span className={`gd-ex-num ${isRevealed ? (isCorrect ? "correct" : "wrong") : ""}`}>{i + 1}</span>
                    <p className="gd-ex-question">{ex.question}</p>
                  </div>
                  <div className="gd-ex-options">
                    {ex.options.map((opt, j) => {
                      let cls = "gd-ex-opt";
                      if (isRevealed) {
                        if (j === ex.correct) cls += " correct";
                        else if (j === selected) cls += " wrong";
                        else cls += " dim";
                      } else if (j === selected) cls += " selected";
                      const audioUrl = ex.audio_urls?.[opt];
                      return (
                        <div key={j} style={{ display: "flex", alignItems: "center", gap: 4 }}>
                          <button onClick={() => handleSelectAnswer(i, j)} disabled={isRevealed} className={cls} style={{ flex: 1 }}>
                            <span className={`gd-ex-key ${isRevealed && j === ex.correct ? "correct" : isRevealed && j === selected ? "wrong" : j === selected ? "selected" : ""}`}>
                              {String.fromCharCode(65 + j)}
                            </span>
                            {opt}
                          </button>
                          {audioUrl && (
                            <button
                              className="gd-audio-btn"
                              onClick={(e) => { e.stopPropagation(); playAudio(audioUrl, opt); }}
                              title={`Nghe phát âm: ${opt}`}
                            >
                              {playingWord === opt ? "🔊" : "🔈"}
                            </button>
                          )}
                        </div>
                      );
                    })}
                  </div>
                  {isRevealed && (
                    <div className="gd-ex-explain">💡 {ex.explanation}</div>
                  )}
                </div>
              );
            })}
          </div>

          <div style={{ display: "flex", justifyContent: "center", gap: 12, marginTop: 20, alignItems: "center" }}>
            {allAnswered && (
              <button className="gd-retry-btn" onClick={() => { setAnswers({}); setRevealed(new Set()); setSaved(false); }}>
                🔄 Làm lại
              </button>
            )}
            {saved && <span style={{ fontSize: 12, color: "#16a34a" }}>✓ Đã lưu</span>}
          </div>
        </div>
      )}

      <style jsx global>{`
        .gd-page { max-width: 100%; margin: 0 auto; padding: 24px 24px; }
        .gd-breadcrumb { font-size: 13px; color: var(--text-tertiary); margin-bottom: 16px; display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
        .gd-breadcrumb a { color: var(--text-tertiary); text-decoration: none; }
        .gd-breadcrumb a:hover { color: var(--action-primary); }
        .gd-breadcrumb span:last-child { color: var(--text-primary); }
        .gd-title { font-size: 24px; font-weight: 900; color: var(--text-primary); margin: 0; }
        .gd-label { font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: .05em; color: var(--text-tertiary); margin-bottom: 12px; }

        .gd-content { background: var(--bg-surface); border: 1px solid var(--border-default); border-radius: 16px; padding: 28px 28px 20px; margin-bottom: 28px; box-shadow: var(--shadow-sm); }
        @media (max-width: 480px) { .gd-content { padding: 20px 16px 16px; } }

        .gd-section { padding-bottom: 20px; margin-bottom: 20px; border-bottom: 1px solid var(--border-default); }
        .gd-section:last-child { border-bottom: none; margin-bottom: 0; padding-bottom: 0; }
        .gd-section-heading { font-size: 15px; font-weight: 700; color: var(--text-primary); margin: 0 0 12px; display: flex; align-items: center; gap: 8px; }
        .gd-accent-bar { width: 4px; height: 20px; background: var(--action-primary); border-radius: 99px; flex-shrink: 0; }
        .gd-section-body { font-size: 13px; color: var(--text-secondary); line-height: 1.7; white-space: pre-line; }

        .gd-formulas { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
        @media (max-width: 640px) { .gd-formulas { grid-template-columns: 1fr; } }
        .gd-formula-card { background: var(--bg-interactive); border: 1px solid var(--border-default); border-radius: 12px; padding: 16px; transition: all 0.2s; }
        .gd-formula-card:hover { border-color: var(--action-primary); }
        .gd-formula-name { font-size: 11px; font-weight: 700; color: var(--action-primary); text-transform: uppercase; letter-spacing: .05em; margin: 0 0 6px; }
        .gd-formula-text { font-size: 14px; font-weight: 800; color: var(--text-primary); margin: 0; line-height: 1.4; }

        .gd-start-btn { width: 100%; border-radius: 12px; background: linear-gradient(135deg, #3b82f6, #6366f1); padding: 14px; color: white; font-weight: 700; font-size: 14px; border: none; cursor: pointer; transition: all 0.3s; }
        .gd-start-btn:hover { box-shadow: 0 4px 16px rgba(59,130,246,0.3); }
        .gd-start-btn:active { transform: scale(0.98); }
        .gd-start-btn:disabled { cursor: not-allowed; }
        .gd-check-btn { padding: 10px 32px; border-radius: 10px; background: #6366f1; color: white; font-weight: 600; font-size: 13px; border: none; cursor: pointer; transition: all 0.2s; }
        .gd-check-btn:hover { background: #4f46e5; box-shadow: 0 4px 12px rgba(99,102,241,0.3); }
        .gd-check-btn:active { transform: scale(0.97); }
        .gd-check-btn:disabled { cursor: not-allowed; }
        .gd-retry-btn { padding: 10px 32px; border-radius: 10px; background: var(--bg-surface); color: var(--text-primary); font-weight: 600; font-size: 13px; border: 1px solid var(--border-default); cursor: pointer; transition: all 0.2s; }
        .gd-retry-btn:hover { border-color: var(--action-primary); color: var(--action-primary); }
        .gd-hide-btn { font-size: 12px; color: var(--text-tertiary); background: none; border: none; cursor: pointer; }
        .gd-hide-btn:hover { color: var(--action-primary); }

        .gd-score-box { text-align: center; padding: 16px; margin-bottom: 16px; background: var(--bg-surface); border: 1px solid var(--border-default); border-radius: 12px; box-shadow: var(--shadow-sm); animation: gdScaleIn 0.3s ease; }
        .gd-score-num { font-size: 40px; font-weight: 900; margin-bottom: 4px; }

        .gd-ex-item { padding-bottom: 24px; margin-bottom: 24px; border-bottom: none; }
        .gd-ex-item:last-child { margin-bottom: 0; padding-bottom: 0; }
        .gd-ex-header { display: flex; align-items: flex-start; gap: 8px; margin-bottom: 12px; }
        .gd-ex-num { flex-shrink: 0; width: 28px; height: 28px; border-radius: 50%; font-size: 12px; font-weight: 700; display: flex; align-items: center; justify-content: center; background: var(--bg-interactive); color: var(--text-secondary); }
        .gd-ex-num.correct { background: #16a34a; color: white; }
        .gd-ex-num.wrong { background: #dc2626; color: white; }
        .gd-ex-question { font-size: 14px; font-weight: 500; color: var(--text-primary); flex: 1; margin: 0; line-height: 1.5; }

        .gd-ex-options { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; margin-left: 36px; }
        @media (max-width: 480px) { .gd-ex-options { grid-template-columns: 1fr; margin-left: 0; } }
        .gd-ex-opt { display: flex; align-items: center; gap: 8px; border-radius: 8px; border: 1px solid var(--border-default); background: var(--bg-surface); padding: 8px 12px; font-size: 13px; text-align: left; color: var(--text-primary); cursor: pointer; transition: all 0.2s; }
        .gd-ex-opt:hover { border-color: var(--action-primary); }
        .gd-ex-opt.selected { border-color: var(--action-primary); background: var(--bg-interactive); color: var(--action-primary); font-weight: 500; }
        .gd-ex-opt.correct { border-color: #22c55e; background: rgba(34,197,94,0.1); color: #15803d; font-weight: 600; }
        .gd-ex-opt.wrong { border-color: #fca5a5; background: rgba(239,68,68,0.05); color: #b91c1c; }
        .gd-ex-opt.dim { color: var(--text-disabled); border-color: transparent; }

        .gd-ex-key { flex-shrink: 0; width: 20px; height: 20px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: 700; border: 1px solid var(--border-default); color: var(--text-tertiary); }
        .gd-ex-key.selected { background: var(--action-primary); color: white; border-color: var(--action-primary); }
        .gd-ex-key.correct { background: #16a34a; color: white; border-color: #16a34a; }
        .gd-ex-key.wrong { background: #dc2626; color: white; border-color: #dc2626; }

        .gd-ex-explain { margin-left: 36px; margin-top: 8px; font-size: 12px; color: #15803d; padding: 6px 0; }
        @media (max-width: 480px) { .gd-ex-explain { margin-left: 0; } }

        .gd-audio-btn { flex-shrink: 0; width: 32px; height: 32px; border-radius: 50%; border: 1px solid var(--border-default); background: var(--bg-surface); cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 14px; transition: all 0.2s; }
        .gd-audio-btn:hover { border-color: var(--action-primary); background: var(--bg-interactive); transform: scale(1.1); }

        @keyframes gdScaleIn { from { transform: scale(0.95); opacity: 0; } to { transform: scale(1); opacity: 1; } }
      `}</style>
    </div>
  );
}
