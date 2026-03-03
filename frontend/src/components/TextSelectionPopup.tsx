"use client";

/**
 * TextSelectionPopup — floating popup on text selection.
 * Shows explain + save buttons with modern glassmorphism UI.
 * Performance: lazy state, useCallback, conditional rendering.
 */

import { useState, useEffect, useRef, useCallback, memo } from "react";
import s from "./TextSelectionPopup.module.css";

interface PopupState {
  visible: boolean;
  x: number;
  y: number;
  word: string;
}

interface SynAntItem {
  word: string;
  reading?: string;
  meaning?: string;
}

interface ExplainResult {
  word: string;
  reading?: string;
  han_viet?: string;
  meaning_vi?: string;
  jlpt_level?: string;
  english_origin?: string;
  collocation?: string;
  synonyms?: SynAntItem[];
  antonyms?: SynAntItem[];
  source?: string;
  error?: string;
}

interface Props {
  contextSentence?: string;
  children: React.ReactNode;
}

const INITIAL_POPUP: PopupState = { visible: false, x: 0, y: 0, word: "" };

export default memo(function TextSelectionPopup({ contextSentence = "", children }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const popupRef = useRef<HTMLDivElement>(null);
  const [popup, setPopup] = useState<PopupState>(INITIAL_POPUP);
  const [explain, setExplain] = useState<ExplainResult | null>(null);
  const [explaining, setExplaining] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [tabIdx, setTabIdx] = useState(0);

  const hidePopup = useCallback(() => {
    setPopup(INITIAL_POPUP);
    setExplain(null);
    setSaved(false);
    setTabIdx(0);
  }, []);

  // Listen for text selection
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const handleMouseUp = () => {
      setTimeout(async () => {
        const sel = window.getSelection();
        const text = sel?.toString().trim();
        if (!text || text.length < 1 || text.length > 30 || text.includes("\n")) return;

        if (sel?.anchorNode && container.contains(sel.anchorNode)) {
          const range = sel.getRangeAt(0);
          const rect = range.getBoundingClientRect();
          const cr = container.getBoundingClientRect();

          setExplain(null);
          setSaved(false);
          setPopup({
            visible: true,
            x: rect.left - cr.left + rect.width / 2,
            y: rect.bottom - cr.top + 8,
            word: text,
          });

          // Auto-explain immediately
          setExplaining(true);
          try {
            const r = await fetch("/api/v1/vocab/explain-in-context", {
              method: "POST", credentials: "include",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ word: text, context_sentence: contextSentence, language: "jp" }),
            });
            const data = await r.json();
            setExplain(data);
          } catch {
            setExplain({ word: text, error: "Lỗi kết nối" });
          }
          setExplaining(false);
        }
      }, 10);
    };

    container.addEventListener("mouseup", handleMouseUp);
    return () => container.removeEventListener("mouseup", handleMouseUp);
  }, []);

  // Hide on click outside
  useEffect(() => {
    if (!popup.visible) return;
    const handle = (e: MouseEvent) => {
      if (popupRef.current && !popupRef.current.contains(e.target as Node)) hidePopup();
    };
    const t = setTimeout(() => document.addEventListener("mousedown", handle), 50);
    return () => { clearTimeout(t); document.removeEventListener("mousedown", handle); };
  }, [popup.visible, hidePopup]);

  const fetchExplain = useCallback(async (word: string): Promise<ExplainResult> => {
    try {
      const r = await fetch("/api/v1/vocab/explain-in-context", {
        method: "POST", credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ word, context_sentence: contextSentence, language: "jp" }),
      });
      return await r.json();
    } catch {
      return { word, error: "Lỗi kết nối" };
    }
  }, [contextSentence]);

  const handleExplain = useCallback(async () => {
    setExplaining(true);
    const data = await fetchExplain(popup.word);
    setExplain(data);
    setExplaining(false);
  }, [popup.word, fetchExplain]);

  const handleSave = useCallback(async () => {
    setSaving(true);
    try {
      let info = explain;
      if (!info || !info.meaning_vi) {
        setExplaining(true);
        info = await fetchExplain(popup.word);
        setExplain(info);
        setExplaining(false);
      }
      await fetch("/api/v1/vocab/save-highlight", {
        method: "POST", credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          word: info?.word || popup.word,
          context_sentence: contextSentence,
          meaning_vi: info?.meaning_vi || "",
          reading: info?.reading || "",
          han_viet: info?.han_viet || "",
          language: "jp",
        }),
      });
      setSaved(true);
    } catch { /* ignore */ }
    setSaving(false);
  }, [explain, popup.word, contextSentence, fetchExplain]);

  return (
    <div ref={containerRef} style={{ position: "relative" }}>
      {children}

      {popup.visible && (
        <div
          ref={popupRef}
          className={s.popup}
          style={{
            position: "absolute",
            left: popup.x,
            top: popup.y,
            transform: "translateX(-50%)",
            zIndex: 999,
          }}
        >
          {/* Header: word with furigana + close */}
          <div className={s.header}>
            <span className={s.word}>
              {explain?.word ? (
                <ruby>{explain.word}<rp>(</rp><rt>{explain.reading || ""}</rt><rp>)</rp></ruby>
              ) : popup.word}
            </span>
            <button className={s.close} onClick={hidePopup} aria-label="Đóng">×</button>
          </div>

          {/* Explain result */}
          {explain && !explain.error && (
            <div className={s.result}>
              {/* Tab bar */}
              <div className={s.tabs}>
                {["意味", "類語", "連語"].map((label, i) => (
                  <button key={i} className={`${s.tab} ${tabIdx === i ? s.tabActive : ""}`} onClick={() => setTabIdx(i)}>{label}</button>
                ))}
              </div>

              {/* Tab 1: Meaning */}
              {tabIdx === 0 && (
                <div className={s.tabContent}>
                  <div className={s.resultTop}>
                    {explain.han_viet && <span className={s.hanviet}>{explain.han_viet}</span>}
                    {explain.jlpt_level && <span className={s.jlpt}>{explain.jlpt_level}</span>}
                    {explain.english_origin && <span className={s.eng}>{explain.english_origin}</span>}
                    {explain.source && (
                      <span className={`${s.badge} ${explain.source === "db" ? s.badgeDb : s.badgeAi}`}>
                        {explain.source === "db" ? "DB" : "AI"}
                      </span>
                    )}
                  </div>
                  {explain.meaning_vi && <div className={s.meaning}>{explain.meaning_vi}</div>}
                </div>
              )}

              {/* Tab 2: Synonyms & Antonyms */}
              {tabIdx === 1 && (
                <div className={s.tabContent}>
                  {explain.synonyms && explain.synonyms.length > 0 && (
                    <div className={s.synSection}>
                      <div className={s.synLabel}>đồng nghĩa</div>
                      {explain.synonyms.map((syn, i) => (
                        <div key={i} className={s.synItem}>
                          <span className={s.synWord}>
                            {syn.reading ? <ruby>{syn.word}<rp>(</rp><rt>{syn.reading}</rt><rp>)</rp></ruby> : syn.word}
                          </span>
                          {syn.meaning && <span className={s.synMeaning}>{syn.meaning}</span>}
                        </div>
                      ))}
                    </div>
                  )}
                  {explain.antonyms && explain.antonyms.length > 0 && (
                    <div className={s.synSection}>
                      <div className={`${s.synLabel} ${s.synLabelAnt}`}>trái nghĩa</div>
                      {explain.antonyms.map((ant, i) => (
                        <div key={i} className={s.synItem}>
                          <span className={s.synWord}>
                            {ant.reading ? <ruby>{ant.word}<rp>(</rp><rt>{ant.reading}</rt><rp>)</rp></ruby> : ant.word}
                          </span>
                          {ant.meaning && <span className={s.synMeaning}>{ant.meaning}</span>}
                        </div>
                      ))}
                    </div>
                  )}
                  {(!explain.synonyms || explain.synonyms.length === 0) && (!explain.antonyms || explain.antonyms.length === 0) && (
                    <div className={s.empty}>Không có dữ liệu</div>
                  )}
                </div>
              )}

              {/* Tab 3: Collocations */}
              {tabIdx === 2 && (
                <div className={s.tabContent}>
                  {explain.collocation ? (
                    <div className={s.collocation}>{explain.collocation}</div>
                  ) : (
                    <div className={s.empty}>Không có dữ liệu</div>
                  )}
                </div>
              )}
            </div>
          )}
          {explain?.error && <div className={s.error}>{explain.error}</div>}

          {/* Actions */}
          <div className={s.actions}>
            <button className={`${s.btn} ${s.btnExplain}`} onClick={handleExplain} disabled={explaining}>
              {explaining ? (
                <span className={s.spinner} />
              ) : (
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3"/><path d="M12 17h.01"/></svg>
              )}
              {explaining ? "Đang tra..." : "Tra từ"}
            </button>
            <button
              className={`${s.btn} ${s.btnSave} ${saved ? s.btnSaved : ""}`}
              onClick={handleSave}
              disabled={saving || saved || explaining}
            >
              {saved ? (
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6L9 17l-5-5"/></svg>
              ) : saving ? (
                <span className={`${s.spinner} ${s.spinnerSave}`} />
              ) : (
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z"/><path d="M17 21v-8H7v8"/><path d="M7 3v5h8"/></svg>
              )}
              {saved ? "Đã lưu" : saving ? "Lưu..." : "Lưu từ"}
            </button>
          </div>

          <div className={s.arrow} />
        </div>
      )}
    </div>
  );
});
