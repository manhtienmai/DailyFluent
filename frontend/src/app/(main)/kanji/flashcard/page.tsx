"use client";

/**
 * Kanji Vocab Flashcard Page
 *
 * Uses the reusable FSRS grading system to review kanji vocabulary.
 * Cards are loaded from the user's "Từ vựng Kanji" study set via the
 * vocab flashcard API. Grading goes through /vocab/api/flashcard/grade/
 * which calls FsrsService.grade_card() on the backend.
 *
 * Front: Kanji word + reading
 * Back: Meaning + Han Viet (Sino-Vietnamese) + example sentence
 */

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { useFsrsGrading, FsrsCard } from "@/hooks/useFsrsGrading";
import FsrsGradeBar from "@/components/FsrsGradeBar";
import { useStudyTimer } from "@/hooks/useStudyTimer";
import "./kanji-flashcard.css";

interface KanjiFlashcard extends FsrsCard {
  id: number;
  word: string;
  reading: string;
  sino_vi: string;
  meaning: string;
  definition: string;
  example_text: string;
  example_translation: string;
}

export default function KanjiFlashcardPage() {
  useStudyTimer();
  const [initialCards, setInitialCards] = useState<KanjiFlashcard[]>([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({ learning: 0, review: 0, new: 0 });
  const touchStart = useRef<number | null>(null);

  // Fetch cards from the vocab flashcard API (same API as English vocab)
  useEffect(() => {
    fetch("/api/v1/vocab/flashcards", { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d) => {
        // Filter to only JP language cards if the API returns mixed
        const cards = (d.cards || []).filter(
          (c: KanjiFlashcard & { language?: string }) => c.language === "jp"
        );
        setInitialCards(cards);
        setStats({
          learning: d.stats?.learning_count || 0,
          review: d.stats?.review_count || 0,
          new: d.stats?.new_count || 0,
        });
        setLoading(false);
      })
      .catch(() => {
        setInitialCards([]);
        setLoading(false);
      });
  }, []);

  const fsrs = useFsrsGrading<KanjiFlashcard>({
    cards: initialCards,
    gradeUrl: "/vocab/api/flashcard/grade/",
    idField: "vocab_id",
    enableKeyboard: true,
  });

  // Touch swipe
  const onTouchStart = (e: React.TouchEvent) => {
    touchStart.current = e.touches[0].clientX;
  };
  const onTouchEnd = (e: React.TouchEvent) => {
    if (touchStart.current === null) return;
    const diff = e.changedTouches[0].clientX - touchStart.current;
    if (Math.abs(diff) > 60) {
      if (diff > 0) fsrs.prev();
      else fsrs.next();
    }
    touchStart.current = null;
  };

  const current = fsrs.current;

  return (
    <div className="kfc-page">
      {/* Top bar */}
      <div className="kfc-top">
        <Link href="/kanji" className="kfc-back">← Kanji</Link>
        <h1 className="kfc-title">🃏 Flashcard từ vựng Kanji</h1>
      </div>

      {/* Stats */}
      {!loading && initialCards.length > 0 && (
        <div className="kfc-stats">
          <span className="kfc-stat new">🆕 {stats.new} mới</span>
          <span className="kfc-stat learning">📖 {stats.learning} đang học</span>
          <span className="kfc-stat review">🔄 {stats.review} ôn tập</span>
        </div>
      )}

      {/* Progress */}
      {fsrs.total > 0 && !fsrs.complete && (
        <div className="kfc-progress">
          <div className="kfc-progress-bar">
            <div className="kfc-progress-fill" style={{ width: `${((fsrs.currentIndex + 1) / fsrs.total) * 100}%` }} />
          </div>
          <span className="kfc-progress-text">{fsrs.currentIndex + 1} / {fsrs.total}</span>
        </div>
      )}

      {/* Card area */}
      <div className="kfc-card-area" onTouchStart={onTouchStart} onTouchEnd={onTouchEnd}>
        {loading ? (
          <div className="kfc-empty">
            <div className="kfc-empty-icon kfc-pulse">📖</div>
            <div className="kfc-empty-text">Đang tải flashcards...</div>
          </div>
        ) : initialCards.length === 0 ? (
          <div className="kfc-empty">
            <div className="kfc-empty-icon">📭</div>
            <div className="kfc-empty-text">Chưa có từ vựng Kanji</div>
            <div className="kfc-empty-hint">
              Vào trang Kanji, chọn từ vựng và bấm &quot;Thêm vào bộ học&quot; để bắt đầu
            </div>
            <Link href="/kanji" className="kfc-empty-btn">→ Đi học Kanji</Link>
          </div>
        ) : fsrs.complete ? (
          <div className="kfc-empty">
            <div className="kfc-empty-icon">🎉</div>
            <div className="kfc-empty-text">Hoàn thành!</div>
            <div className="kfc-empty-hint">
              Bạn đã ôn tập {fsrs.reviewedCount} từ vựng Kanji
            </div>
            <button className="kfc-empty-btn" onClick={fsrs.reset}>🔄 Học lại</button>
          </div>
        ) : fsrs.waiting ? (
          <div className="kfc-empty">
            <div className="kfc-empty-icon kfc-pulse">⏳</div>
            <div className="kfc-empty-text">Đang chờ thẻ tiếp theo...</div>
          </div>
        ) : current ? (
          <div className="kfc-card-perspective" onClick={fsrs.flip}>
            <div className={`kfc-card ${fsrs.flipped ? "flipped" : ""}`}>
              {/* FRONT */}
              <div className="kfc-face kfc-front">
                <div className="kfc-card-word">{current.word}</div>
                <div className="kfc-card-reading">{current.reading}</div>
                <div className="kfc-hint">tap to flip</div>
              </div>

              {/* BACK */}
              <div className="kfc-face kfc-back-face">
                <div className="kfc-back-scroll">
                  <div className="kfc-back-word">{current.word}</div>
                  <div className="kfc-back-reading">{current.reading}</div>

                  {current.sino_vi && (
                    <div className="kfc-sino-vi">【{current.sino_vi}】</div>
                  )}

                  <div className="kfc-back-meaning">{current.meaning || current.definition}</div>

                  {current.example_text && (
                    <div className="kfc-example">
                      <div className="kfc-example-jp">{current.example_text}</div>
                      {current.example_translation && (
                        <div className="kfc-example-vi">{current.example_translation}</div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        ) : null}
      </div>

      {/* FSRS Grading */}
      {fsrs.total > 0 && fsrs.flipped && fsrs.grading && (
        <FsrsGradeBar
          onGrade={fsrs.grade}
          intervals={fsrs.intervals}
        />
      )}

      {/* Nav — show when not grading */}
      {fsrs.total > 0 && !fsrs.grading && !fsrs.complete && (
        <div className="kfc-nav">
          <button className="kfc-nav-btn" onClick={fsrs.prev} disabled={fsrs.currentIndex === 0}>←</button>
          <button className="kfc-nav-btn flip" onClick={fsrs.flip}>↻</button>
          <button className="kfc-nav-btn" onClick={fsrs.next} disabled={fsrs.currentIndex >= fsrs.total - 1}>→</button>
        </div>
      )}

      
    </div>
  );
}
