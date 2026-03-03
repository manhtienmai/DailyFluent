"use client";

/**
 * Study Hub — Two-tab page:
 * 1) Ngữ pháp: grammar patterns being studied (from localStorage saved-grammar)
 * 2) Từ vựng:  vocabulary words encountered in usage quiz (from API)
 *
 * Grammar cards are always expanded (full info visible).
 * Delete mode: toggle button at top → checkboxes appear → delete selected.
 * Search: supports romaji → hiragana/katakana auto-conversion.
 */

import { useState, useEffect, useMemo, useCallback } from "react";
import Link from "next/link";
import "./study.css";
import {
  getSavedGrammarList,
  getSavedGrammarStats,
  removeGrammar,
  getDismissedSet,
  SavedGrammar,
} from "@/lib/saved-grammar";
import { smartMatch } from "@/lib/romaji";
import { useStudyTimer } from "@/hooks/useStudyTimer";

type Tab = "grammar" | "vocab";

const LEVEL_COLORS: Record<string, string> = {
  N1: "#dc2626", N2: "#2563eb", N3: "#eab308", N4: "#3b82f6", N5: "#10b981",
};
const LEVELS = ["", "N5", "N4", "N3", "N2", "N1"];

interface VocabWord {
  word: string;
  reading: string;
  han_viet: string;
  meaning_vi: string;
  level: string;
}

export default function StudyHubPage() {
  useStudyTimer();
  const [tab, setTab] = useState<Tab>("grammar");

  // ── Grammar state ──
  const [grammarList, setGrammarList] = useState<SavedGrammar[]>([]);
  const [dismissedSet, setDismissedSet] = useState<Set<string>>(new Set());
  const [grammarFilter, setGrammarFilter] = useState("");
  const [grammarSearch, setGrammarSearch] = useState("");
  const [deleteMode, setDeleteMode] = useState(false);
  const [selectedForDelete, setSelectedForDelete] = useState<Set<string>>(new Set());

  // ── Vocab state ──
  const [vocabWords, setVocabWords] = useState<VocabWord[]>([]);
  const [vocabLoading, setVocabLoading] = useState(false);
  const [vocabFilter, setVocabFilter] = useState("");
  const [vocabSearch, setVocabSearch] = useState("");
  const [vocabFetched, setVocabFetched] = useState(false);

  // Load grammar from localStorage
  const refreshGrammar = useCallback(() => {
    setGrammarList(getSavedGrammarList());
    setDismissedSet(getDismissedSet());
  }, []);

  useEffect(() => {
    refreshGrammar();
  }, [refreshGrammar]);

  // Fetch vocab words from usage quiz API (lazy, only when tab = vocab)
  useEffect(() => {
    if (tab !== "vocab" || vocabFetched) return;
    setVocabLoading(true);

    // First sync usage quiz words into FSRS, then fetch the word list
    fetch("/api/v1/exam/usage/sync-to-fsrs", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
    })
      .catch(() => {}) // ignore sync errors
      .finally(() => {
        fetch("/api/v1/exam/usage/all-questions", { credentials: "include" })
          .then((r) => (r.ok ? r.json() : { questions: [] }))
          .then((d) => {
            const questions = d.questions || [];
            const wordMap = new Map<string, VocabWord>();
            for (const q of questions) {
              const ej = q.explanation_json;
              if (ej?.word && !wordMap.has(ej.word)) {
                wordMap.set(ej.word, {
                  word: ej.word,
                  reading: ej.reading || "",
                  han_viet: ej.han_viet || "",
                  meaning_vi: ej.meaning_vi || "",
                  level: q.level || "",
                });
              }
            }
            setVocabWords(Array.from(wordMap.values()));
            setVocabLoading(false);
            setVocabFetched(true);
          })
          .catch(() => setVocabLoading(false));
      });
  }, [tab, vocabFetched]);

  // ── Grammar filtering (with smart search) ──
  const grammarStats = useMemo(() => getSavedGrammarStats(), [grammarList]);
  const activeGrammar = useMemo(() => {
    let list = grammarList.filter((g) => !dismissedSet.has(g.grammar_point));
    if (grammarFilter) list = list.filter((g) => g.level === grammarFilter);
    if (grammarSearch.trim()) {
      list = list.filter((g) =>
        smartMatch(grammarSearch, [
          g.grammar_point,
          g.grammar_meaning,
          g.grammar_structure,
        ])
      );
    }
    return list;
  }, [grammarList, dismissedSet, grammarFilter, grammarSearch]);

  // ── Vocab filtering (with smart search) ──
  const vocabLevelStats = useMemo(() => {
    const stats: Record<string, number> = {};
    for (const w of vocabWords) {
      const lv = w.level || "?";
      stats[lv] = (stats[lv] || 0) + 1;
    }
    return stats;
  }, [vocabWords]);

  const filteredVocab = useMemo(() => {
    let list = vocabWords;
    if (vocabFilter) list = list.filter((w) => w.level === vocabFilter);
    if (vocabSearch.trim()) {
      list = list.filter((w) =>
        smartMatch(vocabSearch, [
          w.word,
          w.reading,
          w.han_viet,
          w.meaning_vi,
        ])
      );
    }
    return list;
  }, [vocabWords, vocabFilter, vocabSearch]);

  // ── Delete mode handlers ──
  const toggleDeleteMode = () => {
    setDeleteMode((v) => {
      if (v) setSelectedForDelete(new Set());
      return !v;
    });
  };
  const toggleSelect = (gp: string) => {
    setSelectedForDelete((prev) => {
      const next = new Set(prev);
      next.has(gp) ? next.delete(gp) : next.add(gp);
      return next;
    });
  };
  const selectAll = () => {
    setSelectedForDelete(new Set(activeGrammar.map((g) => g.grammar_point)));
  };
  const deselectAll = () => setSelectedForDelete(new Set());
  const deleteSelected = () => {
    selectedForDelete.forEach((gp) => removeGrammar(gp));
    setSelectedForDelete(new Set());
    setDeleteMode(false);
    refreshGrammar();
  };

  return (
    <div className="sh-page">
      <div className="sh-container">
        <nav className="sh-breadcrumb">
          <Link href="/exam">Luyện thi</Link>
          <span>/</span>
          <span className="current">Kho học tập</span>
        </nav>

        <h1 className="sh-title">📚 Kho Học Tập</h1>
        <p className="sh-desc">Tổng hợp ngữ pháp và từ vựng đang học từ các bài quiz.</p>

        {/* ── Tab Bar ── */}
        <div className="sh-tabs">
          <button className={`sh-tab ${tab === "grammar" ? "active" : ""}`} onClick={() => setTab("grammar")}>
            <span className="sh-tab-icon">📝</span> Ngữ pháp
            <span className="sh-tab-count">{grammarList.length}</span>
          </button>
          <button className={`sh-tab ${tab === "vocab" ? "active" : ""}`} onClick={() => setTab("vocab")}>
            <span className="sh-tab-icon">📖</span> Từ vựng
            {vocabFetched && <span className="sh-tab-count">{vocabWords.length}</span>}
          </button>
        </div>

        {/* ── Grammar Tab ── */}
        {tab === "grammar" && (
          <div className="sh-content">
            {/* Toolbar: filters + delete toggle */}
            <div className="sh-toolbar">
              <div className="sh-filters">
                {LEVELS.map((l) => (
                  <button
                    key={l}
                    className={`sh-filter ${grammarFilter === l ? "active" : ""}`}
                    onClick={() => setGrammarFilter(l)}
                  >
                    {l || "Tất cả"}
                    {l ? (grammarStats[l] ? ` (${grammarStats[l]})` : "") : ` (${grammarList.length})`}
                  </button>
                ))}
              </div>
              <button
                className={`sh-delete-toggle ${deleteMode ? "active" : ""}`}
                onClick={toggleDeleteMode}
              >
                {deleteMode ? "✕ Hủy" : "🗑 Xóa"}
              </button>
            </div>

            <input
              type="text"
              value={grammarSearch}
              onChange={(e) => setGrammarSearch(e.target.value)}
              placeholder="🔍 Tìm ngữ pháp..."
              className="sh-search"
            />

            {/* Delete action bar */}
            {deleteMode && (
              <div className="sh-delete-bar">
                <button className="sh-delete-bar-btn select-all" onClick={selectedForDelete.size === activeGrammar.length ? deselectAll : selectAll}>
                  {selectedForDelete.size === activeGrammar.length ? "☐ Bỏ chọn" : "☑ Chọn tất cả"}
                </button>
                <span className="sh-delete-bar-count">{selectedForDelete.size} đã chọn</span>
                <button className="sh-delete-bar-btn confirm" disabled={selectedForDelete.size === 0} onClick={deleteSelected}>
                  🗑 Xóa ({selectedForDelete.size})
                </button>
              </div>
            )}

            {grammarList.length === 0 ? (
              <div className="sh-empty">
                <div className="sh-empty-icon">📭</div>
                <div className="sh-empty-text">Chưa có ngữ pháp nào được lưu</div>
                <div className="sh-empty-hint">Làm quiz ngữ pháp để tự động lưu các mẫu ngữ pháp</div>
                <Link href="/exam/bunpou" className="sh-empty-btn">→ Đi làm quiz</Link>
              </div>
            ) : activeGrammar.length === 0 ? (
              <div className="sh-empty">
                <div className="sh-empty-icon">🔍</div>
                <div className="sh-empty-text">Không tìm thấy</div>
              </div>
            ) : (
              <>
                {/* Study CTA */}
                <div className="sh-study-bar">
                  <Link href="/exam/bunpou/flashcard" className="sh-study-btn grammar">
                    <span className="sh-study-btn-icon">🃏</span>
                    <span className="sh-study-btn-text">Học Flashcard Ngữ pháp</span>
                    <span className="sh-study-btn-count">{activeGrammar.length}</span>
                    <span className="sh-study-btn-arrow">→</span>
                  </Link>
                </div>

                <div className="sh-count">{activeGrammar.length} cấu trúc</div>
                <div className="sh-list">
                  {activeGrammar.map((g) => {
                    const lc = LEVEL_COLORS[g.level] || "#475569";
                    const isSelected = selectedForDelete.has(g.grammar_point);
                    return (
                      <div
                        key={g.grammar_point}
                        className={`sh-gcard ${deleteMode && isSelected ? "selected" : ""}`}
                        onClick={deleteMode ? () => toggleSelect(g.grammar_point) : undefined}
                        style={deleteMode ? { cursor: "pointer" } : { borderLeftColor: lc }}
                      >
                        {/* Checkbox in delete mode */}
                        {deleteMode && (
                          <div className="sh-gcard-cb">
                            <input
                              type="checkbox"
                              checked={isSelected}
                              onChange={() => toggleSelect(g.grammar_point)}
                              onClick={(e) => e.stopPropagation()}
                            />
                          </div>
                        )}

                        {/* Card content — always fully visible */}
                        <div className="sh-gcard-body">
                          <div className="sh-gcard-top">
                            <span className="sh-gcard-dot" style={{ background: lc }} />
                            <span className="sh-gcard-name">{g.grammar_point}</span>
                            {g.level && (
                              <span className="sh-gcard-level" style={{ color: lc, borderColor: `${lc}40`, background: `${lc}10` }}>
                                {g.level}
                              </span>
                            )}
                          </div>

                          {g.grammar_structure && (
                            <div className="sh-gcard-struct">{g.grammar_structure}</div>
                          )}

                          {g.grammar_meaning && (
                            <div className="sh-gcard-meaning">► {g.grammar_meaning}</div>
                          )}

                          {g.grammar_note && (
                            <div className="sh-gcard-note">📌 {g.grammar_note}</div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </>
            )}
          </div>
        )}

        {/* ── Vocab Tab ── */}
        {tab === "vocab" && (
          <div className="sh-content">
            {vocabLoading ? (
              <div className="sh-empty">
                <div className="sh-empty-icon sh-pulse">📖</div>
                <div className="sh-empty-text">Đang tải từ vựng...</div>
              </div>
            ) : vocabWords.length === 0 ? (
              <div className="sh-empty">
                <div className="sh-empty-icon">📭</div>
                <div className="sh-empty-text">Chưa có từ vựng</div>
                <div className="sh-empty-hint">Làm quiz cách dùng từ để thêm từ vựng vào đây</div>
                <Link href="/exam/usage" className="sh-empty-btn">→ Đi làm quiz</Link>
              </div>
            ) : (
              <>
                <div className="sh-filters">
                  {LEVELS.map((l) => (
                    <button
                      key={l}
                      className={`sh-filter ${vocabFilter === l ? "active" : ""}`}
                      onClick={() => setVocabFilter(l)}
                    >
                      {l || "Tất cả"}
                      {l ? (vocabLevelStats[l] ? ` (${vocabLevelStats[l]})` : "") : ` (${vocabWords.length})`}
                    </button>
                  ))}
                </div>

                <input
                  type="text"
                  value={vocabSearch}
                  onChange={(e) => setVocabSearch(e.target.value)}
                  placeholder="🔍 Tìm từ vựng... (hỗ trợ romaji)"
                  className="sh-search"
                />

                <div className="sh-count">{filteredVocab.length} từ</div>

                {/* Vocab study CTA */}
                <div className="sh-study-bar">
                  <Link href="/vocab/flashcards?language=jp" className="sh-study-btn vocab">
                    <span className="sh-study-btn-icon">📖</span>
                    <span className="sh-study-btn-text">Học Flashcard Từ vựng</span>
                    <span className="sh-study-btn-count">{filteredVocab.length}</span>
                    <span className="sh-study-btn-arrow">→</span>
                  </Link>
                  <Link href="/vocab/flashcards?language=jp" className="sh-study-btn-secondary">
                    ✍️ Ôn tập
                  </Link>
                </div>

                <div className="sh-vgrid">
                  {filteredVocab.map((w, idx) => {
                    const lc = LEVEL_COLORS[w.level] || "#475569";
                    return (
                      <Link
                        key={w.word}
                        href={`/vocab/${encodeURIComponent(w.word)}`}
                        className="sh-vcard"
                        style={{
                          borderLeftColor: lc,
                          background: `linear-gradient(135deg, ${lc}08, ${lc}04)`,
                          animationDelay: `${Math.min(idx * 20, 300)}ms`,
                        }}
                      >
                        <div className="sh-vcard-head">
                          <span className="sh-vcard-word" style={{ color: lc }}>{w.word}</span>
                          {w.level && (
                            <span className="sh-vcard-badge" style={{ color: lc, borderColor: `${lc}35`, background: `${lc}0c` }}>
                              {w.level}
                            </span>
                          )}
                        </div>
                        <div className="sh-vcard-sub">
                          {w.reading && <span className="sh-vcard-reading">{w.reading}</span>}
                          {w.han_viet && (
                            <span className="sh-vcard-hv" style={{ color: lc }}>【{w.han_viet}】</span>
                          )}
                        </div>
                        <div className="sh-vcard-meaning">{w.meaning_vi}</div>
                      </Link>
                    );
                  })}
                </div>
              </>
            )}
          </div>
        )}
      </div>

      
    </div>
  );
}
