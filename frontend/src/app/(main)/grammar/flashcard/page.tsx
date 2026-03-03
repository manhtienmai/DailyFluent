"use client";

/**
 * Grammar Flashcard Review Page
 * Front: grammar title + formation
 * Back: meaning, explanation, examples
 * Swipe/keyboard navigation, responsive for mobile
 */

import { useState, useEffect, useCallback, useRef } from "react";
import Link from "next/link";
import "./grammar-flashcard.css";

interface GrammarExample {
  id: number;
  sentence_jp: string;
  sentence_vi: string;
  highlighted_jp: string;
}

interface GrammarCard {
  id: number;
  title: string;
  slug: string;
  level: string;
  meaning: string;
  structure: string;
  summary?: string;
  explanation?: string;
  details?: string;
  notes?: string;
  examples?: GrammarExample[];
}

export default function GrammarFlashcardPage() {
  const [cards, setCards] = useState<GrammarCard[]>([]);
  const [idx, setIdx] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [level, setLevel] = useState("N2");
  const [loading, setLoading] = useState(true);
  const touchStart = useRef<number | null>(null);

  const levels = ["N5", "N4", "N3", "N2", "N1"];

  // Fetch cards
  useEffect(() => {
    setLoading(true);
    setFlipped(false);
    setIdx(0);
    fetch(`/api/v1/grammar/points?level=${level}`, { credentials: "include" })
      .then((r) => r.json())
      .then((data) => {
        setCards(data || []);
        setLoading(false);
        // Pre-fetch details for first card
        if (data?.length) prefetchDetail(data[0].slug);
      })
      .catch(() => setLoading(false));
  }, [level]);

  // Prefetch detail for back of card
  const detailCache = useRef<Record<string, GrammarCard>>({});
  const prefetchDetail = useCallback((slug: string) => {
    if (detailCache.current[slug]) return;
    fetch(`/api/v1/grammar/${slug}`, { credentials: "include" })
      .then((r) => r.json())
      .then((d) => {
        detailCache.current[slug] = d;
      })
      .catch(() => {});
  }, []);

  const currentCard = cards[idx];
  const detail = currentCard ? detailCache.current[currentCard.slug] : null;

  // Nav functions
  const goNext = useCallback(() => {
    if (idx < cards.length - 1) {
      setIdx((i) => i + 1);
      setFlipped(false);
      // Prefetch next detail
      if (cards[idx + 2]) prefetchDetail(cards[idx + 2].slug);
    }
  }, [idx, cards, prefetchDetail]);

  const goPrev = useCallback(() => {
    if (idx > 0) {
      setIdx((i) => i - 1);
      setFlipped(false);
    }
  }, [idx]);

  const toggleFlip = useCallback(() => {
    setFlipped((f) => !f);
    // Prefetch detail when flipping to back
    if (!flipped && currentCard && !detailCache.current[currentCard.slug]) {
      prefetchDetail(currentCard.slug);
    }
    // Prefetch next card detail
    if (cards[idx + 1]) prefetchDetail(cards[idx + 1].slug);
  }, [flipped, currentCard, idx, cards, prefetchDetail]);

  // Keyboard
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight") goNext();
      else if (e.key === "ArrowLeft") goPrev();
      else if (e.key === " " || e.key === "Enter") {
        e.preventDefault();
        toggleFlip();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [goNext, goPrev, toggleFlip]);

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

  // Render highlighted example
  const renderExample = (ex: GrammarExample) => {
    const html = ex.highlighted_jp || ex.sentence_jp;
    return (
      <div key={ex.id} className="gfc-example">
        <div className="gfc-ex-jp" dangerouslySetInnerHTML={{ __html: html }} />
        <div className="gfc-ex-vi">{ex.sentence_vi}</div>
      </div>
    );
  };

  return (
    <div className="gfc-page">
      {/* Level selector */}
      <div className="gfc-top">
        <Link href="/grammar" className="gfc-back">← Ngữ pháp</Link>
        <div className="gfc-levels">
          {levels.map((l) => (
            <button
              key={l}
              className={`gfc-level-btn ${level === l ? "active" : ""}`}
              onClick={() => setLevel(l)}
            >
              {l}
            </button>
          ))}
        </div>
      </div>

      {/* Progress */}
      {cards.length > 0 && (
        <div className="gfc-progress">
          <div className="gfc-progress-bar">
            <div
              className="gfc-progress-fill"
              style={{ width: `${((idx + 1) / cards.length) * 100}%` }}
            />
          </div>
          <span className="gfc-progress-text">{idx + 1} / {cards.length}</span>
        </div>
      )}

      {/* Card area */}
      <div
        className="gfc-card-area"
        onTouchStart={onTouchStart}
        onTouchEnd={onTouchEnd}
      >
        {loading ? (
          <div className="gfc-loading">
            <div className="gfc-spinner" />
          </div>
        ) : cards.length === 0 ? (
          <div className="gfc-empty">Chưa có ngữ pháp {level}</div>
        ) : currentCard ? (
          <div
            className={`gfc-card-perspective`}
            onClick={toggleFlip}
          >
            <div className={`gfc-card ${flipped ? "flipped" : ""}`}>
              {/* FRONT */}
              <div className="gfc-face gfc-front">
                <span className="gfc-level-tag">{currentCard.level}</span>
                <div className="gfc-title">{currentCard.title}</div>
                {currentCard.structure && (
                  <div className="gfc-structure">{currentCard.structure}</div>
                )}
                <div className="gfc-hint">tap to flip</div>
              </div>

              {/* BACK */}
              <div className="gfc-face gfc-back">
                <div className="gfc-back-scroll">
                  <span className="gfc-level-tag">{currentCard.level}</span>
                  <div className="gfc-title-sm">{currentCard.title}</div>
                  <div className="gfc-meaning">{currentCard.meaning || detail?.meaning}</div>

                  {(detail?.structure || currentCard.structure) && (
                    <div className="gfc-section">
                      <div className="gfc-section-label">構造</div>
                      <div className="gfc-formation">{detail?.structure || currentCard.structure}</div>
                    </div>
                  )}

                  {detail?.explanation && (
                    <div className="gfc-section">
                      <div className="gfc-section-label">説明</div>
                      <div className="gfc-explanation">{detail.explanation}</div>
                    </div>
                  )}

                  {detail?.notes && (
                    <div className="gfc-section">
                      <div className="gfc-section-label">メモ</div>
                      <div className="gfc-notes">{detail.notes}</div>
                    </div>
                  )}

                  {detail?.examples && detail.examples.length > 0 && (
                    <div className="gfc-section">
                      <div className="gfc-section-label">例文</div>
                      {detail.examples.map(renderExample)}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        ) : null}
      </div>

      {/* Nav buttons */}
      {cards.length > 0 && (
        <div className="gfc-nav">
          <button className="gfc-nav-btn" onClick={goPrev} disabled={idx === 0}>
            ←
          </button>
          <button className="gfc-nav-btn flip" onClick={toggleFlip}>
            ↻
          </button>
          <button className="gfc-nav-btn" onClick={goNext} disabled={idx >= cards.length - 1}>
            →
          </button>
        </div>
      )}

      
    </div>
  );
}
