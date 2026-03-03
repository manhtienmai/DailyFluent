"use client";

/**
 * QuizQuestion — Reusable full-screen question detail view.
 * Shows the question word, choices, explanation after answering.
 * Supports prev/next navigation and bookmarking.
 *
 * Refactored to use shadcn/ui components with rich micro-interactions.
 */

import { useState, useEffect } from "react";
import Link from "next/link";
import TextSelectionPopup from "@/components/TextSelectionPopup";
import { saveGrammar, removeGrammar, isGrammarSaved } from "@/lib/saved-grammar";
import { useStudyTimer } from "@/hooks/useStudyTimer";
import { cn } from "@/lib/utils";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Collapsible,
  CollapsibleTrigger,
  CollapsibleContent,
} from "@/components/ui/collapsible";

export interface QChoice { key: string; text: string; }
export interface QExplanation {
  option: number; is_correct: boolean; reason: string;
  suggested_word?: string; corrected_sentence?: string; corrected_translation?: string;
}
export interface QExplanationJson {
  word?: string; reading?: string; han_viet?: string; meaning_vi?: string;
  correct_translation?: string; explanations?: QExplanation[];
}
export interface QuizQuestionData {
  num: number; id: number; text: string; text_vi: string;
  choices: QChoice[]; correct_answer: string; explanation_json: QExplanationJson;
  level?: string; template_title?: string;
}

interface QuizQuestionProps {
  question: QuizQuestionData;
  totalQuestions: number;
  savedAnswer?: string;
  isRevealed?: boolean;
  isBookmarked?: boolean;
  onAnswer: (questionId: number, key: string) => void;
  onRetry?: (questionId: number, num: number) => void;
  onBookmark?: (num: number) => void;
  prevUrl?: string | null;
  nextUrl?: string | null;
  gridUrl: string;
  levelColor?: string;
  quizType?: "usage" | "bunpou";
}

const LEVEL_COLORS: Record<string, string> = {
  N1: "#dc2626", N2: "#7c3aed", N3: "#eab308", N4: "#3b82f6", N5: "#10b981",
};

export default function QuizQuestion({
  question: q, totalQuestions, savedAnswer, isRevealed: initRevealed = false,
  isBookmarked = false, onAnswer, onRetry, onBookmark, prevUrl, nextUrl, gridUrl, levelColor,
  quizType = "usage",
}: QuizQuestionProps) {
  const [revealed, setRevealed] = useState(initRevealed);
  const [userAns, setUserAns] = useState(savedAnswer || "");
  const [grammarSaved, setGrammarSaved] = useState(false);
  const [justAnswered, setJustAnswered] = useState(false);
  useStudyTimer();
  const [examplesOpen, setExamplesOpen] = useState(false);

  useEffect(() => {
    setRevealed(initRevealed);
    setUserAns(savedAnswer || "");
    setExamplesOpen(false);
    setJustAnswered(false);
  }, [q.id, initRevealed, savedAnswer]);

  const ej = q.explanation_json;
  const lc = levelColor || LEVEL_COLORS[q.level || ""] || "#6366f1";
  const isCorrect = userAns === q.correct_answer;

  useEffect(() => {
    if (quizType === "bunpou" && (ej as any).grammar_point) {
      setGrammarSaved(isGrammarSaved((ej as any).grammar_point));
    } else {
      setGrammarSaved(false);
    }
  }, [q.id, quizType, ej]);

  const handleToggleSaveGrammar = () => {
    const gp = (ej as any).grammar_point;
    if (!gp) return;
    if (grammarSaved) {
      removeGrammar(gp);
      setGrammarSaved(false);
    } else {
      saveGrammar({
        grammar_point: gp,
        grammar_structure: (ej as any).grammar_structure || "",
        grammar_meaning: (ej as any).grammar_meaning || "",
        grammar_note: (ej as any).grammar_note || "",
        grammar_furigana: (ej as any).grammar_furigana || "",
        level: q.level || "",
      });
      setGrammarSaved(true);
    }
  };

  const handleChoose = (key: string) => {
    if (revealed) return;
    setUserAns(key);
    setRevealed(true);
    setJustAnswered(true);
    onAnswer(q.id, key);

    if (quizType === "bunpou" && (ej as any).grammar_point && !grammarSaved) {
      saveGrammar({
        grammar_point: (ej as any).grammar_point,
        grammar_structure: (ej as any).grammar_structure || "",
        grammar_meaning: (ej as any).grammar_meaning || "",
        grammar_note: (ej as any).grammar_note || "",
        grammar_furigana: (ej as any).grammar_furigana || "",
        level: q.level || "",
      });
      setGrammarSaved(true);
    }
  };

  const renderWithRuby = (text: string, furigana: string) => {
    if (!furigana || !text) return <>{text}</>;
    const clean = text.replace(/～/g, '');
    if (!/[\u4e00-\u9fff\u3400-\u4dbf]/.test(clean)) return <>{text}</>;
    const parts: React.ReactNode[] = [];
    if (text.startsWith('～')) parts.push('～');
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
          const idx = furigana.indexOf(nextCh, fi);
          if (idx !== -1) fe = idx;
        }
        const reading = furigana.slice(fi, fe);
        parts.push(<ruby key={ti}>{kanjiStr}<rt>{reading}</rt></ruby>);
        ti = ke; fi = fe;
      }
    }
    if (ti < clean.length) parts.push(clean.slice(ti));
    return <>{parts}</>;
  };

  /** Parse inline furigana like お金（かね） → <ruby>お金<rt>かね</rt></ruby> */
  const renderInlineFurigana = (text: string) => {
    if (!text) return null;
    // Match: one-or-more kanji followed by （reading） or (reading)
    const regex = /([\u4e00-\u9fff\u3400-\u4dbf]+)[（(]([^）)]+)[）)]/g;
    const parts: React.ReactNode[] = [];
    let lastIdx = 0;
    let match;
    while ((match = regex.exec(text)) !== null) {
      if (match.index > lastIdx) {
        parts.push(text.slice(lastIdx, match.index));
      }
      parts.push(<ruby key={match.index}>{match[1]}<rt>{match[2]}</rt></ruby>);
      lastIdx = regex.lastIndex;
    }
    if (lastIdx < text.length) {
      parts.push(text.slice(lastIdx));
    }
    return <>{parts}</>;
  };

  const progressPercent = totalQuestions > 0 ? Math.round((q.num / totalQuestions) * 100) : 0;

  return (
    <>
      <div className="min-h-screen p-5 max-sm:p-3">
        <div className="mx-auto max-w-3xl animate-[fadeIn_0.35s_ease]">

          {/* ── Progress bar ── */}
          <div className="mb-4 animate-[fadeIn_0.3s_ease]">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[0.65rem] font-semibold text-[var(--text-tertiary)] tracking-wide uppercase">Tiến độ</span>
              <span className="text-[0.65rem] font-bold text-[var(--text-tertiary)]">{q.num} / {totalQuestions}</span>
            </div>
            <div className="h-[5px] w-full rounded-full bg-[var(--bg-app-subtle)] overflow-hidden border border-[var(--border-subtle,transparent)]">
              <div
                className="h-full rounded-full bg-gradient-to-r from-indigo-500 via-violet-500 to-fuchsia-500 transition-all duration-700 ease-out animate-[progressGrow_0.8s_ease-out]"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          </div>

          {/* ── Top nav ── */}
          <div className="mb-4 flex items-center gap-2.5">
            <Button variant="outline" size="sm" asChild
              className="rounded-full text-xs font-semibold text-[var(--text-tertiary)] border-[var(--border-default)] bg-[var(--bg-surface)] hover:text-indigo-500 hover:border-indigo-300 hover:bg-indigo-500/[0.04] hover:-translate-y-0.5 hover:shadow-[0_3px_10px_rgba(99,102,241,0.12)] active:translate-y-0 active:scale-[0.97] transition-all duration-200"
            >
              <Link href={gridUrl}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 3h7v7H3z"/><path d="M14 3h7v7h-7z"/><path d="M3 14h7v7H3z"/><path d="M14 14h7v7h-7z"/></svg>
                Danh sách
              </Link>
            </Button>
            <span className="ml-auto text-sm font-bold text-[var(--text-primary)]">Câu {q.num} / {totalQuestions}</span>
            {q.level && (
              <Badge variant="outline"
                className="text-[0.65rem] font-bold px-2.5 py-0.5 rounded-lg transition-all hover:scale-105"
                style={{ color: lc, borderColor: `${lc}40`, background: `${lc}10` }}
              >
                {q.level}
              </Badge>
            )}
          </div>

          {/* ── Question card — wrapped in TextSelectionPopup ── */}
          <TextSelectionPopup contextSentence={q.text}>
          <Card className={cn(
            "mb-3.5 border-[1.5px] border-[var(--border-default)] bg-[var(--bg-surface)] rounded-[18px] shadow-[0_1px_4px_rgba(0,0,0,0.03)] transition-all duration-300 animate-[slideUp_0.4s_ease] py-0",
            "hover:shadow-[0_6px_24px_rgba(0,0,0,0.06)] hover:border-[var(--border-strong)]",
            revealed && isCorrect && "border-emerald-400/40 shadow-[0_0_0_1px_rgba(16,185,129,0.1)]",
            revealed && !isCorrect && "border-red-300/40 shadow-[0_0_0_1px_rgba(239,68,68,0.08)]"
          )}>
            <CardContent className="p-5 max-sm:p-3.5">
              <div className="mb-3 flex items-center gap-3.5">
                <span
                  className={cn(
                    "flex h-[38px] w-[38px] shrink-0 cursor-pointer items-center justify-center rounded-full text-sm font-bold transition-all duration-200",
                    "border-2 border-transparent bg-[var(--bg-app-subtle)] text-[var(--text-tertiary)]",
                    "hover:bg-amber-400 hover:text-white hover:scale-110 hover:shadow-[0_3px_12px_rgba(251,191,36,0.35)] hover:rotate-[8deg]",
                    "active:scale-90 active:rotate-0",
                    isBookmarked && "bg-amber-500 text-white border-amber-500/30 shadow-[0_0_0_4px_rgba(245,158,11,0.15)] animate-[bounceIn_0.4s_ease]"
                  )}
                  onClick={() => onBookmark?.(q.num)}
                  title={isBookmarked ? "Bỏ đánh dấu" : "Đánh dấu"}
                >{q.num}</span>
                {quizType === "bunpou" ? (
                  <div className="flex-1 text-[1.05rem] font-medium leading-[1.7] text-[var(--text-primary)]" style={{ fontFamily: "var(--font-jp)" }}>
                    {revealed && (ej as any).sentence_completed
                      ? <>{(ej as any).sentence_completed.split(/[（(][^）)]*[）)]/).map((part: string, i: number, arr: string[]) => (
                          <span key={i}>
                            {part}
                            {i < arr.length - 1 && (
                              <mark className="rounded bg-emerald-500/[0.12] px-1 py-px font-bold text-emerald-600 no-underline dark:bg-emerald-500/[0.15] dark:text-emerald-400">
                                {q.choices.find(c => c.key === q.correct_answer)?.text || ''}
                              </mark>
                            )}
                          </span>
                        ))}</>
                      : q.text
                    }
                  </div>
                ) : (
                  <h2 className="m-0 text-[1.6rem] font-medium leading-[1.3] text-[var(--text-primary)]" style={{ fontFamily: "var(--font-jp)" }}>{q.text}</h2>
                )}
              </div>

              {/* Sentence translation — bunpou only, after reveal */}
              {revealed && quizType === "bunpou" && (ej as any).correct_translation && (
                <div className="-mt-0.5 mb-3 rounded-[10px] border-l-[3px] border-emerald-500/30 bg-emerald-500/[0.04] px-3.5 py-2.5 text-sm leading-[1.7] text-[var(--text-secondary)] animate-[revealIn_0.3s_ease] dark:bg-emerald-500/[0.06] dark:border-emerald-500/25">
                  {(ej as any).correct_translation}
                </div>
              )}

              {/* Details — only after reveal (usage) */}
              {revealed && quizType === "usage" && (
                <div className="mb-3 flex flex-wrap items-baseline gap-2.5 rounded-xl border border-[var(--border-subtle,transparent)] bg-[var(--bg-app-subtle)] px-3.5 py-2.5 animate-[revealIn_0.35s_ease]">
                  {ej.reading && <span className="text-base text-[var(--text-secondary)]" style={{ fontFamily: "var(--font-jp)" }}>{ej.reading}</span>}
                  {ej.han_viet && <span className="text-sm font-semibold" style={{ color: lc }}>【{ej.han_viet}】</span>}
                  {ej.meaning_vi && <div className="mt-1 w-full text-[0.92rem] leading-[1.6] text-[var(--text-secondary)]">► {ej.meaning_vi}</div>}
                </div>
              )}
              {/* Details — only after reveal (bunpou) */}
              {revealed && quizType === "bunpou" && (
                <div className="mb-3 flex flex-wrap items-baseline gap-2.5 rounded-xl border border-[var(--border-subtle,transparent)] bg-[var(--bg-app-subtle)] px-3.5 py-2.5 animate-[revealIn_0.35s_ease]">
                  <div className="mb-1 flex w-full flex-wrap items-baseline gap-3">
                    {(ej as any).grammar_point && (
                      <span className="text-lg font-bold" style={{ color: lc, fontFamily: "var(--font-jp)" }}>
                        {(ej as any).grammar_furigana
                          ? renderWithRuby((ej as any).grammar_point, (ej as any).grammar_furigana)
                          : (ej as any).grammar_point
                        }
                      </span>
                    )}
                    {(ej as any).grammar_structure && (
                      <span className="inline-block whitespace-pre-line rounded-lg border border-indigo-500/15 bg-indigo-500/[0.06] px-3 py-1.5 transition-all hover:bg-indigo-500/10">
                        <span className="text-[0.92rem] font-semibold leading-relaxed text-indigo-500" style={{ fontFamily: "var(--font-jp)" }}>{(ej as any).grammar_structure}</span>
                      </span>
                    )}
                  </div>
                  {(ej as any).grammar_meaning && <div className="mt-1 w-full text-[0.92rem] leading-[1.6] text-[var(--text-secondary)]">► {(ej as any).grammar_meaning}</div>}
                  {(ej as any).grammar_note && <div className="mt-1 w-full text-xs leading-[1.7] text-[var(--text-secondary)]">📌 {(ej as any).grammar_note}</div>}

                  {/* Collapsible Examples */}
                  {Array.isArray((ej as any).examples) && (ej as any).examples.length > 0 && (
                    <Collapsible open={examplesOpen} onOpenChange={setExamplesOpen} className="mt-2.5 w-full">
                      <CollapsibleTrigger asChild>
                        <Button variant="outline" size="sm"
                          className={cn(
                            "w-full justify-between rounded-[10px] border-[1.5px] text-xs font-semibold text-[var(--text-secondary)]",
                            "hover:bg-indigo-500/[0.04] hover:border-indigo-500/20 hover:text-indigo-500",
                            examplesOpen && "border-indigo-500/25 text-indigo-500 rounded-b-none"
                          )}
                          onClick={(e) => e.stopPropagation()}
                        >
                          <span>📝 Câu ví dụ ({(ej as any).examples.length})</span>
                          <span className={cn("text-[0.6rem] transition-transform duration-200", examplesOpen && "rotate-180")}>{examplesOpen ? "▲" : "▼"}</span>
                        </Button>
                      </CollapsibleTrigger>
                      <CollapsibleContent>
                        <div className="overflow-hidden rounded-b-[10px] border border-t-0 border-indigo-500/[0.12] animate-[revealIn_0.25s_ease]">
                          {(ej as any).examples.map((ex: any, i: number) => (
                            <div key={i} className={cn(
                              "bg-indigo-500/[0.02] px-3.5 py-2.5 transition-all duration-200 hover:bg-indigo-500/[0.05] hover:pl-4",
                              i > 0 && "border-t border-indigo-500/[0.06]"
                            )}>
                              <div className="text-sm leading-[1.7] text-[var(--text-primary)]" style={{ fontFamily: "var(--font-jp)" }}>{renderInlineFurigana(ex.ja)}</div>
                              <div className="mt-0.5 text-xs italic leading-[1.5] text-[var(--text-secondary)]">{ex.vi}</div>
                            </div>
                          ))}
                        </div>
                      </CollapsibleContent>
                    </Collapsible>
                  )}
                  {(ej as any).grammar_point && (
                    <Button
                      variant="outline"
                      size="sm"
                      className={cn(
                        "mt-2.5 rounded-full border-[1.5px] text-[0.7rem] font-bold transition-all duration-200",
                        grammarSaved
                          ? "border-emerald-500/30 bg-emerald-500/[0.06] text-emerald-500 hover:bg-red-500/[0.06] hover:border-red-500/25 hover:text-red-500 hover:scale-[1.03]"
                          : "border-indigo-500/25 bg-indigo-500/[0.05] text-indigo-500 hover:bg-indigo-500/10 hover:border-indigo-500 hover:scale-[1.03] hover:shadow-[0_2px_8px_rgba(99,102,241,0.15)]"
                      )}
                      onClick={(e) => { e.stopPropagation(); handleToggleSaveGrammar(); }}
                    >
                      {grammarSaved ? "✓ Đã lưu" : "📌 Lưu ngữ pháp"}
                    </Button>
                  )}
                </div>
              )}

              {/* ── Result badge after answering ── */}
              {revealed && (
                <div className={cn(
                  "mb-3 flex items-center justify-center gap-2 rounded-xl py-2.5 px-4 text-sm font-bold animate-[resultBadgeIn_0.5s_ease]",
                  isCorrect
                    ? "bg-emerald-500/[0.08] text-emerald-600 dark:text-emerald-400"
                    : "bg-red-500/[0.06] text-red-600 dark:text-red-400"
                )}>
                  <span className="text-lg animate-[bounceIn_0.5s_ease]">{isCorrect ? "🎉" : "💡"}</span>
                  <span>{isCorrect ? "Chính xác!" : "Chưa đúng"}</span>
                  {!isCorrect && onRetry && (
                    <button
                      className="ml-2 rounded-full border border-red-300/40 bg-red-500/[0.06] px-3 py-1 text-xs font-bold text-red-500 transition-all duration-200 hover:bg-red-500/[0.12] hover:border-red-400 hover:scale-105 hover:-translate-y-0.5 active:scale-95"
                      onClick={(e) => {
                        e.stopPropagation();
                        setRevealed(false);
                        setUserAns("");
                        setJustAnswered(false);
                        onRetry(q.id, q.num);
                      }}
                    >
                      🔄 Làm lại
                    </button>
                  )}
                </div>
              )}

              {/* ── Choices ── */}
              <div className="flex flex-col gap-1.5">
                {q.choices.map((c, idx) => {
                  const isThis = userAns === c.key;
                  const isCorrectChoice = c.key === q.correct_answer;
                  return (
                    <button
                      key={c.key}
                      className={cn(
                        "group relative flex w-full items-center gap-2.5 rounded-[12px] border-[1.5px] border-l-[3px] border-l-transparent px-3.5 py-2 text-left transition-all duration-200",
                        "border-[var(--border-default)] bg-[var(--bg-surface)] cursor-pointer",
                        !revealed && "opacity-0 animate-[choiceSlideIn_0.35s_ease_forwards]",
                        // Hover state (only when not revealed)
                        !revealed && !isThis && "hover:border-indigo-300 hover:border-l-indigo-500 hover:bg-indigo-500/[0.03] hover:translate-x-1.5 hover:shadow-[0_3px_12px_rgba(99,102,241,0.1)]",
                        !revealed && !isThis && "active:translate-x-0.5 active:scale-[0.98]",
                        // Selected (before reveal)
                        !revealed && isThis && "border-indigo-400 border-l-indigo-500 bg-indigo-500/[0.04]",
                        // Correct — force opacity-100 since entry animation is no longer applied
                        revealed && isCorrectChoice && "!opacity-100 !border-emerald-400 !border-l-emerald-500 !bg-emerald-500/[0.05] animate-[successGlow_0.8s_ease]",
                        // Wrong
                        revealed && isThis && !isCorrectChoice && "!opacity-100 !border-red-300 !border-l-red-500 !bg-red-500/[0.04] animate-[shake_0.4s_ease]",
                        // Dimmed non-relevant after reveal
                        revealed && !isThis && !isCorrectChoice && "!opacity-50",
                        // Disabled
                        revealed && "cursor-default select-text"
                      )}
                      style={{ animationDelay: revealed ? '0ms' : `${idx * 60}ms` }}
                      onClick={() => !revealed && handleChoose(c.key)}
                    >
                      {/* Choice key circle */}
                      <span className={cn(
                        "flex h-[26px] w-[26px] shrink-0 items-center justify-center rounded-md text-[0.7rem] font-bold transition-all duration-200",
                        "border border-[var(--border-subtle,transparent)] bg-[var(--bg-app-subtle)] text-[var(--text-tertiary)]",
                        !revealed && !isThis && "group-hover:bg-indigo-500 group-hover:text-white group-hover:border-transparent group-hover:shadow-[0_2px_8px_rgba(99,102,241,0.3)] group-hover:scale-110",
                        !revealed && isThis && "bg-indigo-500 text-white",
                        revealed && isCorrectChoice && "!bg-emerald-500 !text-white !border-transparent !shadow-[0_2px_8px_rgba(16,185,129,0.3)]",
                        revealed && isThis && !isCorrectChoice && "!bg-red-500 !text-white !border-transparent"
                      )}>{c.key}</span>
                      {/* Choice text */}
                      <span className="flex-1 text-base leading-[1.5] text-[var(--text-primary)] select-text" style={{ fontFamily: "var(--font-jp)" }}>
                        {c.text}
                        {revealed && isCorrectChoice && quizType === "usage" && ej.correct_translation && (
                          <div className="mt-1 text-[0.78rem] font-medium leading-[1.4] text-emerald-500" style={{ fontFamily: "var(--font-sans)" }}>{ej.correct_translation}</div>
                        )}
                      </span>
                      {/* Result icon with bounce */}
                      {revealed && isCorrectChoice && (
                        <span className="shrink-0 text-lg font-bold text-emerald-500 animate-[bounceIn_0.5s_ease]">✓</span>
                      )}
                      {revealed && isThis && !isCorrectChoice && (
                        <span className="shrink-0 text-lg font-bold text-red-500 animate-[bounceIn_0.4s_ease]">✗</span>
                      )}
                      {/* Hover shimmer effect (only before reveal) */}
                      {!revealed && (
                        <div className="absolute inset-0 rounded-[14px] overflow-hidden pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-indigo-500/[0.03] to-transparent animate-[shimmer_2s_infinite] bg-[length:200%_100%]" />
                        </div>
                      )}
                    </button>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* Explanation */}
          {revealed && ej.explanations && ej.explanations.length > 0 && (
            <Card className={cn(
              "mb-3.5 rounded-2xl border-[1.5px] bg-[var(--bg-surface)] animate-[revealIn_0.4s_ease] py-0",
              isCorrect
                ? "border-emerald-500/20 border-l-[4px] border-l-emerald-500"
                : "border-red-500/20 border-l-[4px] border-l-red-500"
            )} style={{ fontFamily: "var(--font-jp)" }}>
              <CardContent className="p-4">
                {ej.explanations.map((ex, i) => (
                  <div key={ex.option} className="mb-2.5 text-[0.92rem] leading-[1.7] text-[var(--text-secondary)] last:mb-0"
                    style={{ animationDelay: `${i * 80}ms` }}
                  >
                    <strong className={ex.is_correct ? "text-emerald-500" : "text-red-500"}>Câu {ex.option}:</strong> {ex.reason}
                    {ex.suggested_word && (
                      <div className="mt-1 pl-3.5 text-sm text-indigo-500">
                        → Nên dùng: <strong className="font-semibold">{ex.suggested_word}</strong>
                        {ex.corrected_sentence && (
                          <div className="mt-1 text-sm text-[var(--text-tertiary)]">
                            {ex.corrected_sentence}
                            {ex.corrected_translation && <span> — {ex.corrected_translation}</span>}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </CardContent>
            </Card>
          )}
          </TextSelectionPopup>

          {/* ── Bottom nav ── */}
          <div className="mt-3.5 flex items-center justify-between animate-[fadeIn_0.5s_ease]">
            {prevUrl ? (
              <Button variant="outline" asChild
                className="group/nav rounded-3xl border-[1.5px] border-[var(--border-default)] bg-[var(--bg-surface)] text-xs font-semibold text-[var(--text-secondary)] hover:border-indigo-300 hover:text-indigo-500 hover:bg-indigo-500/[0.04] hover:-translate-y-0.5 hover:shadow-[0_4px_14px_rgba(99,102,241,0.1)] active:translate-y-0 active:scale-[0.97] transition-all duration-200"
              >
                <Link href={prevUrl}>
                  <svg className="transition-transform duration-200 group-hover/nav:-translate-x-0.5" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M15 18l-6-6 6-6"/></svg>
                  Câu trước
                </Link>
              </Button>
            ) : <span />}
            {nextUrl ? (
              <Button asChild
                className="group/nav rounded-3xl bg-gradient-to-br from-indigo-500 to-violet-500 text-white text-xs font-semibold shadow-[0_3px_12px_rgba(99,102,241,0.3)] hover:shadow-[0_6px_24px_rgba(99,102,241,0.4)] hover:-translate-y-1 active:translate-y-0 active:scale-[0.97] transition-all duration-200"
              >
                <Link href={nextUrl}>
                  Câu tiếp
                  <svg className="transition-transform duration-200 group-hover/nav:translate-x-0.5" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M9 18l6-6-6-6"/></svg>
                </Link>
              </Button>
            ) : (
              <Button asChild
                className="group/nav rounded-3xl bg-gradient-to-br from-indigo-500 to-violet-500 text-white text-xs font-semibold shadow-[0_3px_12px_rgba(99,102,241,0.3)] hover:shadow-[0_6px_24px_rgba(99,102,241,0.4)] hover:-translate-y-1 active:translate-y-0 active:scale-[0.97] transition-all duration-200"
              >
                <Link href={gridUrl}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 3h7v7H3z"/><path d="M14 3h7v7h-7z"/><path d="M3 14h7v7H3z"/><path d="M14 14h7v7h-7z"/></svg>
                  Xem tổng kết
                </Link>
              </Button>
            )}
          </div>

          {/* ── Keyboard hint ── */}
          <div className="mt-4 flex items-center justify-center gap-3 text-[0.6rem] text-[var(--text-tertiary)] animate-[fadeIn_0.8s_ease]">
            <span className="flex items-center gap-1">
              <kbd className="inline-flex h-5 min-w-5 items-center justify-center rounded border border-[var(--border-default)] bg-[var(--bg-app-subtle)] px-1.5 text-[0.55rem] font-mono">←</kbd>
              <kbd className="inline-flex h-5 min-w-5 items-center justify-center rounded border border-[var(--border-default)] bg-[var(--bg-app-subtle)] px-1.5 text-[0.55rem] font-mono">→</kbd>
              <span className="ml-0.5">chuyển câu</span>
            </span>
          </div>
        </div>
      </div>
    </>
  );
}
