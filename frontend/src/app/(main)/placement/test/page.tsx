"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";

interface Question {
  id: number;
  question_text: string;
  skill_label: string;
  options: Record<string, string>;
  context_text?: string;
  question_audio?: string;
  context_audio?: string;
  question_image?: string;
}

export default function PlacementTestPage() {
  const router = useRouter();
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const [testId, setTestId] = useState<number | null>(null);
  const [question, setQuestion] = useState<Question | null>(null);
  const [nextQ, setNextQ] = useState<Question | null>(null);
  const [answered, setAnswered] = useState(0);
  const [maxQ] = useState(40);
  const [selected, setSelected] = useState<string | null>(null);
  const [showFeedback, setShowFeedback] = useState(false);
  const [correct, setCorrect] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [loading, setLoading] = useState(true);
  const [completed, setCompleted] = useState(false);
  const [score, setScore] = useState(0);
  const [canFinish, setCanFinish] = useState(false);
  const [startTime, setStartTime] = useState(Date.now());

  const startTest = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch("/placement/api/start-test/", { method: "POST", credentials: "include", headers: { "Content-Type": "application/json" } });
      const data = await res.json();
      if (data.question) {
        setTestId(data.test_id);
        setQuestion(data.question);
        setAnswered(data.progress?.answered || 0);
        setStartTime(Date.now());
      }
    } catch (e) { console.error(e); }
    setLoading(false);
  }, []);

  useEffect(() => { startTest(); }, [startTest]);

  const submitAnswer = async () => {
    if (!selected || submitting || !testId) return;
    setSubmitting(true);
    const timeSpent = Math.round((Date.now() - startTime) / 1000);
    try {
      const res = await fetch(`/placement/api/test/${testId}/answer/`, {
        method: "POST", credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question_id: question!.id, answer: selected, time_spent: timeSpent }),
      });
      const data = await res.json();
      if (data.completed) {
        setCompleted(true);
        setTimeout(() => router.push(`/placement/result/${testId}`), 1500);
      } else {
        setShowFeedback(true);
        setCorrect(data.correct_answer);
        setScore(data.progress?.estimated_score || 0);
        setCanFinish(data.progress?.can_finish || false);
        setAnswered(data.progress?.answered || answered + 1);
        setNextQ(data.question);
      }
    } catch (e) { console.error(e); }
    setSubmitting(false);
  };

  const goNext = () => {
    setQuestion(nextQ);
    setNextQ(null);
    setSelected(null);
    setShowFeedback(false);
    setCorrect(null);
    setStartTime(Date.now());
  };

  const finishEarly = async () => {
    if (!confirm("Bạn có chắc muốn kết thúc bài test sớm?")) return;
    try {
      await fetch(`/placement/api/test/${testId}/finish_early/`, { method: "POST", credentials: "include", headers: { "Content-Type": "application/json" } });
      router.push(`/placement/result/${testId}`);
    } catch (e) { console.error(e); }
  };

  if (completed) return (
    <div className="text-center py-20">
      <div className="text-6xl mb-4">✅</div>
      <h2 className="text-2xl font-bold mb-2" style={{ color: "var(--text-primary)" }}>Hoàn thành!</h2>
      <p className="text-sm" style={{ color: "var(--text-tertiary)" }}>Đang chuyển đến kết quả...</p>
    </div>
  );

  return (
    <div style={{ maxWidth: 768, margin: "0 auto", padding: "1.5rem 1rem" }}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <span className="text-sm" style={{ color: "var(--text-tertiary)" }}>Câu <b style={{ color: "var(--text-primary)" }}>{answered + 1}</b>/{maxQ}+</span>
          {question && <span className="px-3 py-1 rounded-full text-xs font-medium" style={{ background: "rgba(99,102,241,.12)", color: "#6366f1" }}>{question.skill_label}</span>}
        </div>
        <div className="flex items-center gap-3">
          {score > 0 && <span className="text-sm" style={{ color: "var(--text-tertiary)" }}>~<b style={{ color: "#6366f1" }}>{score}</b> điểm</span>}
          {canFinish && <button onClick={finishEarly} className="text-sm underline" style={{ color: "var(--text-tertiary)", background: "none", border: "none", cursor: "pointer" }}>Kết thúc sớm</button>}
        </div>
      </div>

      {/* Progress */}
      <div className="h-2 rounded-full overflow-hidden mb-6" style={{ background: "var(--border-default)" }}>
        <div className="h-full rounded-full transition-all" style={{ background: "linear-gradient(90deg, #6366f1, #8b5cf6)", width: `${Math.min((answered / 20) * 100, 100)}%` }} />
      </div>

      {loading ? (
        <div className="text-center py-20" style={{ color: "var(--text-tertiary)" }}>Đang tải câu hỏi...</div>
      ) : question && (
        <div className="p-6 md:p-8 rounded-2xl" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)", boxShadow: "0 4px 24px rgba(0,0,0,.06)" }}>
          {question.context_text && <div className="mb-6 p-4 rounded-xl text-sm whitespace-pre-wrap" style={{ background: "var(--bg-interactive)", color: "var(--text-secondary)" }}>{question.context_text}</div>}

          {(question.question_audio || question.context_audio) && (
            <div className="mb-6">
              <button onClick={() => audioRef.current?.play()} className="flex items-center gap-3 px-6 py-3 rounded-xl text-sm font-medium transition-all" style={{ background: "rgba(99,102,241,.1)", color: "#6366f1", border: "none", cursor: "pointer" }}>🔊 Phát audio</button>
              <audio ref={audioRef} src={question.context_audio || question.question_audio} />
            </div>
          )}

          {question.question_image && <img src={question.question_image} alt="Question" className="max-w-full rounded-xl shadow mb-6 mx-auto" />}

          <h2 className="text-xl font-semibold mb-6" style={{ color: "var(--text-primary)" }}>{question.question_text}</h2>

          <div className="space-y-3">
            {Object.entries(question.options).map(([key, text]) => {
              const isCorrect = showFeedback && key === correct;
              const isWrong = showFeedback && selected === key && key !== correct;
              const isSelected = !showFeedback && selected === key;
              return (
                <button key={key} onClick={() => !showFeedback && setSelected(key)} disabled={showFeedback}
                  className="w-full text-left p-4 rounded-xl flex items-center gap-4 transition-all"
                  style={{
                    background: isCorrect ? "linear-gradient(135deg, #10b981, #059669)" : isWrong ? "linear-gradient(135deg, #ef4444, #dc2626)" : isSelected ? "linear-gradient(135deg, #6366f1, #8b5cf6)" : "var(--bg-interactive)",
                    color: (isCorrect || isWrong || isSelected) ? "white" : "var(--text-primary)",
                    border: `2px solid ${(isCorrect || isWrong || isSelected) ? "transparent" : "var(--border-default)"}`,
                    cursor: showFeedback ? "default" : "pointer",
                  }}>
                  <span className="w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm flex-shrink-0" style={{
                    background: (isCorrect || isWrong || isSelected) ? "rgba(255,255,255,.2)" : "var(--bg-surface)",
                    color: (isCorrect || isWrong || isSelected) ? "white" : "var(--text-secondary)",
                  }}>{key}</span>
                  <span className="flex-1">{text}</span>
                </button>
              );
            })}
          </div>

          <div className="mt-8 flex justify-end">
            {!showFeedback ? (
              <button onClick={submitAnswer} disabled={!selected || submitting}
                className="px-8 py-3 rounded-xl font-bold text-white transition-all"
                style={{ background: selected ? "#6366f1" : "var(--border-default)", cursor: selected ? "pointer" : "not-allowed", border: "none" }}>
                {submitting ? "Đang xử lý..." : "Xác nhận"}
              </button>
            ) : (
              <button onClick={goNext} className="px-8 py-3 rounded-xl font-bold text-white" style={{ background: "#10b981", border: "none", cursor: "pointer" }}>
                Câu tiếp theo →
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
