"use client";

/**
 * QuizQuestionPage — Reusable config-driven quiz question page (Template Method Pattern).
 *
 * Eliminates duplication between usage/q/[num] and bunpou/q/[num].
 * The page structure is identical; only the config differs.
 *
 * Usage:
 *   const CONFIG = { quizType: "bunpou", apiUrl: "/api/v1/exam/bunpou/all-questions", ... };
 *   export default function Page() { return <QuizQuestionPage config={CONFIG} />; }
 */

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import QuizQuestion, { QuizQuestionData } from "@/components/quiz/QuizQuestion";
import { getQuizProgress, saveQuizProgress } from "@/lib/quiz-progress";

export interface QuizPageConfig {
  /** Quiz type identifier (e.g. "usage", "bunpou") — used for localStorage key */
  quizType: string;
  /** Backend API URL to fetch all questions */
  apiUrl: string;
  /** Base path for question URLs (e.g. "/exam/usage/q") */
  basePath: string;
  /** Grid page URL (e.g. "/exam/usage") */
  gridUrl: string;
}

interface QuizQuestionPageProps {
  config: QuizPageConfig;
}

export default function QuizQuestionPage({ config }: QuizQuestionPageProps) {
  const { quizType, apiUrl, basePath, gridUrl } = config;
  const params = useParams();
  const router = useRouter();
  const num = parseInt(params.num as string, 10);
  const [questions, setQuestions] = useState<QuizQuestionData[]>([]);
  const [loading, setLoading] = useState(true);
  const [progress, setProgress] = useState(getQuizProgress(quizType, ""));

  useEffect(() => {
    fetch(apiUrl, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : { questions: [] }))
      .then((d) => {
        setQuestions(
          (d.questions || []).map((q: any) => ({
            num: q.num, id: q.id, text: q.text, text_vi: q.text_vi,
            choices: q.choices, correct_answer: q.correct_answer,
            explanation_json: q.explanation_json,
            level: q.level, template_title: q.template_title,
          }))
        );
        setLoading(false);
        setProgress(getQuizProgress(quizType, ""));
      })
      .catch(() => setLoading(false));
  }, [apiUrl, quizType]);

  const currentQ = questions.find((q) => q.num === num) || null;
  const totalQ = questions.length;

  const handleAnswer = useCallback((questionId: number, key: string) => {
    setProgress((prev) => {
      const next = {
        ...prev,
        answers: { ...prev.answers, [String(questionId)]: key },
        revealed: [...new Set([...prev.revealed, num])],
        lastQuestion: num,
      };
      saveQuizProgress(quizType, "", next);
      return next;
    });
  }, [num, quizType]);

  /* ── Keyboard arrow navigation ← → ── */
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;
      if (e.key === "ArrowLeft" && num > 1) {
        e.preventDefault();
        router.push(`${basePath}/${num - 1}`);
      } else if (e.key === "ArrowRight" && num < questions.length) {
        e.preventDefault();
        router.push(`${basePath}/${num + 1}`);
      }
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [num, questions.length, router, basePath]);

  const handleBookmark = useCallback((qNum: number) => {
    setProgress((prev) => {
      const bm = new Set(prev.bookmarked);
      if (bm.has(qNum)) bm.delete(qNum); else bm.add(qNum);
      const next = { ...prev, bookmarked: Array.from(bm) };
      saveQuizProgress(quizType, "", next);
      return next;
    });
  }, [quizType]);

  if (loading) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Đang tải...</div>;
  if (!currentQ) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Không tìm thấy câu {num}.</div>;

  const savedAnswer = progress.answers[String(currentQ.id)];
  const isRevealed = progress.revealed.includes(num);
  const isBookmarked = progress.bookmarked.includes(num);

  // If the saved answer is WRONG, auto-reset so the user can retry fresh
  // without ever seeing the correct answer highlighted
  const wasWrong = savedAnswer && savedAnswer !== currentQ.correct_answer;
  const effectiveRevealed = isRevealed && !wasWrong;
  const effectiveAnswer = wasWrong ? undefined : savedAnswer;

  return (
    <QuizQuestion
      question={currentQ}
      totalQuestions={totalQ}
      savedAnswer={effectiveAnswer}
      isRevealed={effectiveRevealed}
      isBookmarked={isBookmarked}
      onAnswer={handleAnswer}
      onBookmark={handleBookmark}
      prevUrl={num > 1 ? `${basePath}/${num - 1}` : null}
      nextUrl={num < totalQ ? `${basePath}/${num + 1}` : null}
      gridUrl={gridUrl}
      quizType={quizType as "usage" | "bunpou"}
    />
  );
}
