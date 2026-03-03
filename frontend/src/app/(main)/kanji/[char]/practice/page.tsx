"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import Script from "next/script";
import "./practice.css";

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
  jlpt_level: string;
}

interface KanjiProgress {
  status: string;
  correct_streak: number;
  mastered: boolean;
}

interface KanjiDetail {
  kanji: KanjiData;
  progress: KanjiProgress | null;
}

/* eslint-disable @typescript-eslint/no-explicit-any */
declare const HanziWriter: any;

const MASTERED_THRESHOLD = 5;
const CANVAS_SIZE = 300;

const jlptBadge: Record<string, string> = {
  n5: "jlpt-n5", n4: "jlpt-n4", n3: "jlpt-n3", n2: "jlpt-n2", n1: "jlpt-n1",
};

export default function KanjiPracticePage() {
  const params = useParams();
  const char = decodeURIComponent(params.char as string);

  const [data, setData] = useState<KanjiDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [progress, setProgress] = useState<KanjiProgress | null>(null);
  const [scriptReady, setScriptReady] = useState(false);
  const [mode, setMode] = useState<"view" | "quiz">("view");
  const [feedback, setFeedback] = useState<{ type: string; html: string } | null>(null);
  const writerRef = useRef<any>(null);

  /* ── Fetch data ── */
  useEffect(() => {
    fetch(`/api/v1/kanji/${encodeURIComponent(char)}`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d: KanjiDetail) => {
        setData(d);
        setProgress(d.progress);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [char]);

  /* ── CDN data loader with fallback ── */
  const charDataLoader = useCallback((ch: string, onLoad: (d: any) => void, onError: (e: Error) => void) => {
    fetch(`https://cdn.jsdelivr.net/npm/hanzi-writer-data-jp/${ch}.json`)
      .then((r) => (r.ok ? r.json() : Promise.reject("not-found")))
      .then(onLoad)
      .catch(() => {
        fetch(`https://cdn.jsdelivr.net/npm/hanzi-writer-data/${ch}.json`)
          .then((r) => (r.ok ? r.json() : Promise.reject("not-found")))
          .then(onLoad)
          .catch(onError);
      });
  }, []);

  /* ── Init HanziWriter ── */
  useEffect(() => {
    if (!scriptReady || !data) return;
    const loadingEl = document.getElementById("writer-loading");

    writerRef.current = HanziWriter.create("writer-target", char, {
      width: CANVAS_SIZE,
      height: CANVAS_SIZE,
      padding: 18,
      showOutline: true,
      strokeColor: "#1e293b",
      outlineColor: "#e2e8f0",
      highlightColor: "#6366f1",
      drawingColor: "#10b981",
      drawingWidth: 22,
      strokeAnimationSpeed: 0.8,
      delayBetweenStrokes: 500,
      charDataLoader,
      onLoadCharDataSuccess: () => {
        if (loadingEl) loadingEl.style.display = "none";
      },
      onLoadCharDataError: () => {
        if (loadingEl) loadingEl.style.display = "none";
        setFeedback({ type: "error", html: "⚠️ Không thể tải dữ liệu Hán tự." });
      },
    });

    return () => {
      writerRef.current = null;
    };
  }, [scriptReady, data, char, charDataLoader]);

  /* ── Record progress ── */
  const recordProgress = useCallback(async (passed: boolean) => {
    if (!data) return;
    try {
      const res = await fetch("/api/v1/kanji/progress", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ kanji_id: data.kanji.id, passed }),
      });
      if (res.ok) {
        const d = await res.json();
        setProgress(d);
        if (d.mastered) {
          setFeedback({ type: "success", html: "⭐ <strong>Đã thuộc!</strong> Bạn đã viết đúng 5 lần liên tiếp." });
        }
      }
    } catch (e) {
      console.error("[KanjiWriter] Progress update failed:", e);
    }
  }, [data]);

  /* ── Button handlers ── */
  const handleAnimate = () => {
    if (!writerRef.current) return;
    setFeedback(null);
    setMode("view");
    writerRef.current.animateCharacter({
      onComplete: () => {
        setFeedback({ type: "info", html: "▶ Hoàn tất! Nhấn <strong>Tự viết</strong> để luyện tập." });
      },
    });
  };

  const handleQuiz = () => {
    if (!writerRef.current) return;
    setFeedback(null);
    setMode("quiz");
    setFeedback({ type: "info", html: "✏️ <strong>Hãy viết từng nét theo thứ tự đúng.</strong> Dưới 3 lỗi sẽ được tính điểm." });

    writerRef.current.quiz({
      showHintAfterMisses: 3,
      markStrokeCorrectAfterMisses: 5,
      onMistake: () => {
        if (navigator.vibrate) navigator.vibrate(80);
      },
      onComplete: (summaryData: { totalMistakes: number }) => {
        const passed = summaryData.totalMistakes < 3;
        setMode("view");
        if (passed) {
          setFeedback({
            type: "success",
            html: `✅ <strong>Xuất sắc!</strong> ${summaryData.totalMistakes} lỗi — đã ghi nhận tiến trình.`,
          });
        } else {
          setFeedback({
            type: "error",
            html: `❌ <strong>${summaryData.totalMistakes} lỗi</strong> — cần luyện thêm. Hãy thử lại!`,
          });
        }
        recordProgress(passed);
      },
    });
  };

  const handleReset = () => {
    if (!writerRef.current) return;
    setFeedback(null);
    setMode("view");
    writerRef.current.setCharacter(char);
  };

  if (loading) {
    return <div className="kp-page px-4 py-8"><div className="max-w-5xl mx-auto text-center py-20" style={{ color: "var(--text-tertiary)" }}>Đang tải...</div></div>;
  }
  if (!data) {
    return <div className="kp-page px-4 py-8"><div className="max-w-5xl mx-auto text-center py-20" style={{ color: "var(--status-error)" }}>Không tìm thấy: {char}</div></div>;
  }

  const { kanji } = data;
  const badge = jlptBadge[kanji.jlpt_level?.toLowerCase()] || "";

  return (
    <>
      <Script
        src="https://cdn.jsdelivr.net/npm/hanzi-writer@3.5.0/dist/hanzi-writer.min.js"
        onLoad={() => setScriptReady(true)}
        strategy="afterInteractive"
      />

      <div className="kp-page px-4 py-8 md:py-12">
        <div className="max-w-5xl mx-auto">

          {/* Breadcrumb */}
          <nav className="mb-6 flex items-center gap-2 text-sm" style={{ color: "var(--text-tertiary)" }}>
            <Link href="/kanji" className="hover:text-indigo-600 transition-colors">Hán tự</Link>
            <ChevronIcon />
            <Link href={`/kanji/${encodeURIComponent(char)}`} className="hover:text-indigo-600 transition-colors font-mono">{char}</Link>
            <ChevronIcon />
            <span className="font-medium" style={{ color: "var(--text-primary)" }}>Luyện viết</span>
          </nav>

          {/* Title */}
          <div className="mb-8">
            <h1 className="text-2xl font-extrabold" style={{ color: "var(--text-primary)" }}>
              Luyện viết Hán tự{" "}
              <span className="ml-2" style={{ fontFamily: "'Noto Sans JP',sans-serif", color: "var(--action-primary, #6366f1)" }}>
                {kanji.char}
              </span>
            </h1>
            <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>
              Xem mẫu hoặc tự viết theo từng nét — hệ thống tự động ghi nhận tiến trình.
            </p>
          </div>

          {/* Grid: info + writing */}
          <div className="grid md:grid-cols-[280px,1fr] gap-6 items-start">

            {/* LEFT: Info card */}
            <div className="kp-glass p-6 flex flex-col items-center text-center gap-4">
              <div className="relative">
                <div className="kp-char-display select-none">{kanji.char}</div>
                {kanji.jlpt_level && (
                  <span className={`jlpt-badge ${badge} absolute -top-2 -right-2`}>
                    {kanji.jlpt_level.toUpperCase()}
                  </span>
                )}
              </div>

              {kanji.keyword && (
                <div>
                  <p className="text-xs uppercase tracking-wider mb-0.5" style={{ color: "var(--text-tertiary)" }}>Keyword</p>
                  <p className="text-base font-bold" style={{ color: "var(--text-primary)" }}>{kanji.keyword}</p>
                </div>
              )}

              {kanji.sino_vi && (
                <div>
                  <p className="text-xs uppercase tracking-wider mb-0.5" style={{ color: "var(--text-tertiary)" }}>Hán Việt</p>
                  <p className="text-sm font-semibold" style={{ color: "var(--text-secondary)", fontFamily: "'Noto Sans JP',sans-serif" }}>{kanji.sino_vi}</p>
                </div>
              )}

              {(kanji.onyomi || kanji.kunyomi) && (
                <div className="w-full border-t pt-4 space-y-2" style={{ borderColor: "var(--border-subtle)" }}>
                  {kanji.onyomi && (
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--text-tertiary)" }}>On-yomi</span>
                      <span style={{ fontFamily: "'Noto Sans JP',sans-serif", color: "var(--text-primary)" }}>{kanji.onyomi}</span>
                    </div>
                  )}
                  {kanji.kunyomi && (
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--text-tertiary)" }}>Kun-yomi</span>
                      <span style={{ fontFamily: "'Noto Sans JP',sans-serif", color: "var(--text-primary)" }}>{kanji.kunyomi}</span>
                    </div>
                  )}
                </div>
              )}

              {kanji.strokes && (
                <div className="flex items-center gap-2 text-sm" style={{ color: "var(--text-secondary)" }}>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                  </svg>
                  {kanji.strokes} nét
                </div>
              )}

              {/* Progress streak */}
              <div className="w-full border-t pt-4" style={{ borderColor: "var(--border-subtle)" }}>
                <p className="text-xs uppercase tracking-wider mb-2" style={{ color: "var(--text-tertiary)" }}>Tiến trình</p>
                <div className="flex justify-center gap-1.5 mb-2">
                  {[1, 2, 3, 4, 5].map((i) => (
                    <div
                      key={i}
                      className={`kp-streak-dot ${
                        progress?.mastered && i <= (progress?.correct_streak || 0) ? "mastered" :
                        i <= (progress?.correct_streak || 0) ? "filled" : ""
                      }`}
                    />
                  ))}
                </div>
                <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
                  {progress?.mastered ? (
                    <span style={{ color: "var(--action-accent)", fontWeight: 600 }}>Đã thuộc ✓</span>
                  ) : (
                    `${progress?.correct_streak || 0}/${MASTERED_THRESHOLD} chuỗi đúng`
                  )}
                </p>
              </div>

              {kanji.note && (
                <div className="w-full border-t pt-4 text-left" style={{ borderColor: "var(--border-subtle)" }}>
                  <p className="text-xs uppercase tracking-wider mb-1" style={{ color: "var(--text-tertiary)" }}>Mẹo nhớ</p>
                  <p className="text-xs leading-relaxed whitespace-pre-line" style={{ color: "var(--text-secondary)" }}>{kanji.note}</p>
                </div>
              )}
            </div>

            {/* RIGHT: Writing area */}
            <div className="kp-glass p-6 flex flex-col gap-5">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Bảng luyện viết</h2>
                <span className={`px-3 py-1 rounded-full border text-xs font-semibold ${
                  mode === "quiz"
                    ? "bg-emerald-50 border-emerald-200 text-emerald-700"
                    : "bg-indigo-50 border-indigo-200 text-indigo-700"
                }`}>
                  Chế độ: {mode === "quiz" ? "Tự viết" : "Xem mẫu"}
                </span>
              </div>

              {/* Canvas */}
              <div className="flex justify-center">
                <div className="kp-writing-grid" style={{ width: `${CANVAS_SIZE}px`, height: `${CANVAS_SIZE}px` }}>
                  <svg className="grid-overlay" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 300" aria-hidden="true">
                    <line x1="0" y1="0" x2="300" y2="300" stroke="rgba(203,213,225,.35)" strokeWidth="1" strokeDasharray="5 4" />
                    <line x1="300" y1="0" x2="0" y2="300" stroke="rgba(203,213,225,.35)" strokeWidth="1" strokeDasharray="5 4" />
                    <line x1="0" y1="150" x2="300" y2="150" stroke="rgba(148,163,184,.6)" strokeWidth="1" strokeDasharray="5 4" />
                    <line x1="150" y1="0" x2="150" y2="300" stroke="rgba(148,163,184,.6)" strokeWidth="1" strokeDasharray="5 4" />
                  </svg>

                  <div id="writer-loading" className="absolute inset-0 flex flex-col items-center justify-center gap-3 z-10" style={{ borderRadius: "14px", background: "rgba(248,250,252,.9)" }}>
                    <div className="kp-loading-shimmer w-32 h-32 rounded-2xl" />
                    <p className="text-xs" style={{ color: "var(--text-tertiary)" }}>Đang tải dữ liệu Hán tự…</p>
                  </div>

                  <div id="writer-target" />
                </div>
              </div>

              {/* Controls */}
              <div className="flex flex-wrap items-center justify-center gap-3">
                <button onClick={handleAnimate} className="kp-btn kp-btn-animate">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Xem mẫu
                </button>
                <button onClick={handleQuiz} className="kp-btn kp-btn-quiz">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                  </svg>
                  Tự viết (Quiz)
                </button>
                <button onClick={handleReset} className="kp-btn kp-btn-reset">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Xóa
                </button>
              </div>

              {/* Feedback */}
              {feedback && (
                <div className={`kp-feedback kp-feedback-${feedback.type}`} dangerouslySetInnerHTML={{ __html: feedback.html }} />
              )}

              {/* Hint */}
              <p className="text-xs text-center leading-relaxed" style={{ color: "var(--text-tertiary)" }}>
                Nhấn <strong style={{ color: "#6366f1" }}>Xem mẫu</strong> để xem thứ tự nét &nbsp;·&nbsp;
                Nhấn <strong style={{ color: "#059669" }}>Tự viết</strong> để luyện tập &nbsp;·&nbsp;
                Quiz yêu cầu ít hơn 3 lỗi để tính điểm.
              </p>
            </div>
          </div>
        </div>
      </div>

      
    </>
  );
}

function ChevronIcon() {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
    </svg>
  );
}
