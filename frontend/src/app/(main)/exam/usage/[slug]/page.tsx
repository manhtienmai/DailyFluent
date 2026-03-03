"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { cn } from "@/lib/utils";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";

/* ── Types ── */
interface Choice { key: string; text: string; }
interface Explanation {
  option: number; is_correct: boolean; reason: string;
  suggested_word?: string; corrected_sentence?: string; corrected_translation?: string;
}
interface ExplanationJson {
  word?: string; reading?: string; han_viet?: string; meaning_vi?: string;
  correct_translation?: string; explanations?: Explanation[];
}
interface Question {
  id: number; text: string; text_vi: string;
  choices: Choice[]; correct_answer: string; explanation_json: ExplanationJson;
}
interface QuizData {
  id: number; title: string; slug: string; level: string;
  question_count: number; book: { id: number; title: string } | null; questions: Question[];
}

type Mode = "all" | "one";
type Phase = "quiz" | "result";

const LEVEL_COLORS: Record<string, string> = {
  N1: "#dc2626", N2: "#7c3aed", N3: "#eab308", N4: "#3b82f6", N5: "#10b981",
};

export default function UsageQuizPage() {
  const params = useParams();
  const slug = params.slug as string;
  const [data, setData] = useState<QuizData | null>(null);
  const [loading, setLoading] = useState(true);
  const [phase, setPhase] = useState<Phase>("quiz");
  const [mode, setMode] = useState<Mode>("one");
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [currentIdx, setCurrentIdx] = useState(0);
  const [revealed, setRevealed] = useState(false);
  const [revealedAll, setRevealedAll] = useState<Set<number>>(new Set());
  const [bookmarked, setBookmarked] = useState<Set<number>>(new Set());
  const [saving, setSaving] = useState(false);
  const [savedResult, setSavedResult] = useState<{ score: number; total: number; rating: string } | null>(null);

  useEffect(() => {
    fetch(`/api/v1/exam/usage/${slug}`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, [slug]);

  const toggleBookmark = (num: number) => {
    setBookmarked((prev) => {
      const next = new Set(prev);
      if (next.has(num)) next.delete(num); else next.add(num);
      return next;
    });
  };

  const saveToDb = async () => {
    if (!data || saving) return;
    setSaving(true);
    try {
      const startRes = await fetch(`/api/v1/exam/attempt/start?template_slug=${data.slug}`, {
        method: "POST", credentials: "include",
      });
      if (!startRes.ok) throw new Error("Failed to start attempt");
      const startData = await startRes.json();
      const attemptId = startData.attempt_id;

      const ansMap: Record<string, string> = {};
      Object.entries(answers).forEach(([qId, key]) => { ansMap[qId] = key; });
      const submitRes = await fetch(`/api/v1/exam/attempt/${attemptId}/submit`, {
        method: "POST", credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answers: ansMap }),
      });
      if (!submitRes.ok) throw new Error("Failed to submit");
      const result = await submitRes.json();
      setSavedResult({ score: result.correct, total: result.total, rating: result.rating });
    } catch (e) {
      console.error("Save failed:", e);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="py-16 text-center text-[var(--text-tertiary)]">Đang tải...</div>;
  if (!data) return <div className="py-16 text-center text-[var(--text-tertiary)]">Không tìm thấy bài quiz.</div>;

  const questions = data.questions;
  const currentQ = questions[currentIdx];
  const totalQ = questions.length;
  const answeredCount = Object.keys(answers).length;
  const lc = LEVEL_COLORS[data.level] || "#6366f1";

  const calcScore = () => {
    let c = 0;
    questions.forEach((q) => { if (answers[q.id] === q.correct_answer) c++; });
    return c;
  };

  const handleSelect = (qId: number, key: string) => {
    if (mode === "one" && revealed) return;
    if (mode === "all" && revealedAll.has(qId)) return;
    setAnswers((p) => ({ ...p, [qId]: key }));
    if (mode === "one") setRevealed(true);
  };

  const handleNext = () => {
    if (currentIdx < totalQ - 1) {
      setCurrentIdx(currentIdx + 1);
      setRevealed(false);
    } else {
      setPhase("result");
      saveToDb();
    }
  };

  const handleRestart = () => {
    setPhase("quiz");
    setAnswers({});
    setCurrentIdx(0);
    setRevealed(false);
    setRevealedAll(new Set());
    setBookmarked(new Set());
    setSavedResult(null);
  };

  const switchMode = (m: Mode) => {
    setMode(m);
    setAnswers({});
    setCurrentIdx(0);
    setRevealed(false);
    setRevealedAll(new Set());
    setBookmarked(new Set());
    setSavedResult(null);
  };

  /* ── Result phase ── */
  if (phase === "result") {
    const score = calcScore();
    const pct = Math.round((score / totalQ) * 100);
    const rating = pct >= 80 ? "GIỎI" : pct >= 60 ? "TRUNG BÌNH" : "CẦN CỐ GẮNG";
    const rc = pct >= 80 ? "#10b981" : pct >= 60 ? "#f59e0b" : "#ef4444";

    return (
      <div className="min-h-screen p-5 max-sm:p-3">
        <div className="mx-auto max-w-[820px] animate-[fadeIn_0.35s_ease]">
          {/* Score */}
          <Card className="mb-5 text-center py-6">
            <CardContent className="px-6">
              <div className="text-[52px] font-extrabold leading-none" style={{ color: rc }}>{score}<span className="text-xl text-[var(--text-tertiary)]">/{totalQ}</span></div>
              <div className="mt-1.5 text-sm font-bold" style={{ color: rc }}>{rating} • {pct}%</div>
              <div className="mt-1 text-xs text-[var(--text-tertiary)]">{data.title}</div>
              {savedResult && <div className="mt-1.5 text-[11px] text-emerald-500">✓ Đã lưu kết quả</div>}
              {saving && <div className="mt-1.5 text-[11px] text-[var(--text-tertiary)]">⏳ Đang lưu...</div>}
              <div className="mt-4 flex justify-center gap-2.5">
                <Button variant="outline" onClick={handleRestart} className="rounded-full">↺ Làm lại</Button>
                <Button asChild className="rounded-full bg-gradient-to-br from-indigo-500 to-violet-500 text-white">
                  <Link href="/exam/usage">← Danh sách</Link>
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Review all */}
          <div className="flex flex-col gap-3">
            {questions.map((q, i) => {
              const ua = answers[q.id];
              const ok = ua === q.correct_answer;
              const ej = q.explanation_json;
              return (
                <Card key={q.id} className={cn(
                  "border-[1.5px] border-l-[4px] py-0",
                  ok ? "border-l-emerald-500 border-emerald-500/20" : "border-l-red-500 border-red-500/20"
                )}>
                  <CardContent className="p-4">
                    <QuestionHeader num={i + 1} q={q} ej={ej} lc={lc} statusColor={ok ? "#10b981" : "#ef4444"} isBookmarked={bookmarked.has(i + 1)} onToggleBookmark={() => toggleBookmark(i + 1)} showDetails={true} />
                    <ChoicesList q={q} userAns={ua} showResult />
                    <ExplanationBlock ej={ej} isCorrect={ok} />
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      </div>
    );
  }

  /* ── Quiz phase ── */
  return (
    <div className="min-h-screen p-5 max-sm:p-3">
      <div className={cn("mx-auto animate-[fadeIn_0.35s_ease]", mode === "one" ? "max-w-[680px]" : "max-w-[820px]")}>
        {/* Header bar */}
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="icon" asChild className="h-9 w-9 rounded-full text-[var(--text-tertiary)]">
              <Link href="/exam/usage">←</Link>
            </Button>
            <div>
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="text-[0.65rem] font-bold rounded-lg" style={{ color: lc, background: `${lc}12`, borderColor: `${lc}30` }}>{data.level}</Badge>
                <span className="text-sm font-bold text-[var(--text-primary)]">{data.title}</span>
              </div>
              <div className="text-xs text-[var(--text-tertiary)]">
                {mode === "one" ? `${currentIdx + 1}/${totalQ}` : `${answeredCount}/${totalQ} đã trả lời`}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {/* Mode toggle */}
            <div className="flex rounded-full border border-[var(--border-default)] p-0.5">
              <Button variant={mode === "one" ? "default" : "ghost"} size="xs"
                className={cn("rounded-full text-[0.7rem] font-semibold", mode === "one" && "bg-gradient-to-br from-indigo-500 to-violet-500 text-white")}
                onClick={() => switchMode("one")}
              >Từng câu</Button>
              <Button variant={mode === "all" ? "default" : "ghost"} size="xs"
                className={cn("rounded-full text-[0.7rem] font-semibold", mode === "all" && "bg-gradient-to-br from-indigo-500 to-violet-500 text-white")}
                onClick={() => switchMode("all")}
              >Tất cả</Button>
            </div>
            {mode === "all" && (
              <Button onClick={() => { setPhase("result"); saveToDb(); }} disabled={answeredCount === 0}
                className="rounded-full bg-gradient-to-br from-indigo-500 to-violet-500 text-white text-xs font-semibold"
              >
                Nộp bài
              </Button>
            )}
          </div>
        </div>

        {/* Progress bar */}
        <Progress value={((mode === "one" ? currentIdx + 1 : answeredCount) / totalQ) * 100}
          className="mb-4 h-1.5 bg-[var(--border-subtle)]"
        />

        {/* ── Mode: One-by-one ── */}
        {mode === "one" && currentQ && (() => {
          const ej = currentQ.explanation_json;
          const userAns = answers[currentQ.id];
          const isCorrect = userAns === currentQ.correct_answer;

          return (
            <>
              <Card className="mb-3 animate-[slideUp_0.4s_ease] border-[1.5px] border-[var(--border-default)] bg-[var(--bg-surface)] py-0">
                <CardContent className="p-5 max-sm:p-3.5">
                  <QuestionHeader num={currentIdx + 1} q={currentQ} ej={ej} lc={lc} isBookmarked={bookmarked.has(currentIdx + 1)} onToggleBookmark={() => toggleBookmark(currentIdx + 1)} showDetails={revealed} />
                  {/* Choices */}
                  <div className="flex flex-col gap-2 mt-3">
                    {currentQ.choices.map((c) => {
                      const isThis = userAns === c.key;
                      const isCorrectChoice = c.key === currentQ.correct_answer;
                      return (
                        <button key={c.key}
                          className={cn(
                            "group flex w-full items-center gap-3 rounded-[14px] border-[1.5px] border-l-[3px] border-l-transparent px-4 py-3 text-left transition-all",
                            "border-[var(--border-default)] bg-[var(--bg-surface)] cursor-pointer",
                            !revealed && !isThis && "hover:border-indigo-300 hover:border-l-indigo-500 hover:bg-indigo-500/[0.03] hover:translate-x-1",
                            !revealed && isThis && "border-indigo-400 border-l-indigo-500 bg-indigo-500/[0.04]",
                            revealed && isCorrectChoice && "!border-emerald-400 !border-l-emerald-500 !bg-emerald-500/[0.05] animate-[pulseOk_0.6s_ease]",
                            revealed && isThis && !isCorrectChoice && "!border-red-300 !border-l-red-500 !bg-red-500/[0.04] animate-[shake_0.4s_ease]",
                            revealed && "cursor-default"
                          )}
                          onClick={() => handleSelect(currentQ.id, c.key)}
                          disabled={revealed}
                        >
                          <span className={cn(
                            "flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-xs font-bold transition-all",
                            "bg-[var(--bg-app-subtle)] text-[var(--text-tertiary)]",
                            !revealed && !isThis && "group-hover:bg-indigo-500 group-hover:text-white",
                            !revealed && isThis && "bg-indigo-500 text-white",
                            revealed && isCorrectChoice && "!bg-emerald-500 !text-white",
                            revealed && isThis && !isCorrectChoice && "!bg-red-500 !text-white"
                          )}>{c.key}</span>
                          <span className="flex-1 text-[0.95rem] text-[var(--text-primary)]" style={{ fontFamily: "var(--font-jp)" }}>{c.text}</span>
                          {revealed && isCorrectChoice && <span className="text-emerald-500 font-bold">✓</span>}
                          {revealed && isThis && !isCorrectChoice && <span className="text-red-500 font-bold">✗</span>}
                        </button>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>

              {/* Explanation */}
              {revealed && <ExplanationPanel ej={ej} isCorrect={isCorrect} />}

              {/* Next */}
              {revealed && (
                <Button onClick={handleNext}
                  className="w-full rounded-full bg-gradient-to-br from-indigo-500 to-violet-500 text-white font-semibold shadow-[0_3px_12px_rgba(99,102,241,0.3)] hover:shadow-[0_6px_20px_rgba(99,102,241,0.4)] animate-[revealIn_0.3s_ease]"
                >
                  {currentIdx < totalQ - 1 ? "Câu tiếp theo →" : "📊 Xem kết quả"}
                </Button>
              )}
            </>
          );
        })()}

        {/* ── Mode: All-at-once ── */}
        {mode === "all" && (
          <div className="flex flex-col gap-3">
            {questions.map((q, i) => {
              return (
                <Card key={q.id} className="animate-[fadeIn_0.3s_ease] border-[1.5px] border-[var(--border-default)] bg-[var(--bg-surface)] py-0">
                  <CardContent className="p-4">
                    <QuestionHeader num={i + 1} q={q} ej={q.explanation_json} lc={lc} isBookmarked={bookmarked.has(i + 1)} onToggleBookmark={() => toggleBookmark(i + 1)} showDetails={false} />
                    <div className="flex flex-col gap-2 mt-3">
                      {q.choices.map((c) => {
                        const isThis = answers[q.id] === c.key;
                        return (
                          <button key={c.key}
                            className={cn(
                              "group flex w-full items-center gap-3 rounded-[14px] border-[1.5px] border-l-[3px] border-l-transparent px-4 py-3 text-left transition-all",
                              "border-[var(--border-default)] bg-[var(--bg-surface)] cursor-pointer",
                              !isThis && "hover:border-indigo-300 hover:border-l-indigo-500 hover:bg-indigo-500/[0.03] hover:translate-x-1",
                              isThis && "border-indigo-400 border-l-indigo-500 bg-indigo-500/[0.04]"
                            )}
                            onClick={() => handleSelect(q.id, c.key)}
                          >
                            <span className={cn(
                              "flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-xs font-bold transition-all",
                              "bg-[var(--bg-app-subtle)] text-[var(--text-tertiary)]",
                              !isThis && "group-hover:bg-indigo-500 group-hover:text-white",
                              isThis && "bg-indigo-500 text-white"
                            )}>{c.key}</span>
                            <span className="flex-1 text-[0.95rem] text-[var(--text-primary)]" style={{ fontFamily: "var(--font-jp)" }}>{c.text}</span>
                          </button>
                        );
                      })}
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

/* ── Sub-components ── */
function QuestionHeader({ num, q, ej, lc, statusColor, isBookmarked, onToggleBookmark, showDetails = true }: { num: number; q: Question; ej: ExplanationJson; lc: string; statusColor?: string; isBookmarked?: boolean; onToggleBookmark?: () => void; showDetails?: boolean }) {
  return (
    <div className="flex items-center gap-3">
      <span
        className={cn(
          "flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-sm font-bold transition-all",
          onToggleBookmark && "cursor-pointer hover:bg-amber-400 hover:text-white hover:scale-110",
          isBookmarked && "bg-amber-500 text-white shadow-[0_0_0_2px_rgba(245,158,11,0.25)]"
        )}
        style={statusColor ? { background: statusColor, color: "#fff" } : isBookmarked ? {} : { background: "var(--bg-app-subtle)", color: "var(--text-tertiary)" }}
        onClick={(e) => { e.stopPropagation(); onToggleBookmark?.(); }}
        title={isBookmarked ? "Bỏ đánh dấu" : "Đánh dấu câu này"}
      >{num}</span>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-lg font-medium text-[var(--text-primary)]" style={{ fontFamily: "var(--font-jp)" }}>{q.text}</span>
          {showDetails && ej.reading && <span className="text-sm text-[var(--text-secondary)]" style={{ fontFamily: "var(--font-jp)" }}>{ej.reading}</span>}
          {showDetails && ej.han_viet && <span className="text-[0.85rem] font-semibold" style={{ color: lc }}>【{ej.han_viet}】</span>}
        </div>
        {showDetails && ej.meaning_vi && <div className="text-sm text-[var(--text-secondary)] mt-0.5">► {ej.meaning_vi}</div>}
      </div>
    </div>
  );
}

function ChoicesList({ q, userAns, showResult }: { q: Question; userAns?: string; showResult?: boolean }) {
  return (
    <div className="mt-3 flex flex-col gap-1.5">
      {q.choices.map((c) => {
        const isThis = userAns === c.key;
        const isCorrectChoice = c.key === q.correct_answer;
        return (
          <div key={c.key}
            className={cn(
              "flex items-center gap-3 rounded-xl border-[1.5px] border-l-[3px] border-l-transparent px-3.5 py-2.5",
              "border-[var(--border-default)] bg-[var(--bg-surface)]",
              showResult && isCorrectChoice && "!border-emerald-400 !border-l-emerald-500 !bg-emerald-500/[0.05]",
              showResult && isThis && !isCorrectChoice && "!border-red-300 !border-l-red-500 !bg-red-500/[0.04]"
            )}
          >
            <span className={cn(
              "flex h-6 w-6 shrink-0 items-center justify-center rounded-md text-[0.7rem] font-bold",
              "bg-[var(--bg-app-subtle)] text-[var(--text-tertiary)]",
              showResult && isCorrectChoice && "!bg-emerald-500 !text-white",
              showResult && isThis && !isCorrectChoice && "!bg-red-500 !text-white"
            )}>{c.key}</span>
            <span className="flex-1 text-sm text-[var(--text-primary)]" style={{ fontFamily: "var(--font-jp)" }}>{c.text}</span>
            {showResult && isCorrectChoice && <span className="text-emerald-500 font-bold text-sm">✓</span>}
            {showResult && isThis && !isCorrectChoice && <span className="text-red-500 font-bold text-sm">✗</span>}
          </div>
        );
      })}
    </div>
  );
}

function ExplanationBlock({ ej, isCorrect }: { ej: ExplanationJson; isCorrect: boolean }) {
  if (!ej.explanations || ej.explanations.length === 0) return null;
  return (
    <div className="mt-3 rounded-xl bg-[var(--bg-app-subtle)] p-3.5 border border-[var(--border-subtle,transparent)] animate-[revealIn_0.3s_ease]">
      {ej.correct_translation && <div className="text-sm font-medium text-emerald-500 mb-2 rounded-lg bg-emerald-500/[0.05] px-3 py-2">✓ {ej.correct_translation}</div>}
      {ej.explanations.map((ex) => (
        <div key={ex.option} className="mb-2 text-sm leading-[1.7] text-[var(--text-secondary)] last:mb-0">
          <strong className={ex.is_correct ? "text-emerald-500" : "text-red-500"}>Câu {ex.option}:</strong> {ex.reason}
          {ex.suggested_word && (
            <div className="text-indigo-500 text-[0.88rem] mt-1 pl-3.5">
              → Nên dùng: <strong className="font-semibold">{ex.suggested_word}</strong>
              {ex.corrected_sentence && (
                <div className="mt-1 text-sm text-[var(--text-tertiary)]">
                  {ex.corrected_sentence}
                  {ex.corrected_translation && <span> — {ex.corrected_translation}</span>}
                </div>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function ExplanationPanel({ ej, isCorrect }: { ej: ExplanationJson; isCorrect: boolean }) {
  return (
    <Card className={cn(
      "mb-3 animate-[revealIn_0.4s_ease] border-[1.5px] border-l-[4px] py-0",
      isCorrect ? "border-l-emerald-500 border-emerald-500/20" : "border-l-red-500 border-red-500/20"
    )}>
      <CardContent className="p-4">
        <div className={cn("mb-3 text-lg font-bold", isCorrect ? "text-emerald-500" : "text-red-500")}>
          {isCorrect ? "🎉 Chính xác!" : "❌ Sai rồi!"}
        </div>
        <ExplanationBlock ej={ej} isCorrect={isCorrect} />
      </CardContent>
    </Card>
  );
}
