"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useSearchParams } from "next/navigation";
import { useStudyTimer } from "@/hooks/useStudyTimer";
import "./flashcards.css";

interface FlashcardData {
  id: number;
  word: string;
  reading: string;
  sino_vi: string;
  meaning: string;
  definition: string;
  example_text: string;
  example_translation: string;
  language: "en" | "jp";
  intervals: { again: string; hard: string; good: string; easy: string };
}

const GRADE_BUTTONS = [
  { rating: "again", emoji: "😵", label: "Quên", color: "#ef4444", gradient: "linear-gradient(135deg, #fee2e2, #fecaca)" },
  { rating: "hard", emoji: "😣", label: "Khó", color: "#f59e0b", gradient: "linear-gradient(135deg, #fef3c7, #fde68a)" },
  { rating: "good", emoji: "🙂", label: "Tốt", color: "#10b981", gradient: "linear-gradient(135deg, #d1fae5, #a7f3d0)" },
  { rating: "easy", emoji: "😌", label: "Dễ", color: "#6366f1", gradient: "linear-gradient(135deg, #e0e7ff, #c7d2fe)" },
];

export default function FlashcardPage() {
  useStudyTimer();
  const [cards, setCards] = useState<FlashcardData[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [loading, setLoading] = useState(true);
  const [complete, setComplete] = useState(false);
  const [stats, setStats] = useState({ learning: 0, review: 0, new: 0 });
  const total = cards.length;
  const reviewed = useRef(0);
  const startTime = useRef(Date.now());

  const current = cards[currentIndex] || null;
  const progressPct = total > 0 ? (reviewed.current / total) * 100 : 0;

  const searchParams = useSearchParams();
  const language = searchParams.get("language") || "en";

  /* ── Fetch cards ── */
  useEffect(() => {
    fetch(`/api/v1/vocab/flashcards?language=${language}`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d: { cards: FlashcardData[]; stats: { learning_count: number; review_count: number; new_count: number } }) => {
        setCards(d.cards || []);
        setStats({ learning: d.stats?.learning_count || 0, review: d.stats?.review_count || 0, new: d.stats?.new_count || 0 });
        setLoading(false);
      })
      .catch(() => { setCards([]); setLoading(false); });
  }, [language]);

  /* ── Grade ── */
  const grade = useCallback(async (rating: string) => {
    if (!current) return;

    let requeue = false;
    let requeueDelayMs = 0;
    let newIntervals = current.intervals;

    try {
      const resp = await fetch("/vocab/api/flashcard/grade/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ vocab_id: current.id, rating }),
      });
      if (resp.ok) {
        const data = await resp.json();
        requeue = data.requeue ?? false;
        requeueDelayMs = data.requeue_delay_ms ?? 0;
        if (data.intervals) newIntervals = data.intervals;
      }
    } catch (e) {
      console.error("Grade failed:", e);
    }

    reviewed.current++;

    // Requeue: add card back to end of deck after delay (FSRS Learning steps)
    if (requeue) {
      const requeuedCard = { ...current, intervals: newIntervals };
      setTimeout(() => {
        setCards((prev) => [...prev, requeuedCard]);
      }, Math.max(requeueDelayMs, 500));
    }

    if (currentIndex < cards.length - 1) {
      setCurrentIndex((i) => i + 1);
      setFlipped(false);
    } else if (requeue) {
      // Last card but will be requeued — advance past end, wait for card to arrive
      setCurrentIndex((i) => i + 1);
      setFlipped(false);
    } else {
      setComplete(true);
    }
  }, [current, currentIndex, cards.length]);

  /* ── Auto-advance when requeued card appears at end of deck ── */
  useEffect(() => {
    // current is null when waiting for requeued card; it becomes non-null when card arrives
    if (!complete && !loading && current && cards.length > 0 && currentIndex === cards.length - 1) {
      // Requeued card has arrived — just make sure we're showing it (unflipped)
      setFlipped(false);
    }
  }, [cards.length, complete, loading, current, currentIndex]);

  /* ── Goal ring ── */
  const minutesElapsed = Math.floor((Date.now() - startTime.current) / 60000);
  const goalPct = Math.min(100, (minutesElapsed / 10) * 100);

  if (loading) {
    return <div className="fc-page"><div className="max-w-lg mx-auto text-center py-20" style={{ color: "var(--text-tertiary)" }}>Đang tải thẻ...</div></div>;
  }

  return (
    <div className="fc-page">
      <div className="max-w-lg mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-xl font-bold" style={{ color: "var(--text-primary)" }}>🎴 Luyện Flashcard</h1>
            <div className="flex gap-3 text-xs mt-1">
              <span style={{ color: "#f59e0b" }}>Learning: <strong>{stats.learning}</strong></span>
              <span style={{ color: "#6366f1" }}>Review: <strong>{stats.review}</strong></span>
              <span style={{ color: "#10b981" }}>New: <strong>{stats.new}</strong></span>
            </div>
          </div>
          <div className="flex items-center gap-2 text-sm" style={{ color: "var(--text-secondary)" }}>
            <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
            <span className="font-bold">{total}</span> thẻ
          </div>
        </div>


        {cards.length === 0 ? (
          /* Empty state */
          <div className="text-center py-16" style={{ color: "var(--text-secondary)" }}>
            <div className="text-5xl mb-4">📦</div>
            <h2 className="text-lg font-bold">Chưa có thẻ nào</h2>
            <p className="text-sm mt-1">Hiện chưa có thẻ nào đến hạn để ôn.</p>
          </div>
        ) : complete ? (
          /* Complete */
          <div className="fc-card text-center p-8">
            <div className="text-5xl mb-4">🎉</div>
            <h2 className="text-2xl font-bold mb-2" style={{ color: "var(--text-primary)" }}>Hết thẻ!</h2>
            <p className="text-sm mb-6" style={{ color: "var(--text-secondary)" }}>Bạn đã hoàn thành {total} thẻ. Muốn tiếp tục?</p>
            <button onClick={() => window.location.reload()} className="px-6 py-2.5 rounded-xl text-sm font-semibold text-white" style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6)" }}>
              Tiếp tục học thêm
            </button>
          </div>
        ) : !current ? (
          /* Waiting for requeued card */
          <div className="fc-card text-center p-8" style={{ animation: "pulse 1.5s infinite" }}>
            <div className="text-4xl mb-3">⏳</div>
            <p className="text-sm font-medium" style={{ color: "var(--text-secondary)" }}>Đang chờ thẻ tiếp theo...</p>
          </div>
        ) : (
          /* Card */
          <>
            {/* Progress bar */}
            <div className="h-1.5 rounded-full mb-5 overflow-hidden" style={{ background: "rgba(148,163,184,.15)" }}>
              <div className="h-full rounded-full transition-all" style={{ width: `${progressPct}%`, background: "linear-gradient(90deg, #6366f1, #8b5cf6)" }} />
            </div>

            <div className="fc-card p-6">
              {!flipped ? (
                /* Front */
                <div className="text-center">
                  <div className="text-4xl font-black mb-4" style={{ fontFamily: current.language === "jp" ? "'Noto Sans JP', sans-serif" : "inherit", color: "var(--text-primary)" }}>
                    {current.word}
                  </div>
                  {current.reading && (
                    <div className="text-sm mb-4" style={{ fontFamily: "'Noto Sans JP', sans-serif", color: "var(--text-secondary)" }}>{current.reading}</div>
                  )}
                  <button
                    onClick={() => setFlipped(true)}
                    className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl text-sm font-semibold text-white"
                    style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6)" }}
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    Lật thẻ
                  </button>
                </div>
              ) : (
                /* Back */
                <div>
                  <div className="text-center mb-4">
                    <div className="text-2xl font-bold" style={{ fontFamily: current.language === "jp" ? "'Noto Sans JP', sans-serif" : "inherit", color: "var(--text-primary)" }}>{current.word}</div>
                    {current.reading && <div className="text-sm" style={{ fontFamily: "'Noto Sans JP', sans-serif", color: "var(--text-secondary)" }}>{current.reading}</div>}
                  </div>

                  {current.sino_vi && (
                    <div className="mb-3">
                      <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded" style={{ background: "rgba(245,158,11,.1)", color: "#b45309" }}>Âm Hán Việt</span>
                      <div className="text-sm mt-1 font-medium" style={{ color: "var(--text-primary)" }}>{current.sino_vi}</div>
                    </div>
                  )}

                  <div className="mb-3">
                    <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded" style={{ background: "rgba(99,102,241,.1)", color: "#6366f1" }}>Nghĩa</span>
                    <div className="text-sm mt-1" style={{ color: "var(--text-primary)" }}>{current.meaning}</div>
                  </div>

                  {current.definition && (
                    <div className="text-xs p-2 rounded-lg mb-3" style={{ background: "var(--bg-app-subtle)", color: "var(--text-secondary)" }}>
                      {current.definition}
                    </div>
                  )}

                  {current.example_text && (
                    <div className="flex gap-2 p-3 rounded-xl mb-4" style={{ background: "var(--bg-interactive)", border: "1px solid var(--border-subtle)" }}>
                      <svg className="w-4 h-4 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20" style={{ color: "#6366f1" }}>
                        <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd" />
                      </svg>
                      <div className="flex-1">
                        <div className="text-sm" style={{ fontFamily: "'Noto Sans JP', sans-serif", color: "var(--text-primary)" }}>{current.example_text}</div>
                        {current.example_translation && <div className="text-xs mt-1" style={{ color: "var(--text-secondary)" }}>{current.example_translation}</div>}
                      </div>
                    </div>
                  )}

                  {/* Grade buttons */}
                  <div className="grid grid-cols-4 gap-2">
                    {GRADE_BUTTONS.map((b) => (
                      <button
                        key={b.rating}
                        onClick={() => grade(b.rating)}
                        className="flex flex-col items-center gap-1 py-3 rounded-xl transition-all hover:scale-105"
                        style={{ background: b.gradient, border: `1px solid ${b.color}22` }}
                      >
                        <span className="text-xl">{b.emoji}</span>
                        <span className="text-[11px] font-semibold" style={{ color: b.color }}>{b.label}</span>
                        <span className="text-[9px]" style={{ color: b.color + "99" }}>{current.intervals?.[b.rating as keyof typeof current.intervals] || ""}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </>
        )}
      </div>

      
    </div>
  );
}
