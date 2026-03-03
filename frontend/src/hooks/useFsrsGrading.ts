"use client";

/**
 * useFsrsGrading — Reusable hook for FSRS-powered flashcard grading.
 *
 * Handles:
 * - Card navigation (next/prev/flip)
 * - Backend grade submission (vocab cards)
 * - Client-side grade tracking (grammar cards)
 * - Anki-style requeue for learning cards
 * - Interval preview display
 * - Keyboard shortcuts (1-4 for grading, arrows for nav, space for flip)
 * - Completion tracking
 */

import { useState, useCallback, useRef, useEffect } from "react";

export interface FsrsIntervals {
  again: string;
  hard: string;
  good: string;
  easy: string;
}

export interface FsrsCard {
  /** Unique ID for the card (vocab_id for backend cards, or any string) */
  id: string | number;
  /** Preview intervals for each rating, updated after grading */
  intervals?: FsrsIntervals;
  /** Any extra data the consumer needs */
  [key: string]: unknown;
}

export interface UseFsrsGradingOptions<T extends FsrsCard> {
  /** Initial cards array */
  cards: T[];
  /** Backend URL for grading (if provided, grades are sent to backend) */
  gradeUrl?: string;
  /** Key in the POST body for the card ID (default: "vocab_id") */
  idField?: string;
  /** Called when all cards are reviewed */
  onComplete?: (reviewedCount: number) => void;
  /** Enable keyboard shortcuts (default: true) */
  enableKeyboard?: boolean;
}

export interface UseFsrsGradingReturn<T extends FsrsCard> {
  /** Current card (null when between requeued cards or complete) */
  current: T | null;
  /** Current index */
  currentIndex: number;
  /** Total cards in deck (may grow if cards are requeued) */
  total: number;
  /** Whether card is flipped */
  flipped: boolean;
  /** Whether grading buttons should be visible */
  grading: boolean;
  /** Whether session is complete */
  complete: boolean;
  /** Whether waiting for a requeued card */
  waiting: boolean;
  /** Number of cards reviewed */
  reviewedCount: number;
  /** Progress percentage */
  progressPct: number;
  /** Current card's intervals */
  intervals: FsrsIntervals | null;
  /** Flip the card */
  flip: () => void;
  /** Go to next card (without grading) */
  next: () => void;
  /** Go to previous card */
  prev: () => void;
  /** Grade the current card */
  grade: (rating: "again" | "hard" | "good" | "easy") => Promise<void>;
  /** Reset and start over */
  reset: () => void;
  /** The live cards array (may change due to requeue) */
  cards: T[];
}

export function useFsrsGrading<T extends FsrsCard>(
  options: UseFsrsGradingOptions<T>
): UseFsrsGradingReturn<T> {
  const {
    cards: initialCards,
    gradeUrl,
    idField = "vocab_id",
    onComplete,
    enableKeyboard = true,
  } = options;

  const [cards, setCards] = useState<T[]>(initialCards);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [grading, setGrading] = useState(false);
  const [complete, setComplete] = useState(false);
  const reviewed = useRef(0);
  const startTime = useRef(Date.now());

  // Sync cards when initialCards changes
  useEffect(() => {
    setCards(initialCards);
    setCurrentIndex(0);
    setFlipped(false);
    setGrading(false);
    setComplete(false);
    reviewed.current = 0;
  }, [initialCards]);

  const current = cards[currentIndex] || null;
  const waiting = !current && !complete && cards.length > 0;
  const total = cards.length;
  const progressPct = total > 0 ? Math.min((reviewed.current / total) * 100, 100) : 0;
  const intervals = (current?.intervals as FsrsIntervals | undefined) ?? null;

  const flip = useCallback(() => {
    setFlipped((f) => {
      if (!f) setGrading(true);
      return !f;
    });
  }, []);

  const next = useCallback(() => {
    if (currentIndex < cards.length - 1) {
      setCurrentIndex((i) => i + 1);
      setFlipped(false);
      setGrading(false);
    }
  }, [currentIndex, cards.length]);

  const prev = useCallback(() => {
    if (currentIndex > 0) {
      setCurrentIndex((i) => i - 1);
      setFlipped(false);
      setGrading(false);
    }
  }, [currentIndex]);

  const grade = useCallback(
    async (rating: "again" | "hard" | "good" | "easy") => {
      if (!current) return;

      let requeue = false;
      let requeueDelayMs = 0;
      let newIntervals = current.intervals;

      // Send to backend if gradeUrl is provided
      if (gradeUrl) {
        try {
          const resp = await fetch(gradeUrl, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ [idField]: current.id, rating }),
          });
          if (resp.ok) {
            const data = await resp.json();
            requeue = data.requeue ?? false;
            requeueDelayMs = data.requeue_delay_ms ?? 0;
            if (data.intervals) newIntervals = data.intervals;
          }
        } catch (e) {
          console.error("FSRS grade failed:", e);
        }
      }

      reviewed.current++;

      // Anki-style requeue: add card back to end of deck after delay
      if (requeue) {
        const requeuedCard = { ...current, intervals: newIntervals } as T;
        setTimeout(() => {
          setCards((prev) => [...prev, requeuedCard]);
        }, Math.max(requeueDelayMs, 500));
      }

      // Advance
      if (currentIndex < cards.length - 1) {
        setCurrentIndex((i) => i + 1);
        setFlipped(false);
        setGrading(false);
      } else if (requeue) {
        // Last card but will be requeued — advance past end, wait for card
        setCurrentIndex((i) => i + 1);
        setFlipped(false);
        setGrading(false);
      } else {
        // Complete
        setComplete(true);
        setFlipped(false);
        setGrading(false);
        onComplete?.(reviewed.current);
      }
    },
    [current, currentIndex, cards.length, gradeUrl, idField, onComplete]
  );

  const reset = useCallback(() => {
    setCurrentIndex(0);
    setFlipped(false);
    setGrading(false);
    setComplete(false);
    reviewed.current = 0;
    startTime.current = Date.now();
  }, []);

  // Auto-advance when requeued card arrives
  useEffect(() => {
    if (!complete && !waiting && current && currentIndex === cards.length - 1) {
      setFlipped(false);
    }
  }, [cards.length, complete, waiting, current, currentIndex]);

  // Keyboard shortcuts
  useEffect(() => {
    if (!enableKeyboard) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight") next();
      else if (e.key === "ArrowLeft") prev();
      else if (e.key === " " || e.key === "Enter") {
        e.preventDefault();
        flip();
      } else if (flipped && grading && ["1", "2", "3", "4"].includes(e.key)) {
        const ratings = ["again", "hard", "good", "easy"] as const;
        grade(ratings[parseInt(e.key) - 1]);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [enableKeyboard, next, prev, flip, flipped, grading, grade]);

  return {
    current,
    currentIndex,
    total,
    flipped,
    grading,
    complete,
    waiting,
    reviewedCount: reviewed.current,
    progressPct,
    intervals,
    flip,
    next,
    prev,
    grade,
    reset,
    cards,
  };
}
