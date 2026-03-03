"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

interface DokkaiChoice {
  key: string;
  text_html: string;
}

interface DokkaiQuestion {
  id: number;
  text_html: string;
  choices: DokkaiChoice[];
  correct_answer: string;
  explanation_json: Record<string, unknown>;
}

interface BilingualSentence {
  japanese_sentence: string;
  vietnamese_translation: string;
  vocabulary?: { kanji: string; hiragana: string; meaning: string }[];
}

interface VocabItem {
  word: string;
  reading: string;
  han_viet?: string;
  meaning_vi: string;
  type?: string;
}

interface DokkaiPassage {
  title: string;
  text_html: string;
  image_url: string;
  bilingual_reading: BilingualSentence[];
  vocabulary: VocabItem[];
}

interface DokkaiData {
  title: string;
  level: string;
  reading_format: string;
  total_count: number;
  passages: DokkaiPassage[];
  questions: DokkaiQuestion[];
}

/* ── Styles ─────────────────────────────────────────────── */
const S = {
  page: {
    padding: "16px 16px 40px",
    minHeight: "100vh",
  } as React.CSSProperties,
  breadcrumb: {
    display: "flex",
    alignItems: "center",
    gap: 6,
    fontSize: 12,
    color: "var(--text-tertiary)",
    marginBottom: 12,
  } as React.CSSProperties,
  headerBar: {
    display: "flex",
    alignItems: "center",
    gap: 10,
    padding: "10px 14px",
    borderRadius: 12,
    background: "var(--bg-surface)",
    border: "1px solid var(--border-default)",
    marginBottom: 12,
  } as React.CSSProperties,
  badge: (bg: string, color: string) => ({
    fontSize: 11,
    fontWeight: 700,
    padding: "2px 8px",
    borderRadius: 20,
    background: bg,
    color,
    whiteSpace: "nowrap",
  }) as React.CSSProperties,
  scorePanel: {
    padding: "14px 16px",
    borderRadius: 14,
    background: "linear-gradient(135deg, rgba(99,102,241,.06), rgba(139,92,246,.06))",
    border: "1px solid var(--border-default)",
    marginBottom: 12,
    textAlign: "center",
  } as React.CSSProperties,
  grid: {
    display: "grid",
    gridTemplateColumns: "1fr",
    gap: 12,
  } as React.CSSProperties,
  card: {
    padding: "12px 14px",
    borderRadius: 14,
    background: "var(--bg-surface)",
    border: "1px solid var(--border-default)",
  } as React.CSSProperties,
  cardLabel: {
    display: "flex",
    alignItems: "center",
    gap: 6,
    fontSize: 12,
    fontWeight: 600,
    color: "var(--text-secondary)",
    marginBottom: 8,
  } as React.CSSProperties,
  passageText: {
    fontSize: 14,
    lineHeight: 2,
    fontFamily: "'Noto Sans JP', sans-serif",
    color: "var(--text-primary)",
  } as React.CSSProperties,
  submitBar: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "8px 14px",
    borderRadius: 12,
    background: "var(--bg-surface)",
    border: "1px solid var(--border-default)",
  } as React.CSSProperties,
  submitBtn: {
    display: "inline-flex",
    alignItems: "center",
    gap: 6,
    padding: "7px 18px",
    borderRadius: 10,
    fontSize: 13,
    fontWeight: 600,
    color: "#fff",
    background: "linear-gradient(135deg, #6366f1, #8b5cf6)",
    border: "none",
    cursor: "pointer",
  } as React.CSSProperties,
  qCard: {
    padding: "10px 14px",
    borderRadius: 14,
    background: "var(--bg-surface)",
    border: "1px solid var(--border-default)",
  } as React.CSSProperties,
  qHeader: {
    display: "flex",
    alignItems: "flex-start",
    gap: 8,
    marginBottom: 8,
  } as React.CSSProperties,
  qNum: {
    fontSize: 11,
    fontWeight: 700,
    padding: "1px 7px",
    borderRadius: 6,
    background: "var(--bg-interactive)",
    color: "var(--text-secondary)",
    flexShrink: 0,
    lineHeight: "20px",
  } as React.CSSProperties,
  qText: {
    fontSize: 14,
    fontFamily: "'Noto Sans JP', sans-serif",
    color: "var(--text-primary)",
    flex: 1,
  } as React.CSSProperties,
  choiceBtn: (selected: boolean, isCorrect: boolean, isWrong: boolean, dimmed: boolean) => ({
    display: "flex",
    alignItems: "center",
    gap: 8,
    width: "100%",
    textAlign: "left" as const,
    padding: "7px 10px",
    borderRadius: 10,
    border: `1.5px solid ${isCorrect ? "#34d399" : isWrong ? "#f87171" : selected ? "var(--action-primary)" : "var(--border-default)"}`,
    background: isCorrect ? "rgba(209,250,229,.6)" : isWrong ? "rgba(254,226,226,.6)" : selected ? "var(--bg-interactive)" : "transparent",
    cursor: dimmed ? "default" : "pointer",
    opacity: dimmed ? 0.45 : 1,
    transition: "all .15s",
    outline: "none",
  }) as React.CSSProperties,
  choiceKey: {
    width: 22,
    height: 22,
    borderRadius: "50%",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: 10,
    fontWeight: 700,
    background: "var(--bg-app-subtle)",
    color: "var(--text-secondary)",
    flexShrink: 0,
  } as React.CSSProperties,
  choiceText: {
    fontSize: 14,
    fontFamily: "'Noto Sans JP', sans-serif",
  } as React.CSSProperties,
  toggleBtn: (color: string) => ({
    display: "flex",
    alignItems: "center",
    gap: 6,
    width: "100%",
    padding: "8px 14px",
    borderRadius: 12,
    border: "1px solid var(--border-default)",
    background: "var(--bg-surface)",
    cursor: "pointer",
    fontSize: 13,
    fontWeight: 600,
    color,
    outline: "none",
  }) as React.CSSProperties,
};

export default function DokkaiPracticePage() {
  const params = useParams();
  const slug = params.slug as string;

  const [data, setData] = useState<DokkaiData | null>(null);
  const [loading, setLoading] = useState(true);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [results, setResults] = useState<Record<number, { is_correct: boolean; explanation_json: Record<string, unknown> }>>({});
  const [showExplanations, setShowExplanations] = useState<Record<number, boolean>>({});
  const [showBilingual, setShowBilingual] = useState(false);
  const [showVocab, setShowVocab] = useState(false);

  useEffect(() => {
    fetch(`/api/v1/exam/dokkai/${slug}`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d: DokkaiData) => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, [slug]);

  const answeredCount = Object.keys(answers).length;
  const correctCount = Object.values(results).filter((r) => r.is_correct).length;
  const totalCount = data?.total_count || data?.questions?.length || 0;
  const scorePct = totalCount > 0 ? Math.round((correctCount / totalCount) * 100) : 0;

  const selectAnswer = (qId: number, key: string) => {
    if (submitted) return;
    setAnswers((prev) => ({ ...prev, [qId]: key }));
  };

  const submit = useCallback(async () => {
    if (!data || submitting) return;
    setSubmitting(true);
    try {
      const newResults: Record<number, { is_correct: boolean; explanation_json: Record<string, unknown> }> = {};
      for (const q of data.questions) {
        const selected = answers[q.id] || "";
        const isCorrect = selected === q.correct_answer;
        newResults[q.id] = { is_correct: isCorrect, explanation_json: q.explanation_json || {} };
      }
      setResults(newResults);
      setSubmitted(true);

      fetch(`/exam/dokkai/${slug}/submit/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ answers }),
      }).catch(() => {});
    } catch (e) {
      console.error("Submit failed:", e);
    }
    setSubmitting(false);
  }, [data, slug, answers, submitting]);

  const rating = scorePct >= 90 ? "🎉 Xuất sắc!" : scorePct >= 70 ? "👏 Tốt lắm!" : scorePct >= 50 ? "💪 Khá!" : "📖 Hãy ôn lại!";

  const allBilingual = data?.passages?.flatMap((p) => p.bilingual_reading || []) || [];
  const allVocab = data?.passages?.flatMap((p) => p.vocabulary || []) || [];

  if (loading) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Đang tải...</div>;
  if (!data) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Không tìm thấy bài đọc.</div>;

  return (
    <div style={S.page}>
      <div style={{ maxWidth: 960, margin: "0 auto" }}>
        {/* Breadcrumb */}
        <nav style={S.breadcrumb}>
          <Link href="/exam" style={{ color: "inherit" }}>Luyện thi</Link>
          <span>/</span>
          <Link href="/exam/dokkai" style={{ color: "inherit" }}>Dokkai</Link>
          <span>/</span>
          <span style={{ color: "var(--text-primary)" }}>{data.title}</span>
        </nav>

        {/* Compact Header */}
        <div style={S.headerBar}>
          <span style={{ fontSize: 16, fontWeight: 700, flex: 1, color: "var(--text-primary)", fontFamily: "'Noto Sans JP', sans-serif" }}>{data.title}</span>
          {data.level && <span style={S.badge("rgba(16,185,129,.1)", "#059669")}>{data.level}</span>}
          {data.reading_format && <span style={{ fontSize: 11, color: "var(--text-tertiary)" }}>{data.reading_format}</span>}
          <span style={{ fontSize: 11, color: "var(--text-tertiary)" }}>{totalCount} câu</span>
        </div>

        {/* Score Panel */}
        {submitted && (
          <div style={S.scorePanel as React.CSSProperties}>
            <div style={{ fontSize: 28, fontWeight: 800, color: "var(--text-primary)", marginBottom: 2 }}>{scorePct}%</div>
            <div style={{ fontSize: 12, color: "var(--text-secondary)", marginBottom: 6 }}>{correctCount} / {totalCount} câu đúng</div>
            <div style={{ height: 5, borderRadius: 10, background: "var(--border-default)", maxWidth: 200, margin: "0 auto 6px", overflow: "hidden" }}>
              <div style={{ height: "100%", borderRadius: 10, width: `${scorePct}%`, background: scorePct >= 70 ? "#10b981" : "#f59e0b" }} />
            </div>
            <div style={{ fontSize: 14 }}>{rating}</div>
          </div>
        )}

        {/* Two-column on desktop */}
        <div style={{ ...S.grid, gridTemplateColumns: "1fr" }} className="dokkai-grid">
          {/* Passages Column */}
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {data.passages?.map((p, i) => (
              <div key={i} style={S.card}>
                <div style={S.cardLabel}>
                  <svg style={{ width: 14, height: 14 }} fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" /><polyline points="14 2 14 8 20 8" /></svg>
                  {p.title || "Bài đọc"}
                </div>
                {p.image_url && <img src={p.image_url} alt="" style={{ borderRadius: 10, marginBottom: 8, maxWidth: "100%" }} />}
                {p.text_html && <div style={S.passageText} dangerouslySetInnerHTML={{ __html: p.text_html }} />}
              </div>
            ))}

            {/* Bilingual Toggle */}
            {allBilingual.length > 0 && (
              <div>
                <button onClick={() => setShowBilingual(!showBilingual)} style={S.toggleBtn("#6366f1")}>
                  <span>🌐</span>
                  <span>{showBilingual ? "Ẩn bản dịch song ngữ" : "Xem bản dịch song ngữ"}</span>
                  <svg style={{ width: 14, height: 14, marginLeft: "auto", transition: "transform .2s", transform: showBilingual ? "rotate(180deg)" : "none" }} fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M19 9l-7 7-7-7"/></svg>
                </button>
                {showBilingual && (
                  <div style={{ display: "flex", flexDirection: "column", gap: 6, marginTop: 8 }}>
                    {allBilingual.map((s, idx) => (
                      <div key={idx} style={{ padding: "8px 10px", borderRadius: 10, background: "var(--bg-interactive)", border: "1px solid var(--border-default)" }}>
                        <div style={{ fontSize: 13, fontFamily: "'Noto Sans JP', sans-serif", color: "var(--text-primary)", lineHeight: 1.8 }} dangerouslySetInnerHTML={{ __html: s.japanese_sentence }} />
                        <div style={{ fontSize: 11, color: "#6366f1", fontStyle: "italic", marginTop: 2 }}>{s.vietnamese_translation}</div>
                        {s.vocabulary && s.vocabulary.length > 0 && (
                          <div style={{ display: "flex", flexWrap: "wrap", gap: 4, marginTop: 4 }}>
                            {s.vocabulary.map((v, vi) => (
                              <span key={vi} style={{ fontSize: 10, padding: "1px 5px", borderRadius: 4, background: "rgba(16,185,129,.08)", color: "#059669" }}>
                                {v.kanji}({v.hiragana}) {v.meaning}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Vocabulary Toggle */}
            {allVocab.length > 0 && (
              <div>
                <button onClick={() => setShowVocab(!showVocab)} style={S.toggleBtn("var(--text-secondary)")}>
                  <span>📝</span>
                  <span>{showVocab ? "Ẩn từ vựng" : `Xem từ vựng (${allVocab.length} từ)`}</span>
                  <svg style={{ width: 14, height: 14, marginLeft: "auto", transition: "transform .2s", transform: showVocab ? "rotate(180deg)" : "none" }} fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M19 9l-7 7-7-7"/></svg>
                </button>
                {showVocab && (
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6, marginTop: 8 }}>
                    {allVocab.map((v, idx) => {
                      const hasKanji = v.word && /[\u4e00-\u9faf\u3400-\u4dbf]/.test(v.word);
                      const rubyHtml = hasKanji && v.reading
                        ? `<ruby>${v.word}<rp>(</rp><rt>${v.reading}</rt><rp>)</rp></ruby>`
                        : v.word;

                      return (
                        <div key={idx} style={{
                          padding: "8px 10px",
                          borderRadius: 10,
                          background: "var(--bg-surface)",
                          border: "1px solid var(--border-default)",
                        }}>
                          {/* Row: Kanji (furigana) + Han Viet */}
                          <div style={{ display: "flex", alignItems: "baseline", gap: 6 }}>
                            <span
                              style={{ fontSize: 17, fontWeight: 700, fontFamily: "'Noto Sans JP', sans-serif", color: "var(--text-primary)", lineHeight: 1.6 }}
                              dangerouslySetInnerHTML={{ __html: rubyHtml }}
                            />
                            {v.han_viet && (
                              <span style={{ fontSize: 12, color: "var(--text-tertiary)", fontWeight: 500 }}>{v.han_viet}</span>
                            )}
                          </div>
                          {/* Meaning */}
                          <div style={{ fontSize: 13, color: "var(--text-secondary)", marginTop: 2 }}>{v.meaning_vi}</div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Questions Column */}
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {/* Submit Bar */}
            {!submitted && (
              <div style={S.submitBar}>
                <button onClick={submit} disabled={submitting} style={{ ...S.submitBtn, opacity: submitting ? 0.6 : 1 }}>
                  {submitting ? "Đang nộp..." : "Nộp bài"}
                </button>
                <span style={{ fontSize: 11, color: "var(--text-tertiary)" }}>Đã chọn: {answeredCount}/{totalCount}</span>
              </div>
            )}

            {data.questions?.map((q, i) => (
              <div key={q.id} style={S.qCard}>
                {/* Question header */}
                <div style={S.qHeader}>
                  <span style={S.qNum}>{i + 1}</span>
                  {q.text_html && <div style={S.qText} dangerouslySetInnerHTML={{ __html: q.text_html }} />}
                </div>

                {/* Choices */}
                <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
                  {q.choices?.map((c) => {
                    const selected = answers[q.id] === c.key;
                    const isCorrect = submitted && c.key === q.correct_answer;
                    const isWrong = submitted && selected && !isCorrect;
                    const dimmed = submitted && !isCorrect && !selected;
                    return (
                      <button
                        key={c.key}
                        onClick={() => selectAnswer(q.id, c.key)}
                        disabled={submitted}
                        style={S.choiceBtn(selected, isCorrect, isWrong, dimmed)}
                      >
                        <span style={S.choiceKey}>{c.key}</span>
                        <span style={S.choiceText} dangerouslySetInnerHTML={{ __html: c.text_html }} />
                      </button>
                    );
                  })}
                </div>

                {/* Feedback */}
                {submitted && results[q.id] && (
                  <div style={{ marginTop: 6 }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: results[q.id].is_correct ? "#16a34a" : "#dc2626" }}>
                      {results[q.id].is_correct ? "✅ Chính xác!" : `❌ Đáp án đúng: ${q.correct_answer}`}
                    </div>
                    {results[q.id].explanation_json && Object.keys(results[q.id].explanation_json).length > 0 && (
                      <>
                        <button
                          onClick={() => setShowExplanations((p) => ({ ...p, [q.id]: !p[q.id] }))}
                          style={{ fontSize: 11, marginTop: 4, color: "var(--action-primary)", background: "none", border: "none", cursor: "pointer", padding: 0, display: "flex", alignItems: "center", gap: 4 }}
                        >
                          {showExplanations[q.id] ? "▲ Ẩn giải thích" : "▼ Xem giải thích"}
                        </button>
                        {showExplanations[q.id] && (
                          <ExplanationPanel data={results[q.id].explanation_json} />
                        )}
                      </>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Responsive grid */}
      <style>{`
        @media (min-width: 768px) {
          .dokkai-grid {
            grid-template-columns: 1fr 1fr !important;
          }
        }
      `}</style>
    </div>
  );
}

/* Render structured explanation JSON */
function ExplanationPanel({ data }: { data: Record<string, unknown> }) {
  const summary = (data.overall_analysis as Record<string, string>)?.summary || "";
  const quote = (data.quote_from_passage as string) || "";
  const breakdown = data.options_breakdown as Record<string, { text?: string; status?: string; reason?: string }> | undefined;

  return (
    <div style={{ marginTop: 6, padding: "8px 10px", borderRadius: 10, fontSize: 12, background: "var(--bg-interactive)", color: "var(--text-primary)", lineHeight: 1.6 }}>
      {summary && <p style={{ margin: "0 0 6px" }}>{summary}</p>}
      {quote && (
        <div style={{ padding: "5px 8px", borderRadius: 8, background: "rgba(99,102,241,.06)", borderLeft: "3px solid #6366f1", marginBottom: 6 }}>
          <span style={{ color: "#6366f1", fontWeight: 600 }}>Trích dẫn: </span>
          <span style={{ fontFamily: "'Noto Sans JP', sans-serif" }}>{quote}</span>
        </div>
      )}
      {breakdown && Object.entries(breakdown).map(([key, val]) => (
        <div key={key} style={{ display: "flex", alignItems: "flex-start", gap: 6, marginBottom: 2 }}>
          <span style={{ fontWeight: 700, color: val.status === "correct" ? "#16a34a" : "#94a3b8", minWidth: 18 }}>{key}.</span>
          <span>{val.reason || val.text || ""}</span>
        </div>
      ))}
    </div>
  );
}
