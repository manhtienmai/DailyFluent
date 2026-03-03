"use client";

/**
 * Grammar Patterns Browse Page
 * Shows all unique grammar patterns extracted from bunpou quiz questions.
 * Card front: only grammar_point. Click to expand.
 * Auto-highlights patterns that user has learned (from quiz).
 * Users can dismiss/undismiss patterns they don't want to study.
 */

import { useState, useEffect, useMemo, useCallback } from "react";
import Link from "next/link";
import {
  isGrammarSaved,
  isDismissed as isDismissedGrammar,
  dismissGrammar,
  undismissGrammar,
  getDismissedSet,
} from "@/lib/saved-grammar";

interface GrammarExample { ja: string; vi: string }

interface GrammarPattern {
  grammar_point: string;
  grammar_furigana: string;
  grammar_structure: string;
  grammar_meaning: string;
  grammar_note: string;
  grammar_topic: string;
  grammar_reading: string;
  examples: GrammarExample[];
  level: string;
  question_count: number;
  question_ids: number[];
}

const LC: Record<string, { pill: string; badge: string; accent: string; ring: string }> = {
  N1: { pill: "bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/20", badge: "bg-red-500", accent: "border-l-red-500", ring: "ring-red-500/30" },
  N2: { pill: "bg-violet-500/10 text-violet-600 dark:text-violet-400 border-violet-500/20", badge: "bg-violet-500", accent: "border-l-violet-500", ring: "ring-violet-500/30" },
  N3: { pill: "bg-yellow-500/10 text-yellow-600 dark:text-yellow-400 border-yellow-500/20", badge: "bg-yellow-500", accent: "border-l-yellow-500", ring: "ring-yellow-500/30" },
  N4: { pill: "bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20", badge: "bg-blue-500", accent: "border-l-blue-500", ring: "ring-blue-500/30" },
  N5: { pill: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20", badge: "bg-emerald-500", accent: "border-l-emerald-500", ring: "ring-emerald-500/30" },
};

const LEVELS = ["N5", "N4", "N3", "N2", "N1"];

type ViewMode = "all" | "learned" | "dismissed";

export default function GrammarPatternsPage() {
  const [patterns, setPatterns] = useState<GrammarPattern[]>([]);
  const [levelStats, setLevelStats] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);
  const [filterLevel, setFilterLevel] = useState("");
  const [search, setSearch] = useState("");
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>("all");

  // Track saved & dismissed states (re-render on change)
  const [savedSet, setSavedSet] = useState<Set<string>>(new Set());
  const [dismissedSet, setDismissedSet] = useState<Set<string>>(new Set());

  // Refresh saved/dismissed from localStorage
  const refreshLocalState = useCallback(() => {
    const saved = new Set<string>();
    try {
      const raw = localStorage.getItem("saved_grammar_list");
      if (raw) {
        const list = JSON.parse(raw) as { grammar_point: string }[];
        list.forEach((g) => saved.add(g.grammar_point));
      }
    } catch { /* ignore */ }
    setSavedSet(saved);
    setDismissedSet(getDismissedSet());
  }, []);

  useEffect(() => {
    refreshLocalState();
  }, [refreshLocalState]);

  useEffect(() => {
    setLoading(true);
    const url = filterLevel
      ? `/api/v1/exam/bunpou/grammar-patterns?level=${filterLevel}`
      : "/api/v1/exam/bunpou/grammar-patterns";
    fetch(url, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d) => {
        setPatterns(d.patterns || []);
        setLevelStats(d.level_stats || {});
        setLoading(false);
      })
      .catch(() => { setPatterns([]); setLoading(false); });
  }, [filterLevel]);

  const filtered = useMemo(() => {
    let list = patterns;

    // View mode filter
    if (viewMode === "learned") {
      list = list.filter((p) => savedSet.has(p.grammar_point) && !dismissedSet.has(p.grammar_point));
    } else if (viewMode === "dismissed") {
      list = list.filter((p) => dismissedSet.has(p.grammar_point));
    }

    if (!search.trim()) return list;
    const q = search.toLowerCase();
    return list.filter(
      (p) =>
        p.grammar_point.toLowerCase().includes(q) ||
        p.grammar_meaning.toLowerCase().includes(q) ||
        p.grammar_structure.toLowerCase().includes(q) ||
        p.grammar_topic.toLowerCase().includes(q) ||
        p.grammar_furigana.toLowerCase().includes(q)
    );
  }, [patterns, search, viewMode, savedSet, dismissedSet]);

  const totalAll = Object.values(levelStats).reduce((a, b) => a + b, 0);
  const learnedCount = patterns.filter((p) => savedSet.has(p.grammar_point) && !dismissedSet.has(p.grammar_point)).length;
  const dismissedCount = patterns.filter((p) => dismissedSet.has(p.grammar_point)).length;

  const handleDismiss = (gp: string) => {
    dismissGrammar(gp);
    refreshLocalState();
  };

  const handleUndismiss = (gp: string) => {
    undismissGrammar(gp);
    refreshLocalState();
  };

  return (
    <div className="min-h-screen px-4 py-6 sm:px-6">
      <div className="max-w-3xl mx-auto">

        {/* ── Header ── */}
        <div className="flex items-start justify-between mb-5 gap-4 flex-wrap">
          <div>
            <h1 className="text-xl sm:text-2xl font-extrabold text-gray-900 dark:text-white tracking-tight">
              📘 Bảng Ngữ pháp
            </h1>
            <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 mt-1">
              {totalAll} cấu trúc · <span className="text-emerald-500 font-bold">{learnedCount} đã học</span>
              {dismissedCount > 0 && <> · <span className="text-gray-400">{dismissedCount} ẩn</span></>}
            </p>
          </div>
          <Link
            href="/exam/bunpou"
            className="shrink-0 inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold text-white bg-gradient-to-br from-indigo-500 to-violet-600 shadow-md shadow-indigo-500/25 hover:shadow-lg hover:-translate-y-0.5 transition-all"
          >
            📝 Làm quiz
          </Link>
        </div>

        {/* ── View Mode Tabs ── */}
        <div className="flex gap-1.5 mb-4 p-1 rounded-xl bg-gray-100 dark:bg-gray-800 w-fit">
          {([
            { key: "all" as ViewMode, label: "Tất cả", count: totalAll },
            { key: "learned" as ViewMode, label: "Đã học", count: learnedCount },
            { key: "dismissed" as ViewMode, label: "Đã ẩn", count: dismissedCount },
          ]).map((tab) => (
            <button
              key={tab.key}
              onClick={() => setViewMode(tab.key)}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                viewMode === tab.key
                  ? "bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm"
                  : "text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
              }`}
            >
              {tab.label} <span className="opacity-50">({tab.count})</span>
            </button>
          ))}
        </div>

        {/* ── Level pills ── */}
        <div className="flex flex-wrap gap-2 mb-4">
          <button
            onClick={() => setFilterLevel("")}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-bold border transition-all ${
              filterLevel === ""
                ? "bg-gray-900 dark:bg-white text-white dark:text-gray-900 border-transparent shadow-sm"
                : "bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-750"
            }`}
          >
            Tất cả
          </button>
          {LEVELS.map((lv) => {
            const count = levelStats[lv] || 0;
            const active = filterLevel === lv;
            const c = LC[lv];
            return (
              <button
                key={lv}
                onClick={() => setFilterLevel(active ? "" : lv)}
                disabled={count === 0}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-bold border transition-all disabled:opacity-30 disabled:cursor-not-allowed ${
                  active
                    ? `${c.pill} border ring-2 ${c.ring}`
                    : `${c.pill} border hover:ring-1 ${c.ring}`
                }`}
              >
                {lv} <span className="opacity-60">({count})</span>
              </button>
            );
          })}
        </div>

        {/* ── Search ── */}
        <div className="relative mb-5">
          <div className="absolute inset-y-0 left-3.5 flex items-center pointer-events-none text-gray-400 dark:text-gray-500">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-4.35-4.35m0 0A7.5 7.5 0 1010.5 18a7.5 7.5 0 006.15-3.35z" />
            </svg>
          </div>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Tìm ngữ pháp (VD: ～ために, 使役...)"
            className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm placeholder-gray-400 dark:placeholder-gray-500 outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-400 transition-all"
            style={{ fontFamily: "'Noto Sans JP', sans-serif" }}
          />
        </div>

        {/* ── Count ── */}
        {!loading && (
          <div className="text-[11px] text-gray-400 dark:text-gray-500 font-semibold mb-3 tracking-wide uppercase">
            {filtered.length} cấu trúc {search && `khớp "${search}"`}
          </div>
        )}

        {/* ── Content ── */}
        {loading ? (
          <div className="text-center py-20 text-gray-400 dark:text-gray-500">
            <div className="text-4xl mb-3 animate-pulse">📚</div>
            <div className="text-sm">Đang tải...</div>
          </div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-20 text-gray-400 dark:text-gray-500">
            <div className="text-4xl mb-3">📭</div>
            <div className="text-sm">
              {viewMode === "learned" ? "Chưa học mẫu ngữ pháp nào. Hãy làm quiz bunpou!" :
               viewMode === "dismissed" ? "Chưa ẩn mẫu nào" :
               search ? "Không tìm thấy" : "Chưa có dữ liệu"}
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-2">
            {filtered.map((p) => {
              const c = LC[p.level] || LC.N3;
              const isOpen = expandedId === p.grammar_point;
              const isSaved = savedSet.has(p.grammar_point);
              const isDismissedItem = dismissedSet.has(p.grammar_point);
              return (
                <div
                  key={p.grammar_point}
                  className={`rounded-2xl border transition-all duration-200 ${
                    isDismissedItem
                      ? "opacity-50 bg-gray-50 dark:bg-gray-800/30 border-gray-200 dark:border-gray-700/40"
                      : isOpen
                        ? "bg-white dark:bg-gray-800/80 border-gray-300 dark:border-gray-600 shadow-lg shadow-gray-200/50 dark:shadow-black/20"
                        : "bg-white dark:bg-gray-800/50 border-gray-100 dark:border-gray-700/60 hover:border-gray-200 dark:hover:border-gray-600 hover:shadow-md hover:shadow-gray-100/50 dark:hover:shadow-black/10"
                  }`}
                >
                  {/* ── Card Front ── */}
                  <div className="flex items-center gap-3 px-4 py-3.5">
                    {/* Clickable area: grammar point */}
                    <button
                      onClick={() => setExpandedId(isOpen ? null : p.grammar_point)}
                      className="flex-1 flex items-center gap-3 text-left min-w-0"
                    >
                      {/* Level dot + learned indicator */}
                      <span className="relative shrink-0">
                        <span className={`block w-2.5 h-2.5 rounded-full ${c.badge}`} />
                        {isSaved && !isDismissedItem && (
                          <span className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-emerald-400 ring-2 ring-white dark:ring-gray-800" />
                        )}
                      </span>

                      {/* Grammar point name */}
                      <span
                        className={`text-[15px] sm:text-base font-bold truncate ${isDismissedItem ? "text-gray-400 dark:text-gray-500 line-through" : "text-gray-900 dark:text-white"}`}
                        style={{ fontFamily: "'Noto Sans JP', sans-serif" }}
                      >
                        {p.grammar_point}
                      </span>

                      {/* Level tag */}
                      <span className={`shrink-0 text-[10px] font-extrabold px-2 py-0.5 rounded-md border ${c.pill}`}>
                        {p.level}
                      </span>

                      {/* Arrow */}
                      <svg
                        className={`w-4 h-4 shrink-0 text-gray-300 dark:text-gray-600 transition-transform duration-200 ${isOpen ? "rotate-180" : ""}`}
                        fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                      </svg>
                    </button>

                    {/* Dismiss / Undismiss button */}
                    {isDismissedItem ? (
                      <button
                        onClick={(e) => { e.stopPropagation(); handleUndismiss(p.grammar_point); }}
                        className="shrink-0 px-2.5 py-1 rounded-lg text-[10px] font-bold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 hover:bg-emerald-500/20 transition-all"
                        title="Khôi phục"
                      >
                        ↩ Học lại
                      </button>
                    ) : (
                      <button
                        onClick={(e) => { e.stopPropagation(); handleDismiss(p.grammar_point); }}
                        className="shrink-0 p-1.5 rounded-lg text-gray-300 dark:text-gray-600 hover:text-red-400 hover:bg-red-500/10 transition-all"
                        title="Ẩn mẫu này"
                      >
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    )}
                  </div>

                  {/* ── Expanded Detail ── */}
                  {isOpen && (
                    <div className="px-4 pb-4 pt-1 border-t border-gray-100 dark:border-gray-700/60 space-y-3">
                      {/* Meaning */}
                      <div className="flex items-start gap-2">
                        <span className="shrink-0 text-[10px] font-bold text-gray-400 dark:text-gray-500 uppercase tracking-wider mt-0.5 w-12">Nghĩa</span>
                        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed font-medium">
                          {p.grammar_meaning || "—"}
                        </p>
                      </div>

                      {/* Structure */}
                      {p.grammar_structure && (
                        <div className="flex items-start gap-2">
                          <span className="shrink-0 text-[10px] font-bold text-gray-400 dark:text-gray-500 uppercase tracking-wider mt-1.5 w-12">Cấu trúc</span>
                          <div className={`flex-1 px-3 py-2 rounded-lg bg-gray-50 dark:bg-gray-900/50 border-l-[3px] ${c.accent} text-sm font-bold text-gray-800 dark:text-gray-200`} style={{ fontFamily: "'Noto Sans JP', sans-serif" }}>
                            {p.grammar_structure}
                          </div>
                        </div>
                      )}

                      {/* Topic + Question count */}
                      <div className="flex items-center gap-2 flex-wrap">
                        {p.grammar_topic && (
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 uppercase tracking-wide">
                            {p.grammar_topic}
                          </span>
                        )}
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-indigo-50 dark:bg-indigo-500/10 text-indigo-500 dark:text-indigo-400">
                          {p.question_count} câu quiz
                        </span>
                        {isSaved && (
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-emerald-50 dark:bg-emerald-500/10 text-emerald-500 dark:text-emerald-400">
                            ✓ Đã học
                          </span>
                        )}
                      </div>

                      {/* Note */}
                      {p.grammar_note && (
                        <div className="text-xs text-gray-500 dark:text-gray-400 leading-relaxed p-3 rounded-lg bg-amber-50/50 dark:bg-amber-500/5 border border-amber-200/40 dark:border-amber-500/10">
                          💡 {p.grammar_note}
                        </div>
                      )}

                      {/* Examples */}
                      {p.examples && p.examples.length > 0 && (
                        <div className="space-y-1.5 pt-1">
                          <span className="text-[10px] font-bold text-gray-400 dark:text-gray-500 uppercase tracking-wider">
                            Ví dụ ({p.examples.length})
                          </span>
                          {p.examples.map((ex, i) => (
                            <div key={i} className={`p-3 rounded-xl bg-gray-50 dark:bg-gray-900/40 border-l-[3px] ${c.accent}`}>
                              <div className="text-sm text-gray-800 dark:text-gray-200 leading-relaxed" style={{ fontFamily: "'Noto Sans JP', sans-serif" }}>
                                {ex.ja}
                              </div>
                              {ex.vi && (
                                <div className="text-[11px] text-gray-500 dark:text-gray-400 mt-1">→ {ex.vi}</div>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
