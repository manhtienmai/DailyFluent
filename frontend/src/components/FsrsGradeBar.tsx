"use client";

/**
 * FsrsGradeBar — Reusable FSRS grading bar component.
 *
 * 4 buttons: Again / Hard / Good / Easy
 * Shows interval preview on each button.
 * Keyboard shortcuts 1-4.
 * Slide-up animation.
 */

import { useCallback } from "react";
import s from "./FsrsGradeBar.module.css";

export interface FsrsIntervals {
  again: string;
  hard: string;
  good: string;
  easy: string;
}

interface FsrsGradeBarProps {
  /** Callback when user selects a rating */
  onGrade: (rating: "again" | "hard" | "good" | "easy") => void;
  /** Interval preview for each rating (optional) */
  intervals?: FsrsIntervals | null;
  /** Whether the bar is visible */
  visible?: boolean;
}

const RATINGS = [
  { key: "again" as const, label: "Quên", emoji: "😵", color: "#ef4444", shortcut: "1" },
  { key: "hard" as const, label: "Khó", emoji: "😓", color: "#f59e0b", shortcut: "2" },
  { key: "good" as const, label: "Nhớ", emoji: "😊", color: "#10b981", shortcut: "3" },
  { key: "easy" as const, label: "Dễ", emoji: "🤩", color: "#3b82f6", shortcut: "4" },
];

export default function FsrsGradeBar({ onGrade, intervals, visible = true }: FsrsGradeBarProps) {
  const handleClick = useCallback(
    (rating: "again" | "hard" | "good" | "easy") => (e: React.MouseEvent) => {
      e.stopPropagation();
      onGrade(rating);
    },
    [onGrade]
  );

  if (!visible) return null;

  return (
    <div className={s.gradeBar}>
      <div className={s.buttons}>
        {RATINGS.map((r) => (
          <button
            key={r.key}
            className={s.btn}
            style={{
              borderColor: `${r.color}30`,
              background: `${r.color}08`,
            }}
            onClick={handleClick(r.key)}
          >
            <span className={s.emoji}>{r.emoji}</span>
            <span className={s.text} style={{ color: r.color }}>
              {r.label}
            </span>
            {intervals && (
              <span className={s.interval} style={{ color: r.color }}>
                {intervals[r.key]}
              </span>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}
