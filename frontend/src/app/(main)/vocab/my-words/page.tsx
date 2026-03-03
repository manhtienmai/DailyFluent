"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import "./my-words.css";

/* ── Types ── */
interface MyWord {
  id: number;
  word: string;
  state: number;
  total_reviews: number;
  last_review: string | null;
  due: string | null;
}

interface SetWord {
  item_id: number;
  word: string;
  reading: string;
  meaning: string;
  language: string;
}

interface UserSet {
  id: number;
  title: string;
  language: string;
  word_count: number;
  words: SetWord[];
}

/* ── Helpers ── */
const STATE_LABELS: Record<number, string> = { 0: "Mới", 1: "Đang học", 2: "Ôn tập", 3: "Đang học" };
const STATE_CLASS: Record<number, string> = { 0: "new", 1: "learning", 2: "review", 3: "learning" };

function formatDue(d: string | null): string {
  if (!d) return "—";
  const due = new Date(d);
  const now = new Date();
  const diff = due.getTime() - now.getTime();
  const absDiff = Math.abs(diff);
  const days = Math.floor(absDiff / 86400000);
  const hours = Math.floor((absDiff % 86400000) / 3600000);

  if (days > 0) return diff < 0 ? `${days} ngày trước` : `còn ${days} ngày`;
  if (hours > 0) return diff < 0 ? `${hours} giờ trước` : `còn ${hours} giờ`;
  return "vừa xong";
}

const ico = (w: number): React.CSSProperties => ({ width: w, height: w, flexShrink: 0 });
const PER_PAGE = 30;

export default function MyWordsPage() {
  const [words, setWords] = useState<MyWord[]>([]);
  const [allWords, setAllWords] = useState<MyWord[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [stats, setStats] = useState({ total_learning: 0, mastered_count: 0, ready_count: 0 });
  const [userSets, setUserSets] = useState<UserSet[]>([]);
  const [expandedSet, setExpandedSet] = useState<number | null>(null);
  const [deletingItem, setDeletingItem] = useState<number | null>(null);
  const [tab, setTab] = useState<"words" | "sets">("sets");

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [wordsRes, setsRes] = await Promise.all([
        fetch(`/api/v1/vocab/my-words`, { credentials: "include" }),
        fetch(`/api/v1/vocab/user-sets`, { credentials: "include" }),
      ]);
      if (wordsRes.ok) {
        const data = await wordsRes.json();
        if (Array.isArray(data)) {
          setAllWords(data);
          setStats({
            total_learning: data.filter((w: MyWord) => w.state === 1 || w.state === 3 || w.state === 0).length,
            mastered_count: data.filter((w: MyWord) => w.total_reviews >= 3).length,
            ready_count: data.filter((w: MyWord) => { if (!w.due) return false; return new Date(w.due) <= new Date(); }).length,
          });
          setTotalPages(Math.ceil(data.length / PER_PAGE));
        }
      }
      if (setsRes.ok) {
        const setsData = await setsRes.json();
        if (Array.isArray(setsData)) setUserSets(setsData);
      }
    } catch { /* ignore */ } finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);
  useEffect(() => { setWords(allWords.slice((page - 1) * PER_PAGE, page * PER_PAGE)); }, [page, allWords]);

  const handleDeleteItem = async (setId: number, itemId: number) => {
    setDeletingItem(itemId);
    try {
      const res = await fetch(`/api/v1/vocab/sets/${setId}/items/${itemId}`, {
        method: "DELETE", credentials: "include",
      });
      if (res.ok) {
        setUserSets(prev => prev.map(s =>
          s.id === setId
            ? { ...s, words: s.words.filter(w => w.item_id !== itemId), word_count: s.word_count - 1 }
            : s
        ));
      }
    } catch { /* ignore */ } finally { setDeletingItem(null); }
  };

  const handleDeleteSet = async (setId: number) => {
    if (!confirm("Xóa toàn bộ bộ từ này?")) return;
    try {
      const res = await fetch(`/api/v1/vocab/sets/${setId}`, {
        method: "DELETE", credentials: "include",
      });
      if (res.ok) setUserSets(prev => prev.filter(s => s.id !== setId));
    } catch { /* ignore */ }
  };

  const totalSetWords = userSets.reduce((sum, s) => sum + s.word_count, 0);

  return (
    <div className="mw-page">
      <div className="mw-container">

        {/* ── Header ── */}
        <div className="mw-glass mw-header">
          <div className="mw-header-left">
            <h1 className="mw-title">Từ vựng của tôi</h1>
            {stats.ready_count > 0 && (
              <span className="mw-badge-ready">
                <svg style={ico(13)} fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2.5"><circle cx="12" cy="12" r="10" /><path d="M12 6v6l4 2" /></svg>
                {stats.ready_count} từ cần ôn
              </span>
            )}
          </div>
          <div className="mw-header-right">
            <Link href="/vocab/flashcards" className="mw-btn mw-btn--primary">
              <svg style={ico(14)} fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2.5"><path d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25H12" /></svg>
              Ôn tập
            </Link>
          </div>
        </div>

        {/* ── Stats Row ── */}
        <div className="mw-glass-light mw-stats">
          <div className="mw-stat">
            <div className="mw-stat-icon mw-stat-icon--indigo">
              <svg style={ico(20)} fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" /></svg>
            </div>
            <div><div className="mw-stat-val">{totalSetWords}</div><div className="mw-stat-lbl">TỔNG TỪ</div></div>
          </div>
          <div className="mw-stat">
            <div className="mw-stat-icon mw-stat-icon--emerald">
              <svg style={ico(20)} fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            </div>
            <div><div className="mw-stat-val">{stats.mastered_count}</div><div className="mw-stat-lbl">ĐÃ THUỘC</div></div>
          </div>
          <div className="mw-stat">
            <div className="mw-stat-icon mw-stat-icon--amber">
              <svg style={ico(20)} fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            </div>
            <div><div className="mw-stat-val">{stats.ready_count}</div><div className="mw-stat-lbl">CẦN ÔN</div></div>
          </div>
          <div className="mw-stat">
            <div className="mw-stat-icon mw-stat-icon--violet">
              <svg style={ico(20)} fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z" /></svg>
            </div>
            <div><div className="mw-stat-val">{userSets.length}</div><div className="mw-stat-lbl">BỘ TỪ</div></div>
          </div>
        </div>

        {/* ── Tabs ── */}
        <div className="mw-tabs">
          <button className={`mw-tab ${tab === "sets" ? "mw-tab--active" : ""}`} onClick={() => setTab("sets")}>
            📁 Bộ từ vựng ({userSets.length})
          </button>
          <button className={`mw-tab ${tab === "words" ? "mw-tab--active" : ""}`} onClick={() => setTab("words")}>
            📖 Tiến trình SRS ({allWords.length})
          </button>
        </div>

        {/* ── Tab: User Sets ── */}
        {tab === "sets" && (
          loading ? (
            <div className="mw-glass" style={{ padding: "3rem", textAlign: "center" }}>
              <div className="mw-spinner" />
              <p style={{ color: "var(--text-secondary)", marginTop: ".75rem", fontSize: ".875rem" }}>Đang tải...</p>
            </div>
          ) : userSets.length > 0 ? (
            <div className="mw-sets">
              {userSets.map(s => (
                <div key={s.id} className="mw-glass mw-set">
                  <div className="mw-set-header" onClick={() => setExpandedSet(expandedSet === s.id ? null : s.id)}>
                    <div className="mw-set-info">
                      <span className="mw-set-lang">{s.language === "jp" ? "🇯🇵" : "🇺🇸"}</span>
                      <div>
                        <h3 className="mw-set-title">{s.title}</h3>
                        <span className="mw-set-count">{s.word_count} từ</span>
                      </div>
                    </div>
                    <div className="mw-set-actions">
                      <button className="mw-btn-icon mw-btn-icon--danger" title="Xóa bộ từ" onClick={(e) => { e.stopPropagation(); handleDeleteSet(s.id); }}>
                        <svg style={ico(14)} fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" /></svg>
                      </button>
                      <svg style={{ ...ico(16), transition: "transform .2s", transform: expandedSet === s.id ? "rotate(180deg)" : "rotate(0)" }} fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" /></svg>
                    </div>
                  </div>

                  {expandedSet === s.id && (
                    <div className="mw-set-words">
                      {s.words.length > 0 ? (
                        <>
                          <div className="mw-sw-hdr">
                            <span>Từ vựng</span><span>Đọc</span><span>Nghĩa</span><span></span>
                          </div>
                          {s.words.map(w => (
                            <div key={w.item_id} className="mw-sw-row">
                              <span className="mw-sw-word">{w.word}</span>
                              <span className="mw-sw-reading">{w.reading || "—"}</span>
                              <span className="mw-sw-meaning">{w.meaning || "—"}</span>
                              <button
                                className="mw-btn-del"
                                disabled={deletingItem === w.item_id}
                                onClick={() => handleDeleteItem(s.id, w.item_id)}
                                title="Xóa từ này"
                              >
                                {deletingItem === w.item_id ? "..." : "✕"}
                              </button>
                            </div>
                          ))}
                        </>
                      ) : (
                        <p className="mw-sw-empty">Chưa có từ nào trong bộ này.</p>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="mw-glass" style={{ padding: "3rem", textAlign: "center", color: "var(--text-secondary)" }}>
              <p style={{ fontSize: "1.5rem", marginBottom: ".5rem" }}>📁</p>
              <p>Chưa có bộ từ nào. Thêm từ vựng qua trang <strong>Hán tự</strong>!</p>
            </div>
          )
        )}

        {/* ── Tab: SRS Words ── */}
        {tab === "words" && (
          loading ? (
            <div className="mw-glass" style={{ padding: "3rem", textAlign: "center" }}>
              <div className="mw-spinner" />
            </div>
          ) : words.length > 0 ? (
            <div className="mw-glass mw-words">
              <div className="mw-words-hdr"><span>TỪ VỰNG</span><span>TRẠNG THÁI</span><span>ÔN TẬP</span></div>
              <div className="mw-words-body">
                {words.map((w, i) => (
                  <div key={w.id} className="mw-word-row" style={{ animationDelay: `${i * 20}ms` }}>
                    <div className="mw-word-left">
                      <span className="mw-word-idx">{(page - 1) * PER_PAGE + i + 1}</span>
                      <span className="mw-word-txt">{w.word}</span>
                    </div>
                    <div>
                      <span className={`mw-status mw-status--${STATE_CLASS[w.state] || "new"}`}>
                        <span className="mw-status-dot" />
                        {STATE_LABELS[w.state] || "Mới"}
                      </span>
                    </div>
                    <div className="mw-word-due">{formatDue(w.due)}</div>
                  </div>
                ))}
              </div>
              {totalPages > 1 && (
                <div className="mw-pagination">
                  {page > 1 && <button className="mw-pg-btn" onClick={() => setPage(page - 1)}><svg style={ico(14)} fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2.5"><path d="M15 18l-6-6 6-6" /></svg></button>}
                  {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
                    <button key={p} className={`mw-pg-btn${p === page ? " active" : ""}`} onClick={() => setPage(p)}>{p}</button>
                  ))}
                  {page < totalPages && <button className="mw-pg-btn" onClick={() => setPage(page + 1)}><svg style={ico(14)} fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2.5"><path d="M9 18l6-6-6-6" /></svg></button>}
                </div>
              )}
            </div>
          ) : (
            <div className="mw-glass" style={{ padding: "3rem", textAlign: "center", color: "var(--text-secondary)" }}>
              <p style={{ fontSize: "1.5rem", marginBottom: ".5rem" }}>📚</p>
              <p>Chưa có dữ liệu SRS. Hãy bắt đầu ôn tập qua <strong>Flashcard</strong>!</p>
            </div>
          )
        )}
      </div>

      
    </div>
  );
}
