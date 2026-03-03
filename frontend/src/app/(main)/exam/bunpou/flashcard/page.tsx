"use client";

/**
 * Bunpou Grammar Flashcard Review Page
 * Front: grammar_point (name only) + level badge
 * Back: grammar_structure + grammar_meaning + grammar_note
 * FSRS grading: user rates memory (Again / Hard / Good / Easy)
 * Includes JLPT level stats and level filtering.
 */

import { useState, useEffect, useCallback, useRef, useMemo } from "react";
import Link from "next/link";
import { apiFetch, apiUrl } from "@/lib/api";
import { useStudyTimer } from "@/hooks/useStudyTimer";
import FsrsGradeBar from "@/components/FsrsGradeBar";
import type { FsrsIntervals } from "@/components/FsrsGradeBar";
import "./bunpou-flashcard.css";

const LEVEL_COLORS: Record<string, string> = {
  N1: "#dc2626", N2: "#2563eb", N3: "#eab308", N4: "#3b82f6", N5: "#10b981",
};
const LEVELS = ["", "N5", "N4", "N3", "N2", "N1"];

interface GrammarCard {
  id: number;
  grammar_point: string;
  grammar_structure: string;
  grammar_meaning: string;
  grammar_note: string;
  grammar_furigana: string;
  level: string;
  state_id: number | null;
  is_new: boolean;
  intervals: FsrsIntervals | null;
}

interface SessionStats {
  total: number;
  learning: number;
  review: number;
  new: number;
}

export default function BunpouFlashcardPage() {
  useStudyTimer();
  const [cards, setCards] = useState<GrammarCard[]>([]);
  const [stats, setStats] = useState<SessionStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [filterLevel, setFilterLevel] = useState("");
  const [idx, setIdx] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [grading, setGrading] = useState(false);
  const [gradingLoading, setGradingLoading] = useState(false);
  const touchStart = useRef<number | null>(null);
  const reviewed = useRef(0);
  const startTime = useRef(Date.now());

  const fetchCards = useCallback(async (level?: string) => {
    setLoading(true);
    try {
      // Sync quiz grammar patterns into FSRS first
      await fetch("/api/v1/exam/bunpou/sync-to-fsrs", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
      }).catch(() => {}); // ignore sync errors

      const params = level ? `?level=${level}` : "";
      const data = await apiFetch<{ cards: GrammarCard[]; stats: SessionStats }>(
        apiUrl(`/grammar/flashcards${params}`)
      );
      setCards(data.cards);
      setStats(data.stats);
      setIdx(0);
      setFlipped(false);
      setGrading(false);
    } catch (err) {
      console.error("Failed to fetch grammar flashcards:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCards(filterLevel || undefined);
  }, [filterLevel, fetchCards]);

  const currentCard = cards[idx];
  const total = cards.length;

  const goNext = useCallback(() => {
    if (idx < cards.length - 1) {
      setIdx((i) => i + 1);
      setFlipped(false);
      setGrading(false);
    }
  }, [idx, cards.length]);

  const goPrev = useCallback(() => {
    if (idx > 0) {
      setIdx((i) => i - 1);
      setFlipped(false);
      setGrading(false);
    }
  }, [idx]);

  const toggleFlip = useCallback(() => {
    setFlipped((f) => {
      if (!f) setGrading(true);
      return !f;
    });
  }, []);

  // FSRS grade handler — calls backend
  const handleGrade = useCallback(async (rating: string) => {
    if (!currentCard || gradingLoading) return;
    setGradingLoading(true);
    try {
      const result = await apiFetch<{
        success?: boolean;
        intervals?: FsrsIntervals;
        requeue?: boolean;
        requeue_delay_ms?: number;
      }>(apiUrl("/grammar/flashcards/grade"), {
        method: "POST",
        body: JSON.stringify({
          grammar_point_id: currentCard.id,
          rating,
        }),
      });

      reviewed.current++;

      // Update current card intervals
      if (result.intervals) {
        setCards((prev) =>
          prev.map((c, i) =>
            i === idx ? { ...c, intervals: result.intervals! } : c
          )
        );
      }

      // Advance to next card
      if (idx < cards.length - 1) {
        setIdx((i) => i + 1);
        setFlipped(false);
        setGrading(false);
      } else {
        setFlipped(false);
        setGrading(false);
      }
    } catch (err) {
      console.error("Failed to grade card:", err);
    } finally {
      setGradingLoading(false);
    }
  }, [currentCard, gradingLoading, idx, cards.length]);

  // Keyboard
  useEffect(() => {
    const RATINGS_ORDER = ["again", "hard", "good", "easy"] as const;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight") goNext();
      else if (e.key === "ArrowLeft") goPrev();
      else if (e.key === " " || e.key === "Enter") {
        e.preventDefault();
        toggleFlip();
      }
      else if (flipped && grading && ["1", "2", "3", "4"].includes(e.key)) {
        handleGrade(RATINGS_ORDER[parseInt(e.key) - 1]);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [goNext, goPrev, toggleFlip, flipped, grading, handleGrade]);

  // Touch swipe
  const onTouchStart = (e: React.TouchEvent) => {
    touchStart.current = e.touches[0].clientX;
  };
  const onTouchEnd = (e: React.TouchEvent) => {
    if (touchStart.current === null) return;
    const diff = e.changedTouches[0].clientX - touchStart.current;
    if (Math.abs(diff) > 60) {
      if (diff > 0) goPrev();
      else goNext();
    }
    touchStart.current = null;
  };

  /** Render text with <ruby> furigana above kanji characters */
  const renderWithRuby = (text: string, furigana: string) => {
    if (!furigana || !text) return <>{text}</>;
    const clean = text.replace(/～/g, "");
    if (!/[\u4e00-\u9fff\u3400-\u4dbf]/.test(clean)) return <>{text}</>;
    const parts: React.ReactNode[] = [];
    if (text.startsWith("～")) parts.push("～");
    let ti = 0, fi = 0;
    while (ti < clean.length && fi < furigana.length) {
      const ch = clean[ti];
      const isK = /[\u4e00-\u9fff\u3400-\u4dbf]/.test(ch);
      if (!isK) {
        parts.push(ch);
        ti++; fi++;
      } else {
        let ke = ti + 1;
        while (ke < clean.length && /[\u4e00-\u9fff\u3400-\u4dbf]/.test(clean[ke])) ke++;
        const kanjiStr = clean.slice(ti, ke);
        const nextCh = ke < clean.length ? clean[ke] : null;
        let fe = furigana.length;
        if (nextCh) {
          const fidx = furigana.indexOf(nextCh, fi);
          if (fidx !== -1) fe = fidx;
        }
        const reading = furigana.slice(fi, fe);
        parts.push(<ruby key={ti}>{kanjiStr}<rt>{reading}</rt></ruby>);
        ti = ke; fi = fe;
      }
    }
    if (ti < clean.length) parts.push(clean.slice(ti));
    return <>{parts}</>;
  };

  const cardLevelColor = currentCard ? (LEVEL_COLORS[currentCard.level] || "#475569") : "#475569";
  const isComplete = total > 0 && idx >= total - 1 && !flipped && reviewed.current >= total;

  if (loading) {
    return (
      <div className="bfc-page">
        <div className="bfc-top">
          <Link href="/exam/study" className="bfc-back">← Kho Học Tập</Link>
          <h1 className="bfc-title">🃏 Flashcard Ngữ pháp</h1>
        </div>
        <div className="bfc-empty">
          <div className="bfc-empty-icon">⏳</div>
          <div className="bfc-empty-text">Đang tải...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="bfc-page">
      {/* Top bar */}
      <div className="bfc-top">
        <Link href="/exam/study" className="bfc-back">← Kho Học Tập</Link>
        <h1 className="bfc-title">🃏 Flashcard Ngữ pháp</h1>
      </div>




      {/* Level filter */}
      <div className="bfc-filters">
        {LEVELS.map((l) => (
          <button
            key={l}
            className={`bfc-filter ${filterLevel === l ? "active" : ""}`}
            onClick={() => setFilterLevel(l)}
            style={filterLevel === l && l ? { background: LEVEL_COLORS[l], borderColor: LEVEL_COLORS[l] } : undefined}
          >
            {l || "Tất cả"}
          </button>
        ))}
      </div>

      {/* Stats */}
      {stats && (
        <div className="bfc-progress">
          <div className="bfc-progress-bar">
            <div
              className="bfc-progress-fill"
              style={{ width: total > 0 ? `${((idx + 1) / total) * 100}%` : '0%' }}
            />
          </div>
          <span className="bfc-progress-text">
            {total > 0 ? `${idx + 1} / ${total}` : 'Không có thẻ'}
            {stats.review > 0 && ` · ${stats.review} ôn`}
            {stats.new > 0 && ` · ${stats.new} mới`}
          </span>
        </div>
      )}

      {/* Card area */}
      <div
        className="bfc-card-area"
        onTouchStart={onTouchStart}
        onTouchEnd={onTouchEnd}
      >
        {cards.length === 0 ? (
          <div className="bfc-empty">
            <div className="bfc-empty-icon">🎉</div>
            <div className="bfc-empty-text">Hôm nay không còn thẻ nào cần ôn!</div>
            <div className="bfc-empty-hint">
              {stats ? `Tổng: ${stats.total} mẫu đã học` : ''}
            </div>
            <Link href="/exam/bunpou" className="bfc-empty-btn">
              → Đi làm bài quiz
            </Link>
          </div>
        ) : cards.length === 0 ? (
          <div className="bfc-empty">
            <div className="bfc-empty-icon">🔍</div>
            <div className="bfc-empty-text">Không có mẫu nào cho {filterLevel}</div>
            <button className="bfc-empty-btn" onClick={() => setFilterLevel("")}>
              Xem tất cả
            </button>
          </div>
        ) : isComplete ? (
          <div className="bfc-empty">
            <div className="bfc-empty-icon">🎉</div>
            <div className="bfc-empty-text">Hoàn thành!</div>
            <div className="bfc-empty-hint">
              Bạn đã ôn tập {reviewed.current} mẫu ngữ pháp
            </div>
            <button className="bfc-empty-btn" onClick={() => fetchCards(filterLevel || undefined)}>
              🔄 Tải lại
            </button>
          </div>
        ) : currentCard ? (
          <div className="bfc-card-perspective" onClick={toggleFlip}>
            <div className={`bfc-card ${flipped ? "flipped" : ""}`}>
              {/* FRONT — only grammar_point name + level badge */}
              <div className="bfc-face bfc-front">
                {currentCard.level && (
                  <span className="bfc-level-tag" style={{
                    color: cardLevelColor,
                    background: `${cardLevelColor}12`,
                  }}>
                    {currentCard.level}
                  </span>
                )}
                <div className="bfc-card-title">
                  {currentCard.grammar_furigana
                    ? renderWithRuby(currentCard.grammar_point, currentCard.grammar_furigana)
                    : currentCard.grammar_point
                  }
                </div>
                <div className="bfc-hint">tap to flip</div>
              </div>

              {/* BACK — structure + meaning + note */}
              <div className="bfc-face bfc-back-face">
                <div className="bfc-back-scroll">
                  <div className="bfc-back-top-row">
                    <div className="bfc-card-title-sm">
                      {currentCard.grammar_furigana
                        ? renderWithRuby(currentCard.grammar_point, currentCard.grammar_furigana)
                        : currentCard.grammar_point
                      }
                    </div>
                    {currentCard.level && (
                      <span className="bfc-level-tag-sm" style={{
                        color: cardLevelColor,
                        background: `${cardLevelColor}12`,
                      }}>
                        {currentCard.level}
                      </span>
                    )}
                  </div>
                  {currentCard.grammar_structure && (
                    <div className="bfc-section">
                      <div className="bfc-section-label">構造</div>
                      <div className="bfc-formation">{currentCard.grammar_structure}</div>
                    </div>
                  )}
                  {currentCard.grammar_meaning && (
                    <div className="bfc-section">
                      <div className="bfc-section-label">意味</div>
                      <div className="bfc-meaning">{currentCard.grammar_meaning}</div>
                    </div>
                  )}
                  {currentCard.grammar_note && (
                    <div className="bfc-section">
                      <div className="bfc-section-label">メモ</div>
                      <div className="bfc-note">{currentCard.grammar_note}</div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        ) : null}
      </div>

      {/* FSRS Grading — reusable component */}
      {cards.length > 0 && flipped && grading && (
        <FsrsGradeBar
          onGrade={handleGrade}
          intervals={currentCard?.intervals}
        />
      )}

      {/* Nav buttons — show when not grading */}
      {cards.length > 0 && !grading && (
        <div className="bfc-nav">
          <button className="bfc-nav-btn" onClick={goPrev} disabled={idx === 0}>
            ←
          </button>
          <button className="bfc-nav-btn flip" onClick={toggleFlip}>
            ↻
          </button>
          <button className="bfc-nav-btn" onClick={goNext} disabled={idx >= cards.length - 1}>
            →
          </button>
        </div>
      )}

      
    </div>
  );
}
