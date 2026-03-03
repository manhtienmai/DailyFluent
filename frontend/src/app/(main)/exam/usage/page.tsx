"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import QuizGrid, { GridQuestion } from "@/components/quiz/QuizGrid";
import { getQuizProgress, resetQuizProgress } from "@/lib/quiz-progress";
import "./usage-list.css";

const LEVELS = ["", "N1", "N2", "N3", "N4", "N5"];

interface QuestionStub {
  num: number; id: number; correct_answer: string;
}

export default function UsageGridPage() {
  const [questions, setQuestions] = useState<QuestionStub[]>([]);
  const [loading, setLoading] = useState(true);
  const [level, setLevel] = useState("");
  const [progress, setProgress] = useState(getQuizProgress("usage", ""));

  const fetchAll = useCallback(() => {
    setLoading(true);
    const url = level
      ? `/api/v1/exam/usage/all-questions?level=${level}`
      : `/api/v1/exam/usage/all-questions`;
    fetch(url, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : { questions: [] }))
      .then((d) => {
        setQuestions(
          (d.questions || []).map((q: any) => ({
            num: q.num, id: q.id, correct_answer: q.correct_answer,
          }))
        );
        setLoading(false);
        setProgress(getQuizProgress("usage", level));
      })
      .catch(() => setLoading(false));
  }, [level]);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  // Re-read progress when page gains focus (returning from question page)
  useEffect(() => {
    const onFocus = () => setProgress(getQuizProgress("usage", level));
    window.addEventListener("focus", onFocus);
    return () => window.removeEventListener("focus", onFocus);
  }, [level]);

  // Also re-read on visibilitychange for mobile
  useEffect(() => {
    const onVisible = () => {
      if (document.visibilityState === "visible") {
        setProgress(getQuizProgress("usage", level));
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
    resetQuizProgress("usage", level);
    setProgress(getQuizProgress("usage", level));
  };

  const levelParam = level ? `?level=${level}` : "";

  return (
    <div className="ugp">
      <div className="ugp-container">
        <nav className="ugp-breadcrumb">
          <Link href="/exam">Luyện thi</Link>
          <span>/</span>
          <span className="current">用法 Cách dùng từ</span>
        </nav>

        <h1 className="ugp-title">✍️ 用法 — Cách dùng từ</h1>
        <p className="ugp-desc">Chọn câu để làm bài. Bấm vào ô số để chuyển câu.</p>

        {/* Level filter */}
        <div className="ugp-filters">
          {LEVELS.map((l) => (
            <button key={l} className={`ugp-filter ${level === l ? "active" : ""}`}
              onClick={() => setLevel(l)}>
              {l || "Tất cả"}
            </button>
          ))}
        </div>

        {/* Stats */}
        {answeredCount > 0 && (
          <div className="ugp-stats">
            <span className="ugp-stat">{answeredCount}/{questions.length} đã làm</span>
            {correctCount > 0 && <span className="ugp-stat ok">{correctCount} đúng</span>}
            {wrongCount > 0 && <span className="ugp-stat bad">{wrongCount} sai</span>}
            <button className="ugp-stat reset" onClick={handleReset}>↺ Làm lại</button>
          </div>
        )}

        {loading && <div className="ugp-empty">Đang tải...</div>}
        {!loading && questions.length === 0 && (
          <div className="ugp-empty">Chưa có câu hỏi{level ? ` cho ${level}` : ""}.</div>
        )}

        {!loading && questions.length > 0 && (
          <QuizGrid
            questions={gridQuestions}
            baseUrl="/exam/usage/q"
          />
        )}
      </div>

      
    </div>
  );
}
