"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

interface ExamQuestion {
  id: number;
  text: string;
  text_html: string;
  choices: { key: string; text: string }[];
  image_url?: string;
  audio_url?: string;
  group_label?: string;
}

interface ExamSession {
  session_id: number;
  exam_title: string;
  questions: ExamQuestion[];
  duration_minutes: number;
  is_toeic: boolean;
}

export default function ExamTakePage() {
  const params = useParams();
  const sessionId = params.sessionId as string;

  const [data, setData] = useState<ExamSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [timeLeft, setTimeLeft] = useState<number | null>(null);
  const [currentGroup, setCurrentGroup] = useState(0);

  useEffect(() => {
    fetch(`/api/v1/exam/session/${sessionId}`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d: ExamSession) => {
        setData(d);
        if (d.duration_minutes > 0) setTimeLeft(d.duration_minutes * 60);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [sessionId]);

  // Timer
  useEffect(() => {
    if (timeLeft === null || timeLeft <= 0 || submitted) return;
    const t = setInterval(() => setTimeLeft((t) => (t !== null && t > 0 ? t - 1 : 0)), 1000);
    return () => clearInterval(t);
  }, [timeLeft, submitted]);

  // Auto-submit on timeout
  useEffect(() => {
    if (timeLeft === 0 && !submitted) handleSubmit();
  }, [timeLeft, submitted]);

  const handleSubmit = useCallback(async () => {
    if (submitting || submitted) return;
    setSubmitting(true);
    try {
      await fetch(`/exam/session/${sessionId}/result/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ answers }),
      });
      window.location.href = `/exam/session/${sessionId}/result`;
    } catch {
      setSubmitting(false);
    }
  }, [sessionId, answers, submitting, submitted]);

  const formatTime = (s: number) => {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return `${m}:${sec.toString().padStart(2, "0")}`;
  };

  const answeredCount = Object.keys(answers).length;
  const totalCount = data?.questions?.length || 0;

  if (loading) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Đang tải bài thi...</div>;
  if (!data) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Không tìm thấy. API chưa sẵn sàng.</div>;

  // Group questions
  const groups = data.questions.reduce<{ label: string; questions: ExamQuestion[] }[]>((acc, q) => {
    const label = q.group_label || "Phần chung";
    const existing = acc.find((g) => g.label === label);
    if (existing) existing.questions.push(q);
    else acc.push({ label, questions: [q] });
    return acc;
  }, []);

  const activeGroup = groups[currentGroup] || groups[0];

  return (
    <div style={{ padding: "24px", minHeight: "100vh" }}>
      <div className="max-w-4xl mx-auto">
        {/* Sticky header */}
        <div className="sticky top-0 z-20 flex items-center justify-between gap-4 p-4 rounded-2xl mb-5" style={{ background: "var(--bg-surface)", borderBottom: "1px solid var(--border-default)", backdropFilter: "blur(12px)" }}>
          <div>
            <h1 className="text-sm font-bold" style={{ color: "var(--text-primary)" }}>{data.exam_title}</h1>
            <span className="text-xs" style={{ color: "var(--text-tertiary)" }}>{answeredCount}/{totalCount} đã trả lời</span>
          </div>
          {timeLeft !== null && (
            <div className="text-lg font-mono font-bold" style={{ color: timeLeft < 60 ? "#dc2626" : timeLeft < 300 ? "#f59e0b" : "var(--text-primary)" }}>
              ⏱ {formatTime(timeLeft)}
            </div>
          )}
          <button onClick={handleSubmit} disabled={submitting} className="px-4 py-2 rounded-xl text-sm font-semibold text-white" style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6)", opacity: submitting ? 0.6 : 1 }}>
            {submitting ? "Đang nộp..." : "Nộp bài"}
          </button>
        </div>

        {/* Group tabs */}
        {groups.length > 1 && (
          <div className="flex gap-2 mb-5 overflow-x-auto pb-1">
            {groups.map((g, i) => (
              <button key={g.label} onClick={() => setCurrentGroup(i)} className="px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all" style={{
                background: currentGroup === i ? "linear-gradient(135deg, #6366f1, #8b5cf6)" : "var(--bg-interactive)",
                color: currentGroup === i ? "#fff" : "var(--text-secondary)",
                border: currentGroup === i ? "none" : "1px solid var(--border-default)",
              }}>
                {g.label} ({g.questions.length})
              </button>
            ))}
          </div>
        )}

        {/* Questions */}
        <div className="space-y-4">
          {activeGroup?.questions.map((q, i) => (
            <div key={q.id} className="p-5 rounded-2xl" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
              <div className="flex items-start gap-3 mb-4">
                <span className="text-xs font-bold px-2 py-0.5 rounded flex-shrink-0" style={{ background: answers[q.id] ? "rgba(99,102,241,.1)" : "var(--bg-interactive)", color: answers[q.id] ? "#6366f1" : "var(--text-secondary)" }}>
                  {data.questions.indexOf(q) + 1}
                </span>
                {q.text_html ? (
                  <div className="text-sm flex-1" style={{ color: "var(--text-primary)" }} dangerouslySetInnerHTML={{ __html: q.text_html }} />
                ) : (
                  <p className="text-sm flex-1" style={{ color: "var(--text-primary)" }}>{q.text}</p>
                )}
              </div>
              {q.image_url && <img src={q.image_url} alt="" className="rounded-lg mb-3 max-w-full" style={{ maxHeight: "200px" }} />}
              {q.audio_url && <audio controls className="w-full mb-3" style={{ height: "36px" }}><source src={q.audio_url} type="audio/mpeg" /></audio>}
              <div className="space-y-2">
                {q.choices?.map((c) => (
                  <button key={c.key} onClick={() => setAnswers((p) => ({ ...p, [q.id]: c.key }))} className="w-full text-left p-3 rounded-xl border transition-all flex items-center gap-3" style={{
                    background: answers[q.id] === c.key ? "var(--bg-interactive)" : "var(--bg-surface)",
                    borderColor: answers[q.id] === c.key ? "var(--action-primary)" : "var(--border-default)",
                  }}>
                    <span className="w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold flex-shrink-0" style={{ background: answers[q.id] === c.key ? "var(--action-primary)" : "var(--bg-app-subtle)", color: answers[q.id] === c.key ? "#fff" : "var(--text-secondary)" }}>{c.key}</span>
                    <span className="text-sm" style={{ color: "var(--text-primary)" }}>{c.text}</span>
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
