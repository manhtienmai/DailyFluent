"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import Script from "next/script";
import "./kanji-detail.css";

/* ── Types ── */
interface KanjiData {
  id: number;
  char: string;
  sino_vi: string;
  keyword: string;
  onyomi: string;
  kunyomi: string;
  meaning_vi: string;
  strokes: number | null;
  note: string;
  formation: string;
  jlpt_level: string;
}

interface KanjiVocab {
  id: number;
  word: string;
  reading: string;
  meaning: string;
  priority: number;
  vocabulary_id: number | null;
  jlpt_level: string;
}


interface KanjiSibling {
  char: string;
  sino_vi: string;
}

interface KanjiDetail {
  kanji: KanjiData;
  vocab: KanjiVocab[];
  kanji_map: Record<string, string>;
  lesson_label: string;
  kanji_index: number;
  kanji_total: number;
  prev_kanji: KanjiSibling | null;
  next_kanji: KanjiSibling | null;
}

/* ── Dmak globals ── */
declare const Dmak: unknown;
declare const Raphael: unknown;

const KVG_URI = "https://kanjivg.tagaini.net/kanjivg/kanji/";

/* ── JLPT badge color map ── */
const jlptBadgeClass: Record<string, string> = {
  n5: "jb-n5",
  n4: "jb-n4",
  n3: "jb-n3",
  n2: "jb-n2",
  n1: "jb-n1",
  bt: "jb-bt",
};

export default function KanjiDetailPage() {
  const params = useParams();
  const router = useRouter();
  const char = decodeURIComponent(params.char as string);

  const [data, setData] = useState<KanjiDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showOrder, setShowOrder] = useState(false);
  const [showGrid, setShowGrid] = useState(true);
  const [selectedVocab, setSelectedVocab] = useState<Set<number>>(new Set());
  const [studyMsg, setStudyMsg] = useState<string | null>(null);
  const [scriptsLoaded, setScriptsLoaded] = useState(false);
  const [raphaelLoaded, setRaphaelLoaded] = useState(false);
  const dmakRef = useRef<unknown>(null);
  const canvasRef = useRef<HTMLDivElement>(null);
  const [canvasDone, setCanvasDone] = useState(false);
  const [transitioning, setTransitioning] = useState(false);

  /* ── Fetch data ── */
  useEffect(() => {
    // Only show full loading on first load (no data yet)
    if (!data) setLoading(true);
    setTransitioning(true);
    setError(null);
    fetch(`/api/v1/kanji/${encodeURIComponent(char)}`, { credentials: "include" })
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((d: KanjiDetail) => {
        setData(d);
        setLoading(false);
        // Small delay to let React render then fade in
        requestAnimationFrame(() => setTransitioning(false));
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
        setTransitioning(false);
      });
  }, [char]);

  /* ── Reset UI state when navigating to a different kanji ── */
  useEffect(() => {
    setSelectedVocab(new Set());
    setStudyMsg(null);
    setCanvasDone(false);
  }, [char]);

  /* ── Keyboard arrow navigation ← → ── */
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;

      if (e.key === "ArrowLeft" && data?.prev_kanji) {
        e.preventDefault();
        router.push(`/kanji/${encodeURIComponent(data.prev_kanji.char)}`);
      } else if (e.key === "ArrowRight" && data?.next_kanji) {
        e.preventDefault();
        router.push(`/kanji/${encodeURIComponent(data.next_kanji.char)}`);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [data, router]);

  /* ── Create Dmak animation ── */
  const createDmak = useCallback(() => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const w = window as any;

    // Check scripts are available (either via state or already on window)
    const hasRaphael = raphaelLoaded || !!w.Raphael;
    const hasDmak = scriptsLoaded || !!w.Dmak;
    if (!hasRaphael || !hasDmak || !data) return;

    const target = document.getElementById("dmak-target");
    if (!target) return;

    // Clean up old Dmak instance
    if (dmakRef.current) {
      try { (dmakRef.current as any).erase(); } catch { /* ignore */ }
      dmakRef.current = null;
    }
    target.innerHTML = "";
    setCanvasDone(false);

    // Show loading shimmer (use CSS, don't remove from DOM)
    const loadingEl = document.getElementById("writer-loading");
    if (loadingEl) loadingEl.style.display = "flex";

    let stepCount = 0;
    let totalStk = 0;

    try {
      const DmakC = w.Dmak;
      if (!DmakC) return;

      dmakRef.current = new DmakC(char, {
        element: "dmak-target",
        width: "322",
        height: "322",
        uri: KVG_URI,
        step: 0.022,
        grid: { show: false },

        loaded: (strokes: unknown[]) => {
          totalStk = strokes.length;
          if (loadingEl) loadingEl.style.display = "none";

          // Create gray ghost strokes as background guide
          const dmakInstance = dmakRef.current as any;
          if (dmakInstance && dmakInstance.strokes && dmakInstance.papers) {
            // Find the SVG element created by Dmak
            const dmakSvg = target.querySelector("svg.dmak-svg");
            if (dmakSvg) {
              // Draw all stroke paths in gray as ghost guides
              for (let i = 0; i < dmakInstance.strokes.length; i++) {
                const s = dmakInstance.strokes[i];
                const ghostPath = document.createElementNS("http://www.w3.org/2000/svg", "path");
                ghostPath.setAttribute("d", s.path);
                ghostPath.setAttribute("fill", "none");
                ghostPath.setAttribute("stroke", "#d1d5db");
                ghostPath.setAttribute("stroke-width", "5");
                ghostPath.setAttribute("stroke-linecap", "round");
                ghostPath.setAttribute("stroke-linejoin", "round");
                ghostPath.classList.add("dmak-ghost-stroke");
                // Insert ghost strokes before other elements so they appear behind
                dmakSvg.insertBefore(ghostPath, dmakSvg.firstChild);
              }
            }
          }

          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          (dmakRef.current as any)?.render(totalStk);
        },

        erred: () => {
          // SVG not found for this kanji
          if (loadingEl) loadingEl.style.display = "none";
          console.warn("[Dmak] SVG not found for:", char);
        },

        drew: () => {
          stepCount++;
        },

        stroke: {
          animated: { drawing: true, erasing: true },
          order: {
            type: 1,
            visible: true,  // Always render; visibility controlled by CSS
            attr: { "font-size": "8" },
          },
          attr: {
            stroke: "#0f172a",
            "stroke-width": 5,
            active: "#0f172a",
            "stroke-linecap": "round",
            "stroke-linejoin": "round",
          },
        },
      });
    } catch (e) {
      console.error("[Dmak] Error creating dmak:", e);
      if (loadingEl) loadingEl.style.display = "none";
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scriptsLoaded, raphaelLoaded, data, char]);

  /* ── Auto-create Dmak when scripts load ── */
  useEffect(() => {
    createDmak();
  }, [createDmak]);

  /* ── Loading (only on first visit, no data yet) ── */
  if (loading && !data) {
    return (
      <div className="kd-page px-4 py-7">
        <div className="max-w-4xl mx-auto text-center" style={{ padding: "60px 0", color: "var(--text-tertiary)" }}>
          Đang tải...
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="kd-page px-4 py-7">
        <div className="max-w-4xl mx-auto text-center" style={{ padding: "60px 0", color: "var(--status-error)" }}>
          Không tìm thấy Hán tự: {char}
        </div>
      </div>
    );
  }

  const { kanji, vocab, kanji_map, lesson_label, kanji_index, kanji_total, prev_kanji, next_kanji } = data;
  const jlptClass = jlptBadgeClass[kanji.jlpt_level?.toLowerCase()] || "";

  return (
    <>
      {/* External scripts for Dmak */}
      <Script
        src="https://cdnjs.cloudflare.com/ajax/libs/raphael/2.3.0/raphael.min.js"
        onLoad={() => setRaphaelLoaded(true)}
        strategy="afterInteractive"
      />
      <Script
        src="https://cdn.jsdelivr.net/gh/mbilbille/dmak/dist/dmak.min.js"
        onLoad={() => setScriptsLoaded(true)}
        strategy="afterInteractive"
      />

      <div className={`kd-page px-4 py-7 md:py-8 ${transitioning ? "kd-transitioning" : ""}`}>
        <div className="kd-container">

          {/* Breadcrumb */}
          <nav className="mb-5 flex items-center gap-2 text-sm flex-wrap" style={{ color: "var(--text-tertiary)" }}>
            <Link href="/kanji" className="hover:text-current transition-colors" style={{ color: "var(--text-tertiary)" }}>
              Hán tự
            </Link>
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
            </svg>
            <span className="font-semibold" style={{ color: "var(--text-primary)", fontFamily: "var(--font-jp-user, 'Noto Sans JP'), sans-serif" }}>
              {kanji.char}
            </span>
            {lesson_label && (
              <>
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
                </svg>
                <span style={{ color: "var(--text-tertiary)" }}>
                  {lesson_label}{kanji_index > 0 && ` (${kanji_index}/${kanji_total})`}
                </span>
              </>
            )}
          </nav>

          {/* Two‑column layout: LEFT (canvas + info) | RIGHT (vocab) */}
          <div className="kd-split">

            {/* ── LEFT COLUMN ── */}
            <div className="kd-left">
              <div className="kd-card p-5">
                <div className="kd-info-layout">

                  {/* Canvas */}
                  <div className="kd-canvas-col">
                    {/* Toolbar above SVG */}
                    <div className="kd-toolbar">
                      <button
                        className={`kd-btn-tool ${showOrder ? "active" : ""}`}
                        onClick={() => setShowOrder(!showOrder)}
                        title="Hiện số thứ tự nét"
                      >
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"
                            d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" />
                        </svg>
                        Số nét
                      </button>
                      <button
                        className={`kd-btn-tool ${showGrid ? "active" : ""}`}
                        onClick={() => setShowGrid(!showGrid)}
                        title="Bật/tắt lưới hỗ trợ"
                      >
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"
                            d="M4 4h16v16H4V4zm0 8h16M12 4v16" />
                        </svg>
                        Lưới
                      </button>
                    </div>

                    <div
                      ref={canvasRef}
                      id="canvas-wrap"
                      className={`kd-canvas-wrap ${canvasDone ? "is-done" : ""}${showOrder ? "" : " hide-order"}`}
                      onClick={() => createDmak()}
                    >
                      <svg className="grid-svg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 280 280" aria-hidden="true"
                        style={{ display: showGrid ? "block" : "none" }}
                      >
                        <line x1="0" y1="0" x2="280" y2="280" stroke="rgba(0,0,0,.15)" strokeWidth="1" strokeDasharray="5 4" />
                        <line x1="280" y1="0" x2="0" y2="280" stroke="rgba(0,0,0,.15)" strokeWidth="1" strokeDasharray="5 4" />
                        <line x1="0" y1="140" x2="280" y2="140" stroke="rgba(0,0,0,.22)" strokeWidth="1" strokeDasharray="5 4" />
                        <line x1="140" y1="0" x2="140" y2="280" stroke="rgba(0,0,0,.22)" strokeWidth="1" strokeDasharray="5 4" />
                      </svg>

                      <div id="writer-loading" className="kd-shimmer">
                        <div className="kd-shimmer-box" />
                        <p style={{ fontSize: ".75rem", color: "#94a3b8", marginTop: "4px" }}>Đang tải nét chữ…</p>
                      </div>

                      <div id="dmak-target" />
                    </div>
                  </div>

                  {/* Info */}
                  <div className="kd-meta">
                    {/* Hán Việt + JLPT badge */}
                    <div className="kd-header-row">
                      {kanji.sino_vi && (
                        <span className="kd-hanviet">{kanji.sino_vi}</span>
                      )}
                      {kanji.jlpt_level && (
                        <span className={`jb ${jlptClass}`}>{kanji.jlpt_level}</span>
                      )}
                    </div>

                    {/* Meaning */}
                    {kanji.meaning_vi && (
                      <p className="kd-meaning">{kanji.meaning_vi}</p>
                    )}

                    {/* Readings */}
                    {(kanji.onyomi || kanji.kunyomi) && (
                      <div className="kd-readings">
                        {kanji.onyomi && (
                          <div className="kd-pill">
                            <div className="kd-pill-label">Âm on</div>
                            <div className="kd-pill-val">{kanji.onyomi}</div>
                          </div>
                        )}
                        {kanji.kunyomi && (
                          <div className="kd-pill">
                            <div className="kd-pill-label">Âm kun</div>
                            <div className="kd-pill-val">{kanji.kunyomi}</div>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Strokes */}
                    {kanji.strokes && (
                      <p className="kd-strokes">
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"
                            d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                        </svg>
                        {kanji.strokes} nét
                      </p>
                    )}

                    {/* Formation */}
                    {kanji.formation && (
                      <div className="kd-formation">
                        <p className="kd-formation-label">🧩 Cấu tạo</p>
                        <p className="kd-formation-text">{kanji.formation}</p>
                      </div>
                    )}

                    {/* Note */}
                    {kanji.note && (
                      <div className="kd-note">
                        <p className="kd-note-label">Mẹo nhớ</p>
                        <p className="kd-note-text">{kanji.note}</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* ── RIGHT COLUMN: Vocabulary ── */}
            <div className="kd-right">
              <div className="kd-card kd-vocab-card">
                <h2 className="kd-vocab-title">
                  Từ vựng chứa{" "}
                  <span className="kd-vocab-kanji">{kanji.char}</span>
                </h2>

                {vocab.length > 0 ? (
                  <>
                    <div className="kd-vocab-toolbar">
                      <button
                        className="kd-btn-select-all"
                        onClick={() => {
                          if (selectedVocab.size === vocab.length) {
                            setSelectedVocab(new Set());
                          } else {
                            setSelectedVocab(new Set(vocab.map(v => v.id)));
                          }
                        }}
                      >
                        {selectedVocab.size === vocab.length ? "✕ Bỏ chọn" : "☑ Chọn tất cả"}
                      </button>
                    </div>
                    <div className="kd-vocab-list">
                      {vocab.map((v) => {
                        const kanjiChars = [...v.word].filter(ch => ch >= '\u4e00' && ch <= '\u9fff');
                        const breakdownParts = (kanjiChars.length >= 2 && kanji_map)
                          ? kanjiChars.map(ch => kanji_map[ch] ? `${ch}(${kanji_map[ch]})` : null).filter(Boolean)
                          : [];

                        return (
                            <div key={v.id} className="kd-vocab-item">
                            <div className={`kd-vocab-row ${selectedVocab.has(v.id) ? "kd-vocab-selected" : ""}`}>
                              <input
                                type="checkbox"
                                className="kd-vocab-cb"
                                checked={selectedVocab.has(v.id)}
                                onChange={(e) => {
                                  setSelectedVocab(prev => {
                                    const next = new Set(prev);
                                    e.target.checked ? next.add(v.id) : next.delete(v.id);
                                    return next;
                                  });
                                }}
                              />
                              <Link href={`/vocab/${encodeURIComponent(v.word)}`} className="kd-vocab-word kd-vocab-link">{v.word}</Link>
                              <span className="kd-vocab-reading">
                                {v.reading || "\u2013"}
                                {v.jlpt_level && (
                                  <span className={`jb jb-sm ${jlptBadgeClass[v.jlpt_level.toLowerCase()] || ""}`}>
                                    {v.jlpt_level}
                                  </span>
                                )}
                              </span>
                              <span className="kd-vocab-meaning">{v.meaning || "\u2013"}</span>
                              {breakdownParts.length >= 2 && (
                                <span className="kd-vocab-breakdown">{breakdownParts.join(" + ")}</span>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                    {selectedVocab.size > 0 && (
                      <div className="kd-vocab-actions">
                        <button
                          className="kd-btn-study"
                          onClick={async () => {
                            setStudyMsg(null);
                            try {
                              const res = await fetch("/api/v1/kanji/vocab/add-to-study", {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({ kanji_vocab_ids: [...selectedVocab] }),
                              });
                              if (!res.ok) throw new Error("Lỗi");
                              const result = await res.json();
                              setStudyMsg(`Đã thêm ${result.added} từ${result.already ? `, ${result.already} từ đã có` : ""}`);
                              setSelectedVocab(new Set());
                            } catch {
                              setStudyMsg("Có lỗi xảy ra. Vui lòng đăng nhập.");
                            }
                          }}
                        >
                          📚 Thêm {selectedVocab.size} từ vào học
                        </button>
                        <button
                          className="kd-btn-remove"
                          onClick={async () => {
                            setStudyMsg(null);
                            try {
                              const res = await fetch("/api/v1/kanji/vocab/remove-from-study", {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({ kanji_vocab_ids: [...selectedVocab] }),
                              });
                              if (!res.ok) throw new Error("Lỗi");
                              const result = await res.json();
                              setStudyMsg(`🗑️ Đã xóa ${result.removed} từ khỏi bộ học`);
                              setSelectedVocab(new Set());
                            } catch {
                              setStudyMsg("Có lỗi xảy ra. Vui lòng đăng nhập.");
                            }
                          }}
                        >
                          🗑️ Xóa {selectedVocab.size} từ
                        </button>
                      </div>
                    )}
                    {studyMsg && <p className="kd-study-msg">{studyMsg}</p>}
                  </>
                ) : (
                  <p className="kd-vocab-empty">Chưa có từ vựng nào.</p>
                )}
              </div>
            </div>
          </div>

          {/* ── Navigation bar ── */}
          {(prev_kanji || next_kanji) && (
            <div className="kd-nav">
              {prev_kanji ? (
                <Link href={`/kanji/${encodeURIComponent(prev_kanji.char)}`} className="kd-nav-btn">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 19l-7-7 7-7" />
                  </svg>
                  <span className="kd-nav-char">{prev_kanji.char}</span>
                  <span className="kd-nav-label">{prev_kanji.sino_vi}</span>
                </Link>
              ) : <span />}
              {next_kanji ? (
                <Link href={`/kanji/${encodeURIComponent(next_kanji.char)}`} className="kd-nav-btn kd-nav-next">
                  <span className="kd-nav-label">{next_kanji.sino_vi}</span>
                  <span className="kd-nav-char">{next_kanji.char}</span>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
                  </svg>
                </Link>
              ) : <span />}
            </div>
          )}
        </div>
      </div>

      
    </>
  );
}
