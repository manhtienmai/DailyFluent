"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import QuizGrid, { GridQuestion } from "@/components/quiz/QuizGrid";
import { getQuizProgress, resetQuizProgress } from "@/lib/quiz-progress";

const LEVELS = ["", "N1", "N2", "N3", "N4", "N5"];

interface QuestionStub {
  num: number; id: number; correct_answer: string;
}

export default function BunpouGridPage() {
  const [questions, setQuestions] = useState<QuestionStub[]>([]);
  const [loading, setLoading] = useState(true);
  const [level, setLevel] = useState("");
  const [progress, setProgress] = useState(getQuizProgress("bunpou", ""));


  const fetchAll = useCallback(() => {
    setLoading(true);
    const url = level
      ? `/api/v1/exam/bunpou/all-questions?level=${level}`
      : `/api/v1/exam/bunpou/all-questions`;
    fetch(url, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : { questions: [] }))
      .then((d) => {
        setQuestions(
          (d.questions || []).map((q: any) => ({
            num: q.num, id: q.id, correct_answer: q.correct_answer,
          }))
        );
        setLoading(false);
        setProgress(getQuizProgress("bunpou", level));
      })
      .catch(() => setLoading(false));
  }, [level]);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  useEffect(() => {
    const onFocus = () => {
      setProgress(getQuizProgress("bunpou", level));
    };
    window.addEventListener("focus", onFocus);
    return () => window.removeEventListener("focus", onFocus);
  }, [level]);

  useEffect(() => {
    const onVisible = () => {
      if (document.visibilityState === "visible") {
        setProgress(getQuizProgress("bunpou", level));
      }
    };
    document.addEventListener("visibilitychange", onVisible);
    return () => document.removeEventListener("visibilitychange", onVisible);
  }, [level]);

  const answeredSet = new Set(Object.keys(progress.answers));
  const revealedSet = new Set(progress.revealed);
  const bookmarkedSet = new Set(progress.bookmarked);

  const gridQuestions: GridQuestion[] = questions.map((q) => {
    const ans = progress.answers[String(q.id)];
    let status: GridQuestion["status"] = "unanswered";
    if (ans) {
      if (revealedSet.has(q.num)) {
        status = ans === q.correct_answer ? "correct" : "wrong";
      } else {
        status = "answered";
      }
    }
    return { num: q.num, id: q.id, status, bookmarked: bookmarkedSet.has(q.num) };
  });

  const answeredCount = gridQuestions.filter((q) => q.status !== "unanswered").length;
  const correctCount = gridQuestions.filter((q) => q.status === "correct").length;
  const wrongCount = gridQuestions.filter((q) => q.status === "wrong").length;

  const handleReset = () => {
    resetQuizProgress("bunpou", level);
    setProgress(getQuizProgress("bunpou", level));
  };

  return (
    <div className="min-h-screen p-6 max-sm:p-4">
      <div className="mx-auto max-w-4xl animate-[fadeIn_0.4s_ease]">
        <nav className="mb-5 flex items-center gap-1.5 text-xs text-[var(--text-tertiary)]">
          <Link href="/exam" className="text-[var(--text-tertiary)] no-underline hover:text-indigo-500 transition-colors">Luyện thi</Link>
          <span>/</span>
          <span className="font-semibold text-[var(--text-primary)]">文法 Ngữ pháp</span>
        </nav>

        <h1 className="mb-1 text-2xl font-extrabold tracking-tight text-[var(--text-primary)] max-sm:text-xl">📝 文法 — Ngữ pháp</h1>
        <p className="mb-5 text-sm leading-relaxed text-[var(--text-tertiary)] max-sm:text-xs max-sm:mb-4">Chọn câu để làm bài. Bấm vào ô số để chuyển câu.</p>

        {/* Level filter */}
        <div className="mb-4 flex flex-wrap gap-1.5 max-sm:gap-1 max-sm:mb-3">
          {LEVELS.map((l) => (
            <Button key={l} size="sm"
              variant={level === l ? "default" : "outline"}
              className={cn(
                "rounded-full text-xs font-semibold",
                level === l && "bg-gradient-to-br from-indigo-500 to-violet-500 text-white border-transparent shadow-[0_2px_10px_rgba(99,102,241,0.3)]",
                "max-sm:text-[0.7rem] max-sm:px-3 max-sm:h-7"
              )}
              onClick={() => setLevel(l)}
            >
              {l || "Tất cả"}
            </Button>
          ))}
        </div>

        {/* Stats */}
        {answeredCount > 0 && (
          <div className="mb-5 flex flex-wrap items-center gap-2 max-sm:gap-1.5 max-sm:mb-4">
            <Badge variant="outline" className="text-xs font-bold px-3.5 py-1 rounded-[10px] max-sm:text-[0.65rem] max-sm:px-2.5 max-sm:py-0.5">
              {answeredCount}/{questions.length} đã làm
            </Badge>
            {correctCount > 0 && (
              <Badge variant="outline" className="text-xs font-bold px-3.5 py-1 rounded-[10px] text-emerald-500 border-emerald-500/25 bg-emerald-500/[0.05] max-sm:text-[0.65rem] max-sm:px-2.5 max-sm:py-0.5">
                {correctCount} đúng
              </Badge>
            )}
            {wrongCount > 0 && (
              <Badge variant="outline" className="text-xs font-bold px-3.5 py-1 rounded-[10px] text-red-500 border-red-500/25 bg-red-500/[0.04] max-sm:text-[0.65rem] max-sm:px-2.5 max-sm:py-0.5">
                {wrongCount} sai
              </Badge>
            )}
            <Button variant="outline" size="xs"
              className="rounded-[10px] border-dashed text-xs font-bold text-[var(--text-tertiary)] hover:text-red-500 hover:border-red-500/40 hover:bg-red-500/[0.04] max-sm:text-[0.65rem]"
              onClick={handleReset}
            >
              ↺ Làm lại
            </Button>
          </div>
        )}

        {loading && <div className="py-16 text-center text-sm text-[var(--text-tertiary)]">Đang tải...</div>}
        {!loading && questions.length === 0 && (
          <div className="py-16 text-center text-sm text-[var(--text-tertiary)]">Chưa có câu hỏi{level ? ` cho ${level}` : ""}.</div>
        )}

        {!loading && questions.length > 0 && (
          <QuizGrid
            questions={gridQuestions}
            baseUrl="/exam/bunpou/q"
          />
        )}
      </div>
    </div>
  );
}
