"use client";

/**
 * QuizGrid — Premium grid of numbered cells for any quiz type.
 * Modern design with rounded cards, status colors, micro-interactions.
 *
 * Refactored to use shadcn/ui + Tailwind utilities.
 */

import Link from "next/link";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";

export interface GridQuestion {
  num: number;
  id: number;
  status: "unanswered" | "answered" | "correct" | "wrong";
  bookmarked?: boolean;
}

interface QuizGridProps {
  questions: GridQuestion[];
  baseUrl: string;
  activeNum?: number;
}

const statusStyles: Record<string, string> = {
  unanswered: "border-[1.5px] border-[var(--border-default)] bg-[var(--bg-surface)] text-[var(--text-tertiary)] hover:border-indigo-300 hover:text-indigo-500 hover:shadow-[0_2px_8px_rgba(99,102,241,0.1)]",
  answered: "border-[1.5px] border-indigo-400 bg-gradient-to-br from-indigo-500/[0.06] to-violet-500/[0.06] text-indigo-500 shadow-[0_1px_4px_rgba(99,102,241,0.1)] hover:shadow-[0_3px_12px_rgba(99,102,241,0.2)] hover:border-indigo-500",
  correct: "border-[1.5px] border-emerald-400 bg-gradient-to-br from-emerald-500/[0.06] to-emerald-400/[0.08] text-emerald-600 shadow-[0_1px_4px_rgba(16,185,129,0.1)] hover:shadow-[0_3px_12px_rgba(16,185,129,0.2)] hover:border-emerald-500 dark:text-emerald-400",
  wrong: "border-[1.5px] border-red-300 bg-gradient-to-br from-red-500/[0.04] to-red-300/[0.06] text-red-600 shadow-[0_1px_4px_rgba(239,68,68,0.08)] hover:shadow-[0_3px_12px_rgba(239,68,68,0.15)] hover:border-red-500 dark:text-red-400",
  bookmarked: "border-[1.5px] border-amber-400 bg-gradient-to-br from-amber-500/[0.05] to-amber-400/[0.08] text-amber-700 shadow-[0_1px_4px_rgba(245,158,11,0.1)] hover:shadow-[0_3px_12px_rgba(245,158,11,0.2)] hover:border-amber-500 dark:text-amber-400",
};

export default function QuizGrid({ questions, baseUrl, activeNum }: QuizGridProps) {
  return (
    <div>
      <div className="flex flex-wrap gap-[5px]">
        {questions.map((q, idx) => {
          const isActive = q.num === activeNum;
          const statusKey = q.bookmarked ? "bookmarked" : q.status;
          return (
            <Link
              key={q.num}
              href={`${baseUrl}/${q.num}`}
              className={cn(
                "relative flex h-7 w-7 items-center justify-center rounded-lg text-[0.6rem] font-bold no-underline",
                "transition-all hover:scale-[1.15] hover:z-[2] active:scale-95",
                "opacity-0 animate-[cellIn_0.25s_ease_forwards]",
                statusStyles[statusKey],
                isActive && "!scale-[1.12] !border-indigo-500 !text-indigo-500 shadow-[0_0_0_2.5px_rgba(99,102,241,0.3),0_3px_10px_rgba(99,102,241,0.15)]",
                "max-sm:h-6 max-sm:w-6 max-sm:rounded-md max-sm:text-[0.55rem]"
              )}
              style={{ animationDelay: `${Math.min(idx * 12, 400)}ms` }}
            >
              {q.num}
              {q.bookmarked && (
                <span className="absolute right-0.5 top-0.5 h-[5px] w-[5px] rounded-full bg-amber-500 shadow-[0_0_4px_rgba(245,158,11,0.4)]" />
              )}
            </Link>
          );
        })}
      </div>

      {/* Legend */}
      <div className="mt-4 flex flex-wrap justify-center gap-3.5 max-sm:gap-2.5 max-sm:mt-3">
        {[
          { label: "Chưa làm", dotCls: "border-[1.5px] border-[var(--border-default)] bg-[var(--bg-surface)]" },
          { label: "Đã chọn", dotCls: "border-[1.5px] border-indigo-400 bg-indigo-500/[0.08]" },
          { label: "Đúng", dotCls: "border-[1.5px] border-emerald-400 bg-emerald-500/[0.08]" },
          { label: "Sai", dotCls: "border-[1.5px] border-red-300 bg-red-500/[0.08]" },
          { label: "Đánh dấu", dotCls: "border-[1.5px] border-amber-400 bg-amber-500/[0.08]" },
        ].map((l) => (
          <span key={l.label} className="flex items-center gap-1.5 text-[0.65rem] font-medium text-[var(--text-tertiary)] max-sm:text-[0.6rem] max-sm:gap-1">
            <span className={cn("h-2.5 w-2.5 rounded max-sm:h-2 max-sm:w-2 max-sm:rounded-sm", l.dotCls)} />
            {l.label}
          </span>
        ))}
      </div>
    </div>
  );
}
