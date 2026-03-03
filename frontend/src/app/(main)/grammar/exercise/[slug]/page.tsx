"use client";

import { useState, useCallback, useMemo } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect } from "react";

/* ── Types ── */
interface Choice {
  key: string;
  text: string;
}

interface GrammarQuestion {
  id: number;
  type: "MCQ" | "SENTENCE_ORDER";
  order: number;
  question_text: string;
  explanation_jp: string;
  explanation_vi: string;
  // MCQ
  choices?: Choice[];
  correct_answer?: string;
  // SENTENCE_ORDER
  sentence_prefix?: string;
  sentence_suffix?: string;
  tokens?: string[];
  correct_order?: number[];
  star_position?: number;
}

interface ExerciseData {
  id: number;
  title: string;
  level: string;
  grammar_point_slug: string | null;
  questions: GrammarQuestion[];
}

interface AnswerRecord {
  question_id: number;
  question_text: string;
  user_answer: unknown;
  is_correct: boolean;
}

export default function GrammarExercisePage() {
  const params = useParams();
  const slug = params.slug as string;

  const [data, setData] = useState<ExerciseData | null>(null);
  const [loading, setLoading] = useState(true);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answered, setAnswered] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [answerHistory, setAnswerHistory] = useState<AnswerRecord[]>([]);

  // MCQ state
  const [selectedChoice, setSelectedChoice] = useState<string | null>(null);
  const [lastAnswer, setLastAnswer] = useState<{ correct: boolean; correctKey: string; starAnswer?: string; expJp?: string; expVi?: string } | null>(null);

  // Sentence Order state
  const [boxContents, setBoxContents] = useState<(number | null)[]>([null, null, null, null]);
  const [selectedChip, setSelectedChip] = useState<number | null>(null);

  const totalQuestions = data?.questions?.length || 0;
  const score = answerHistory.filter((a) => a.is_correct).length;
  const current = data?.questions?.[currentIndex] || null;
  const progressPct = totalQuestions > 0 ? ((currentIndex) / totalQuestions) * 100 : 0;
  const allBoxesFilled = useMemo(() => boxContents.every((b) => b !== null), [boxContents]);

  /* ── Fetch ── */
  useEffect(() => {
    fetch(`/api/v1/grammar/exercise/${slug}`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d: ExerciseData) => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, [slug]);

  /* ── Reset question state ── */
  const resetQuestion = useCallback(() => {
    setSelectedChoice(null);
    setLastAnswer(null);
    setAnswered(false);
    setBoxContents([null, null, null, null]);
    setSelectedChip(null);
  }, []);

  /* ── MCQ: check answer ── */
  const checkMCQ = useCallback(async () => {
    if (!current || !selectedChoice) return;
    try {
      const res = await fetch("/grammar/api/check-answer/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ question_id: current.id, user_answer: selectedChoice }),
      });
      const d = await res.json();
      setLastAnswer({
        correct: d.is_correct,
        correctKey: d.correct_answer,
        starAnswer: d.star_answer,
        expJp: d.explanation_jp,
        expVi: d.explanation_vi,
      });
      setAnswered(true);
      setAnswerHistory((prev) => [
        ...prev,
        { question_id: current.id, question_text: current.question_text, user_answer: selectedChoice, is_correct: d.is_correct },
      ]);
    } catch (e) {
      console.error("check-answer failed:", e);
    }
  }, [current, selectedChoice]);

  /* ── Sentence Order: check answer ── */
  const checkOrder = useCallback(async () => {
    if (!current || !allBoxesFilled) return;
    try {
      const res = await fetch("/grammar/api/check-answer/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ question_id: current.id, user_answer: boxContents }),
      });
      const d = await res.json();
      setLastAnswer({
        correct: d.is_correct,
        correctKey: "",
        starAnswer: d.star_answer,
        expJp: d.explanation_jp,
        expVi: d.explanation_vi,
      });
      setAnswered(true);
      setAnswerHistory((prev) => [
        ...prev,
        { question_id: current.id, question_text: current.question_text, user_answer: boxContents, is_correct: d.is_correct },
      ]);
    } catch (e) {
      console.error("check-answer failed:", e);
    }
  }, [current, boxContents, allBoxesFilled]);

  /* ── Next question ── */
  const nextQuestion = useCallback(() => {
    if (currentIndex < totalQuestions - 1) {
      setCurrentIndex((i) => i + 1);
      resetQuestion();
    } else {
      // Submit exercise
      if (data) {
        fetch("/grammar/api/submit-exercise/", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({ exercise_set_id: data.id, answers: answerHistory }),
        }).catch(() => {});
      }
      setShowResults(true);
    }
  }, [currentIndex, totalQuestions, resetQuestion, data, answerHistory]);

  /* ── Restart ── */
  const restart = useCallback(() => {
    setCurrentIndex(0);
    setShowResults(false);
    setAnswerHistory([]);
    resetQuestion();
  }, [resetQuestion]);

  /* ── Sentence Order helpers ── */
  const isChipUsed = (idx: number) => boxContents.includes(idx);

  const selectChip = (idx: number) => {
    if (isChipUsed(idx) || answered) return;
    setSelectedChip(idx);
  };

  const placeInBox = (boxIdx: number) => {
    if (answered) return;
    if (boxContents[boxIdx] !== null) {
      // Remove from box
      const newBoxes = [...boxContents];
      newBoxes[boxIdx] = null;
      setBoxContents(newBoxes);
      return;
    }
    if (selectedChip !== null && !isChipUsed(selectedChip)) {
      const newBoxes = [...boxContents];
      newBoxes[boxIdx] = selectedChip;
      setBoxContents(newBoxes);
      setSelectedChip(null);
    }
  };

  const removeFromBox = (boxIdx: number) => {
    if (answered) return;
    const newBoxes = [...boxContents];
    newBoxes[boxIdx] = null;
    setBoxContents(newBoxes);
  };

  /* ── Choice CSS ── */
  const choiceClass = (key: string) => {
    if (!answered) return selectedChoice === key ? "choice-selected" : "";
    if (key === lastAnswer?.correctKey) return "choice-correct";
    if (key === selectedChoice && !lastAnswer?.correct) return "choice-incorrect";
    return "choice-dimmed";
  };

  /* ── Render ── */
  if (loading) {
    return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Đang tải...</div>;
  }
  if (!data) {
    return (
      <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>
        <p>Không tìm thấy bài tập.</p>
        <p className="text-sm mt-2">API endpoint <code>/api/v1/grammar/exercise/{slug}</code> chưa sẵn sàng.</p>
      </div>
    );
  }

  return (
    <div className="grammar-page-wrapper" style={{ padding: "24px" }}>
      <div className="max-w-2xl mx-auto">

        {/* Header */}
        <div className="flex items-center gap-3 mb-4">
          <Link
            href={data.grammar_point_slug ? `/grammar/${data.grammar_point_slug}` : "/grammar"}
            className="p-2 rounded-lg transition-colors"
            style={{ color: "var(--text-secondary)" }}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M15 18l-6-6 6-6" /></svg>
          </Link>
          <div className="flex-1">
            <h1 className="font-bold text-lg" style={{ color: "var(--text-primary)" }}>{data.title}</h1>
            <p className="text-xs" style={{ color: "var(--text-secondary)" }}>{totalQuestions} câu hỏi</p>
          </div>
        </div>

        {/* Progress */}
        {!showResults && (
          <div className="mb-6">
            <div className="flex justify-between text-xs mb-1.5" style={{ color: "var(--text-secondary)" }}>
              <span>Câu {currentIndex + 1} / {totalQuestions}</span>
              <span>{score} đúng</span>
            </div>
            <div className="h-2 rounded-full overflow-hidden" style={{ background: "var(--border-default)" }}>
              <div className="h-full rounded-full transition-all" style={{ width: `${progressPct}%`, background: "linear-gradient(90deg, #6366f1, #8b5cf6)" }} />
            </div>
          </div>
        )}

        {/* Results Screen */}
        {showResults && (
          <div className="exercise-card text-center p-8 rounded-2xl" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
            <div className="text-5xl font-bold mb-2" style={{ color: "var(--text-primary)" }}>{score}/{totalQuestions}</div>
            <div className="text-lg mb-1" style={{ color: "var(--text-secondary)" }}>{Math.round(score / totalQuestions * 100)}%</div>
            <h2 className="text-2xl font-bold mb-2" style={{ color: "var(--text-primary)" }}>Kết quả</h2>
            <p className="text-sm mb-6" style={{ color: "var(--text-secondary)" }}>
              {score === totalQuestions ? "🎉 Xuất sắc!" : score >= totalQuestions * 0.7 ? "👏 Tốt lắm!" : "💪 Hãy ôn lại!"}
            </p>

            {/* Answer breakdown */}
            <div className="space-y-2 mb-6 text-left">
              {answerHistory.map((ans, i) => (
                <div key={i} className="flex items-start gap-3 p-3 rounded-xl" style={{
                  background: ans.is_correct ? "rgba(209,250,229,.5)" : "rgba(254,226,226,.5)",
                  border: `1px solid ${ans.is_correct ? "rgba(52,211,153,.3)" : "rgba(252,165,165,.3)"}`,
                }}>
                  <span className="text-lg flex-shrink-0">{ans.is_correct ? "✓" : "✗"}</span>
                  <p className="text-sm flex-1" style={{ fontFamily: "'Noto Sans JP', sans-serif" }}>{ans.question_text || `Câu ${i + 1}`}</p>
                </div>
              ))}
            </div>

            <div className="flex items-center justify-center gap-3 flex-wrap">
              <button onClick={restart} className="px-5 py-2.5 rounded-xl text-sm font-semibold" style={{ background: "var(--bg-interactive)", color: "var(--text-primary)", border: "1px solid var(--border-default)" }}>
                Làm lại
              </button>
              <Link href="/grammar" className="px-5 py-2.5 rounded-xl text-sm font-semibold text-white" style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6)", textDecoration: "none" }}>
                Về trang chủ
              </Link>
            </div>
          </div>
        )}

        {/* Question Card */}
        {!showResults && current && (
          <div className="p-6 rounded-2xl" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
            <div className="flex items-center justify-between mb-5">
              <span className="text-xs font-bold uppercase tracking-widest px-2.5 py-1 rounded-lg" style={{
                background: current.type === "MCQ" ? "var(--bg-interactive)" : "#fef3c7",
                color: current.type === "MCQ" ? "var(--action-primary)" : "#b45309",
              }}>
                問 {currentIndex + 1} {current.type === "MCQ" ? "MCQ" : "並べ替え ★"}
              </span>
            </div>

            {/* MCQ */}
            {current.type === "MCQ" && (
              <>
                <p className="text-lg font-medium mb-6 leading-loose" style={{ fontFamily: "'Noto Sans JP', sans-serif", color: "var(--text-primary)" }}>
                  {current.question_text}
                </p>
                <div className="space-y-3 mb-5">
                  {current.choices?.map((c) => (
                    <button
                      key={c.key}
                      disabled={answered}
                      onClick={() => setSelectedChoice(c.key)}
                      className={`w-full text-left p-3 rounded-xl border transition-all flex items-center gap-3 ${choiceClass(c.key)}`}
                      style={{
                        background: choiceClass(c.key) === "choice-correct" ? "rgba(209,250,229,.7)"
                          : choiceClass(c.key) === "choice-incorrect" ? "rgba(254,226,226,.7)"
                          : choiceClass(c.key) === "choice-selected" ? "var(--bg-interactive)"
                          : "var(--bg-surface)",
                        borderColor: choiceClass(c.key) === "choice-correct" ? "#34d399"
                          : choiceClass(c.key) === "choice-incorrect" ? "#f87171"
                          : choiceClass(c.key) === "choice-selected" ? "var(--action-primary)"
                          : "var(--border-default)",
                        opacity: choiceClass(c.key) === "choice-dimmed" ? 0.5 : 1,
                      }}
                    >
                      <span className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0" style={{ background: "var(--bg-interactive)", color: "var(--text-secondary)" }}>
                        {c.key}
                      </span>
                      <span style={{ fontFamily: "'Noto Sans JP', sans-serif" }}>{c.text}</span>
                    </button>
                  ))}
                </div>
                {!answered && (
                  <div className="flex justify-end">
                    <button
                      onClick={checkMCQ}
                      disabled={!selectedChoice}
                      className="px-6 py-2.5 rounded-xl text-sm font-semibold text-white transition-all"
                      style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6)", opacity: selectedChoice ? 1 : 0.4, cursor: selectedChoice ? "pointer" : "not-allowed" }}
                    >
                      Xác nhận
                    </button>
                  </div>
                )}
              </>
            )}

            {/* Sentence Order */}
            {current.type === "SENTENCE_ORDER" && (
              <>
                <p className="text-xs mb-4" style={{ color: "var(--text-secondary)" }}>
                  Nhấn chọn token, sau đó nhấn vào ô trống để điền vào câu.
                </p>

                {/* Sentence display */}
                <div className="flex items-center flex-wrap gap-1 mb-6 text-base" style={{ fontFamily: "'Noto Sans JP', sans-serif", color: "var(--text-primary)" }}>
                  <span>{current.sentence_prefix}</span>
                  {boxContents.map((tokenIdx, boxIdx) => (
                    <span
                      key={boxIdx}
                      onClick={() => placeInBox(boxIdx)}
                      className="inline-flex items-center justify-center min-w-[3rem] h-10 border-b-2 px-2 cursor-pointer relative transition-all"
                      style={{
                        borderColor: tokenIdx !== null ? "var(--action-primary)" : "var(--border-strong)",
                        background: tokenIdx !== null ? "var(--bg-interactive)" : "transparent",
                        borderRadius: "6px",
                      }}
                    >
                      {tokenIdx === null ? (
                        <span style={{ color: "var(--text-disabled)", fontSize: "0.8rem" }}>{boxIdx + 1}</span>
                      ) : (
                        <>
                          <span>{current.tokens?.[tokenIdx]}</span>
                          {!answered && (
                            <button
                              onClick={(e) => { e.stopPropagation(); removeFromBox(boxIdx); }}
                              className="absolute -top-1.5 -right-1.5 w-4 h-4 rounded-full text-white text-xs flex items-center justify-center"
                              style={{ background: "#ef4444", fontSize: "10px", lineHeight: 1 }}
                            >×</button>
                          )}
                        </>
                      )}
                    </span>
                  ))}
                  <span>{current.sentence_suffix}</span>
                </div>

                {/* Token chips */}
                <div className="text-xs font-semibold mb-3" style={{ color: "var(--text-secondary)" }}>選択肢</div>
                <div className="flex flex-wrap gap-2 mb-6">
                  {current.tokens?.map((token, chipIdx) => (
                    <button
                      key={chipIdx}
                      disabled={answered}
                      onClick={() => selectChip(chipIdx)}
                      className="px-3 py-1.5 rounded-lg text-sm font-medium transition-all"
                      style={{
                        fontFamily: "'Noto Sans JP', sans-serif",
                        background: isChipUsed(chipIdx) ? "var(--border-default)" : selectedChip === chipIdx ? "var(--action-primary)" : "var(--bg-interactive)",
                        color: isChipUsed(chipIdx) ? "var(--text-disabled)" : selectedChip === chipIdx ? "var(--action-primary-text)" : "var(--text-primary)",
                        border: `1px solid ${selectedChip === chipIdx ? "var(--action-primary)" : "var(--border-default)"}`,
                        opacity: isChipUsed(chipIdx) ? 0.4 : 1,
                        cursor: isChipUsed(chipIdx) || answered ? "not-allowed" : "pointer",
                        textDecoration: isChipUsed(chipIdx) ? "line-through" : "none",
                      }}
                    >
                      {token}
                    </button>
                  ))}
                </div>

                {/* Check button */}
                {!answered && (
                  <div className="flex justify-end">
                    <button
                      onClick={checkOrder}
                      disabled={!allBoxesFilled}
                      className="px-6 py-2.5 rounded-xl text-sm font-semibold text-white"
                      style={{ background: "linear-gradient(135deg, #f59e0b, #d97706)", opacity: allBoxesFilled ? 1 : 0.4, cursor: allBoxesFilled ? "pointer" : "not-allowed" }}
                    >
                      答えを確認する
                    </button>
                  </div>
                )}
              </>
            )}

            {/* Post-answer explanation */}
            {answered && lastAnswer && (
              <div className="mt-5">
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-xl">{lastAnswer.correct ? "✅" : "❌"}</span>
                  <span className="font-bold text-base" style={{ color: lastAnswer.correct ? "#16a34a" : "#dc2626" }}>
                    {lastAnswer.correct ? "正解！" : "不正解"}
                  </span>
                </div>

                {/* Star answer hint */}
                {current?.type === "SENTENCE_ORDER" && !lastAnswer.correct && lastAnswer.starAnswer && (
                  <div className="p-3 rounded-xl mb-3" style={{ background: "var(--status-warning-subtle)", border: "1px solid var(--status-warning)" }}>
                    <span className="font-semibold" style={{ color: "var(--status-warning-text)" }}>★ の正解: </span>
                    <span className="font-semibold" style={{ fontFamily: "'Noto Sans JP', sans-serif", color: "#0f766e" }}>{lastAnswer.starAnswer}</span>
                  </div>
                )}

                {/* Explanation */}
                {(lastAnswer.expJp || lastAnswer.expVi) && (
                  <div className="p-3 rounded-xl" style={{ background: "var(--bg-interactive)", border: "1px solid var(--border-default)" }}>
                    {lastAnswer.expJp && <div className="text-sm mb-1" style={{ fontFamily: "'Noto Sans JP', sans-serif", color: "var(--text-primary)" }}>{lastAnswer.expJp}</div>}
                    {lastAnswer.expVi && <div className="text-sm" style={{ color: "var(--text-secondary)" }}>{lastAnswer.expVi}</div>}
                  </div>
                )}

                {/* Next button */}
                <div className="flex justify-end mt-4">
                  <button
                    onClick={nextQuestion}
                    className="flex items-center gap-2 px-6 py-2.5 rounded-xl text-sm font-semibold text-white"
                    style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6)" }}
                  >
                    {currentIndex < totalQuestions - 1 ? "次の問題 →" : "結果を見る"}
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
