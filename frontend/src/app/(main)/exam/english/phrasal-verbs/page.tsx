"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";

/* ─── TYPES ────────────────────────────────────────────── */
interface PhrasalVerb {
  id: number;
  verb: string;
  meaning: string;
  meaningEn: string;
  example: string;
  exampleVi: string;
  emoji: string;
}

interface FillSentence {
  sentence: string;
  answer: string;
  hint: string;
}

interface QuizQuestion {
  question: string;
  options: string[];
  correct: number;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

/* Module-level data (populated from API) */
let PHRASAL_VERBS: PhrasalVerb[] = [];
let FILL_SENTENCES: FillSentence[] = [];
let QUIZ_QUESTIONS: QuizQuestion[] = [];

type GameMode = "cards" | "fill" | "match" | "quiz";
type Choice = { key: string; text: string };

function shuffle<T>(arr: T[]): T[] {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

/* ═══════════════════════════════════════════════════════ */
export default function PhrasalVerbPage() {
  const [mode, setMode] = useState<GameMode>("cards");
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE}/api/v1/exam/english/phrasal-verbs-data`)
      .then(r => r.json())
      .then(data => {
        PHRASAL_VERBS = data.verbs || [];
        FILL_SENTENCES = data.fill_sentences || [];
        QUIZ_QUESTIONS = data.quiz_questions || [];
        setLoaded(true);
      })
      .catch(() => setLoaded(true));
  }, []);

  if (!loaded) {
    return (
      <div className="pv-page" style={{ textAlign: "center", paddingTop: 48 }}>
        <div style={{ fontSize: 48, marginBottom: 16 }}>⏳</div>
        <p style={{ fontSize: 14, color: "var(--text-tertiary)" }}>Đang tải...</p>
      </div>
    );
  }

  return (
    <div className="pv-page">
      <nav className="pv-breadcrumb">
        <Link href="/exam/english">English Lớp 10</Link>
        <span>/</span>
        <span>Phrasal Verbs</span>
      </nav>

      <h1 className="pv-title">🔤 Phrasal Verbs</h1>

      <div className="pv-tabs">
        {([
          { key: "cards" as GameMode, label: "📚 Thẻ từ", desc: "Lật thẻ xem nghĩa" },
          { key: "fill" as GameMode, label: "✏️ Điền từ", desc: "Điền vào chỗ trống" },
          { key: "match" as GameMode, label: "🔗 Nối nghĩa", desc: "Nối cụm từ - nghĩa" },
          { key: "quiz" as GameMode, label: "🎯 Trắc nghiệm", desc: "Chọn đáp án đúng" },
        ]).map(t => (
          <button key={t.key} onClick={() => setMode(t.key)} className={`pv-tab ${mode === t.key ? "active" : ""}`}>
            <div className="pv-tab-label">{t.label}</div>
            <div className="pv-tab-desc">{t.desc}</div>
          </button>
        ))}
      </div>

      {mode === "cards" && <FlashcardMode />}
      {mode === "fill" && <FillMode />}
      {mode === "match" && <MatchMode />}
      {mode === "quiz" && <QuizMode />}

      <style jsx global>{`
        .pv-page { max-width: 100%; margin: 0 auto; padding: 24px 24px; }
        .pv-breadcrumb { font-size: 13px; color: var(--text-tertiary); margin-bottom: 16px; display: flex; align-items: center; gap: 6px; }
        .pv-breadcrumb a { color: var(--text-tertiary); text-decoration: none; }
        .pv-breadcrumb a:hover { color: var(--action-primary); }
        .pv-breadcrumb span:last-child { color: var(--text-primary); }
        .pv-title { font-size: 24px; font-weight: 900; color: var(--text-primary); margin-bottom: 4px; }
        .pv-subtitle { font-size: 13px; color: var(--text-tertiary); margin-bottom: 20px; }

        .pv-tabs { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-bottom: 24px; }
        @media (max-width: 640px) { .pv-tabs { grid-template-columns: repeat(2, 1fr); } }
        .pv-tab { border-radius: 12px; padding: 12px; text-align: left; border: 1px solid var(--border-default); background: var(--bg-surface); cursor: pointer; transition: all 0.2s; }
        .pv-tab:hover { border-color: var(--action-primary); }
        .pv-tab.active { border-color: var(--action-primary); background: var(--bg-interactive); box-shadow: var(--shadow-sm); }
        .pv-tab-label { font-size: 14px; font-weight: 700; color: var(--text-primary); }
        .pv-tab-desc { font-size: 11px; color: var(--text-tertiary); margin-top: 2px; }

        /* Card */
        .pv-card-wrap { width: 100%; max-width: 480px; margin: 0 auto; aspect-ratio: 3/2; perspective: 1000px; cursor: pointer; user-select: none; }
        @media (max-width: 640px) { .pv-card-wrap { max-width: 100%; aspect-ratio: 4/3; } }
        .pv-card-inner { position: relative; width: 100%; height: 100%; transition: transform 0.5s; transform-style: preserve-3d; }
        .pv-card-inner.flipped { transform: rotateY(180deg); }
        .pv-card-face { position: absolute; inset: 0; border-radius: 16px; display: flex; flex-direction: column; align-items: center; justify-content: center; backface-visibility: hidden; color: white; padding: 20px; text-align: center; }
        .pv-card-front { background: linear-gradient(135deg, #3b82f6, #6366f1); }
        .pv-card-back { background: linear-gradient(135deg, #10b981, #14b8a6); transform: rotateY(180deg); }
        .pv-card-emoji { font-size: 36px; margin-bottom: 8px; }
        .pv-card-verb { font-size: 22px; font-weight: 900; }
        @media (max-width: 640px) { .pv-card-verb { font-size: 20px; } .pv-card-emoji { font-size: 28px; } }
        .pv-card-hint { font-size: 12px; opacity: 0.7; margin-top: 8px; }
        .pv-card-meaning { font-size: 15px; font-weight: 700; margin-bottom: 2px; }
        .pv-card-meaning-en { font-size: 12px; opacity: 0.8; font-style: italic; margin-bottom: 10px; }
        .pv-card-example { background: rgba(255,255,255,0.2); border-radius: 8px; padding: 8px 12px; font-size: 12px; line-height: 1.4; }

        /* Controls */
        .pv-controls { display: flex; gap: 12px; margin-top: 16px; }
        .pv-btn { flex: 1; padding: 12px; border-radius: 12px; font-weight: 700; font-size: 14px; border: none; cursor: pointer; transition: all 0.2s; }
        .pv-btn:active { transform: scale(0.97); }
        .pv-btn-secondary { background: var(--bg-interactive); color: var(--text-secondary); }
        .pv-btn-secondary:hover { background: var(--bg-interactive-hover); }
        .pv-btn-primary { background: var(--action-primary); color: white; }
        .pv-btn-primary:hover { background: var(--action-primary-hover); }
        .pv-btn-success { background: var(--_green-100, #dcfce7); color: var(--_green-700, #15803d); }

        /* Grid overview */
        .pv-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-top: 24px; }
        .pv-grid-item { border-radius: 12px; padding: 12px; border: 1px solid var(--border-default); background: var(--bg-surface); cursor: pointer; text-align: left; transition: all 0.2s; }
        .pv-grid-item:hover { border-color: var(--action-primary); }
        .pv-grid-item.active { border-color: var(--action-primary); background: var(--bg-interactive); }
        .pv-grid-item-top { display: flex; align-items: center; gap: 8px; }
        .pv-grid-item-verb { font-weight: 700; font-size: 14px; color: var(--text-primary); }
        .pv-grid-item-meaning { font-size: 12px; color: var(--text-tertiary); margin-top: 4px; }

        /* Fill */
        .pv-fill-info { background: var(--bg-interactive); border: 1px solid var(--border-default); border-radius: 12px; padding: 16px; margin-bottom: 20px; }
        .pv-fill-info p { font-size: 13px; color: var(--action-primary); font-weight: 500; margin: 0; }
        .pv-fill-item { border-radius: 12px; border: 1px solid var(--border-default); background: var(--bg-surface); padding: 16px; transition: all 0.3s; }
        .pv-fill-item.correct { border-color: var(--_green-500, #22c55e); background: rgba(34,197,94,0.06); }
        .pv-fill-item.wrong { border-color: var(--_red-500, #ef4444); background: rgba(239,68,68,0.06); }
        .pv-fill-header { display: flex; align-items: flex-start; gap: 8px; margin-bottom: 12px; }
        .pv-fill-num { flex-shrink: 0; width: 28px; height: 28px; border-radius: 50%; font-size: 12px; font-weight: 700; display: flex; align-items: center; justify-content: center; background: var(--bg-interactive); color: var(--text-secondary); }
        .pv-fill-num.correct { background: #22c55e; color: white; }
        .pv-fill-num.wrong { background: #ef4444; color: white; }
        .pv-fill-text { font-size: 14px; color: var(--text-primary); flex: 1; line-height: 1.6; }
        .pv-fill-blank { font-weight: 700; padding: 2px 8px; border-radius: 6px; margin: 0 4px; background: var(--bg-interactive); color: var(--action-primary); }
        .pv-fill-blank.correct { background: rgba(34,197,94,0.15); color: #15803d; }
        .pv-fill-blank.wrong { background: rgba(239,68,68,0.15); color: #dc2626; }
        .pv-fill-hint { font-size: 11px; color: var(--text-tertiary); margin-left: 36px; margin-bottom: 8px; }
        .pv-fill-hint-btn { font-size: 11px; color: var(--action-primary); background: var(--bg-interactive); border: 1px solid var(--border-default); border-radius: 6px; padding: 3px 10px; margin-left: 36px; margin-bottom: 8px; cursor: pointer; transition: all 0.2s; }
        .pv-fill-hint-btn:hover { background: var(--bg-interactive-hover); border-color: var(--action-primary); }
        .pv-fill-options { display: flex; flex-wrap: wrap; gap: 8px; margin-left: 36px; }
        .pv-fill-opt { padding: 6px 12px; border-radius: 8px; font-size: 12px; font-weight: 500; border: 1px solid var(--border-default); background: var(--bg-surface); color: var(--text-secondary); cursor: pointer; transition: all 0.2s; }
        .pv-fill-opt:hover { border-color: var(--action-primary); }
        .pv-fill-opt.selected { background: var(--action-primary); color: white; border-color: var(--action-primary); }

        /* Match */
        .pv-match-info { background: rgba(168,85,247,0.08); border: 1px solid var(--border-default); border-radius: 12px; padding: 16px; margin-bottom: 20px; }
        .pv-match-info p { font-size: 13px; color: #a855f7; font-weight: 500; margin: 0; }
        .pv-match-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
        @media (max-width: 480px) { .pv-match-grid { gap: 8px; } }
        .pv-match-label { font-size: 11px; font-weight: 700; color: var(--text-tertiary); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 12px; }
        .pv-match-btn { width: 100%; border-radius: 12px; padding: 12px 16px; text-align: left; font-size: 13px; font-weight: 600; border: 1px solid var(--border-default); background: var(--bg-surface); color: var(--text-primary); cursor: pointer; transition: all 0.2s; margin-bottom: 8px; }
        .pv-match-btn:hover { border-color: var(--action-primary); }
        .pv-match-btn.selected { border-color: var(--action-primary); background: var(--bg-interactive); color: var(--action-primary); box-shadow: var(--shadow-sm); }
        .pv-match-btn.matched { border-color: #22c55e; background: rgba(34,197,94,0.08); color: #22c55e; opacity: 0.6; cursor: default; }
        .pv-match-btn.wrong { border-color: #ef4444; background: rgba(239,68,68,0.08); color: #ef4444; animation: wrongShake 0.4s ease; }
        .pv-match-meaning { color: var(--text-secondary); }
        .pv-match-done { text-align: center; padding: 20px; background: rgba(34,197,94,0.06); border-radius: 12px; margin-bottom: 16px; }

        /* Quiz */
        .pv-quiz-bar { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
        .pv-quiz-track { flex: 1; height: 8px; background: var(--bg-interactive); border-radius: 99px; overflow: hidden; }
        .pv-quiz-fill { height: 100%; background: var(--action-primary); border-radius: 99px; transition: width 0.3s; }
        .pv-quiz-count { font-size: 12px; color: var(--text-tertiary); font-weight: 700; }
        .pv-quiz-question { background: var(--bg-surface); border-radius: 12px; padding: 24px; border: 1px solid var(--border-default); margin-bottom: 16px; text-align: center; }
        .pv-quiz-question p { font-size: 16px; font-weight: 700; color: var(--text-primary); margin: 0; line-height: 1.5; }
        .pv-quiz-opts { display: grid; gap: 12px; }
        .pv-quiz-opt { display: flex; align-items: center; gap: 12px; border-radius: 12px; padding: 14px 20px; text-align: left; font-size: 14px; border: 1px solid var(--border-default); background: var(--bg-surface); color: var(--text-primary); cursor: pointer; transition: all 0.2s; }
        .pv-quiz-opt:hover { border-color: var(--action-primary); }
        .pv-quiz-opt.correct { border-color: #22c55e; background: rgba(34,197,94,0.08); color: #15803d; font-weight: 600; }
        .pv-quiz-opt.wrong { border-color: #ef4444; background: rgba(239,68,68,0.08); color: #dc2626; }
        .pv-quiz-opt.dim { color: var(--text-disabled); }
        .pv-quiz-key { flex-shrink: 0; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 700; border: 1px solid var(--border-default); color: var(--text-tertiary); }
        .pv-quiz-key.correct { background: #22c55e; color: white; border-color: #22c55e; }
        .pv-quiz-key.wrong { background: #ef4444; color: white; border-color: #ef4444; }
        .pv-quiz-key.selected { background: var(--action-primary); color: white; border-color: var(--action-primary); }
        .pv-quiz-score { font-size: 12px; color: var(--text-tertiary); text-align: center; margin-top: 16px; }

        /* Result */
        .pv-result { text-align: center; padding: 40px 20px; }
        .pv-result-score { font-size: 48px; font-weight: 900; margin-bottom: 8px; }
        .pv-result-detail { font-size: 14px; color: var(--text-secondary); margin-bottom: 4px; }
        .pv-result-msg { font-size: 13px; color: var(--text-tertiary); margin-bottom: 20px; }

        @keyframes wrongShake {
          0%, 100% { transform: translateX(0); }
          20% { transform: translateX(-6px); }
          40% { transform: translateX(6px); }
          60% { transform: translateX(-4px); }
          80% { transform: translateX(4px); }
        }
      `}</style>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════
   1. FLASHCARD MODE
   ═══════════════════════════════════════════════════════ */
function FlashcardMode() {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [learned, setLearned] = useState<Set<number>>(new Set());
  const pv = PHRASAL_VERBS[currentIndex];

  const next = () => { setFlipped(false); setCurrentIndex((currentIndex + 1) % PHRASAL_VERBS.length); };
  const prev = () => { setFlipped(false); setCurrentIndex((currentIndex - 1 + PHRASAL_VERBS.length) % PHRASAL_VERBS.length); };
  const markLearned = () => {
    setLearned(prev => { const s = new Set(prev); if (s.has(pv.id)) s.delete(pv.id); else s.add(pv.id); return s; });
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16, fontSize: 13, color: "var(--text-tertiary)" }}>
        <span>{currentIndex + 1} / {PHRASAL_VERBS.length}</span>
        <span style={{ color: "#22c55e", fontWeight: 700 }}>✓ {learned.size} đã thuộc</span>
      </div>

      <div className="pv-card-wrap" onClick={() => setFlipped(!flipped)}>
        <div className={`pv-card-inner ${flipped ? "flipped" : ""}`}>
          <div className="pv-card-face pv-card-front">
            <div className="pv-card-emoji">{pv.emoji}</div>
            <div className="pv-card-verb">{pv.verb}</div>
            <div className="pv-card-hint">Nhấn để xem nghĩa</div>
          </div>
          <div className="pv-card-face pv-card-back">
            <div style={{ fontSize: 16, fontWeight: 900, marginBottom: 8 }}>{pv.verb}</div>
            <div className="pv-card-meaning">{pv.meaning}</div>
            <div className="pv-card-meaning-en">{pv.meaningEn}</div>
            <div className="pv-card-example">
              <p style={{ fontWeight: 600, margin: 0 }}>📝 {pv.example}</p>
              <p style={{ opacity: 0.8, marginTop: 4, marginBottom: 0 }}>→ {pv.exampleVi}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="pv-controls">
        <button className="pv-btn pv-btn-secondary" onClick={prev}>← Trước</button>
        <button className={`pv-btn ${learned.has(pv.id) ? "pv-btn-success" : "pv-btn-secondary"}`} onClick={markLearned}>
          {learned.has(pv.id) ? "✓ Đã thuộc" : "Đánh dấu"}
        </button>
        <button className="pv-btn pv-btn-primary" onClick={next}>Tiếp →</button>
      </div>

      <div className="pv-grid">
        {PHRASAL_VERBS.map((pv, i) => (
          <button key={pv.id} onClick={() => { setCurrentIndex(i); setFlipped(false); }} className={`pv-grid-item ${i === currentIndex ? "active" : ""}`}>
            <div className="pv-grid-item-top">
              <span>{pv.emoji}</span>
              <span className="pv-grid-item-verb">{pv.verb}</span>
              {learned.has(pv.id) && <span style={{ marginLeft: "auto", color: "#22c55e", fontSize: 12 }}>✓</span>}
            </div>
            <div className="pv-grid-item-meaning">{pv.meaning}</div>
          </button>
        ))}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════
   2. FILL-IN-THE-BLANK MODE
   ═══════════════════════════════════════════════════════ */
function FillMode() {
  const [sentences] = useState(() => shuffle(FILL_SENTENCES).slice(0, 5));
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [checked, setChecked] = useState(false);
  const [showHints, setShowHints] = useState<Set<number>>(new Set());
  const options = ["turn off", "look after", "look up", "look for", "looking for"];

  const handleSelect = (idx: number, value: string) => { if (checked) return; setAnswers(prev => ({ ...prev, [idx]: value })); };
  const correctCount = checked ? sentences.filter((s, i) => answers[i] === s.answer).length : 0;

  return (
    <div>
      <div className="pv-fill-info"><p>✏️ Chọn phrasal verb phù hợp để điền vào chỗ trống.</p></div>
      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        {sentences.map((s, i) => {
          const selected = answers[i];
          const isCorrect = selected === s.answer;
          const parts = s.sentence.split("___");
          return (
            <div key={i} className={`pv-fill-item ${checked ? (isCorrect ? "correct" : "wrong") : ""}`}>
              <div className="pv-fill-header">
                <span className={`pv-fill-num ${checked ? (isCorrect ? "correct" : "wrong") : ""}`}>{i + 1}</span>
                <p className="pv-fill-text">
                  {parts[0]}
                  <span className={`pv-fill-blank ${checked ? (isCorrect ? "correct" : "wrong") : ""}`}>{selected || "___________"}</span>
                  {parts[1]}
                </p>
              </div>
              {!checked && (
                showHints.has(i)
                  ? <div className="pv-fill-hint">💡 {s.hint}</div>
                  : <button className="pv-fill-hint-btn" onClick={() => setShowHints(prev => { const s2 = new Set(prev); s2.add(i); return s2; })}>💡 Gợi ý</button>
              )}
              {!checked && (
                <div className="pv-fill-options">
                  {options.map(opt => (
                    <button key={opt} onClick={() => handleSelect(i, opt)} className={`pv-fill-opt ${selected === opt ? "selected" : ""}`}>{opt}</button>
                  ))}
                </div>
              )}
              {checked && !isCorrect && <p style={{ fontSize: 12, color: "#22c55e", marginLeft: 36, marginTop: 4 }}>Đáp án đúng: <strong>{s.answer}</strong></p>}
            </div>
          );
        })}
      </div>
      <div className="pv-controls" style={{ marginTop: 20 }}>
        {!checked ? (
          <button className="pv-btn pv-btn-primary" onClick={() => setChecked(true)} disabled={Object.keys(answers).length < sentences.length} style={{ opacity: Object.keys(answers).length < sentences.length ? 0.4 : 1 }}>
            ✅ Kiểm tra
          </button>
        ) : (
          <>
            <div className="pv-btn pv-btn-secondary" style={{ textAlign: "center", cursor: "default" }}>{correctCount}/{sentences.length} đúng</div>
            <button className="pv-btn pv-btn-primary" onClick={() => { setAnswers({}); setChecked(false); }}>🔄 Làm lại</button>
          </>
        )}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════
   3. MATCH MODE
   ═══════════════════════════════════════════════════════ */
function MatchMode() {
  const [verbs] = useState(() => shuffle(PHRASAL_VERBS));
  const [meanings] = useState(() => shuffle(PHRASAL_VERBS));
  const [selectedVerb, setSelectedVerb] = useState<number | null>(null);
  const [matched, setMatched] = useState<Set<number>>(new Set());
  const [wrongPair, setWrongPair] = useState<{ v: number; m: number } | null>(null);

  const handleVerbClick = (id: number) => { if (matched.has(id)) return; setSelectedVerb(id); setWrongPair(null); };
  const handleMeaningClick = (id: number) => {
    if (matched.has(id) || selectedVerb === null) return;
    if (selectedVerb === id) { setMatched(prev => new Set(prev).add(id)); setSelectedVerb(null); }
    else { setWrongPair({ v: selectedVerb, m: id }); setTimeout(() => { setWrongPair(null); setSelectedVerb(null); }, 800); }
  };
  const allMatched = matched.size === PHRASAL_VERBS.length;

  return (
    <div>
      <div className="pv-match-info"><p>🔗 Chọn 1 phrasal verb bên trái, sau đó chọn nghĩa đúng bên phải.</p></div>
      {allMatched && (
        <div className="pv-match-done">
          <div style={{ fontSize: 32 }}>🎉</div>
          <p style={{ fontWeight: 700, color: "#22c55e", margin: "8px 0" }}>Hoàn thành! Nối đúng tất cả!</p>
          <button onClick={() => { setMatched(new Set()); setSelectedVerb(null); }} style={{ fontSize: 13, color: "var(--action-primary)", background: "none", border: "none", cursor: "pointer" }}>🔄 Chơi lại</button>
        </div>
      )}
      <div className="pv-match-grid">
        <div>
          <div className="pv-match-label">Phrasal Verb</div>
          {verbs.map(pv => (
            <button key={pv.id} onClick={() => handleVerbClick(pv.id)} disabled={matched.has(pv.id)}
              className={`pv-match-btn ${matched.has(pv.id) ? "matched" : selectedVerb === pv.id ? "selected" : wrongPair?.v === pv.id ? "wrong" : ""}`}>
              {pv.emoji} {pv.verb}
            </button>
          ))}
        </div>
        <div>
          <div className="pv-match-label">Nghĩa</div>
          {meanings.map(pv => (
            <button key={pv.id} onClick={() => handleMeaningClick(pv.id)} disabled={matched.has(pv.id)}
              className={`pv-match-btn pv-match-meaning ${matched.has(pv.id) ? "matched" : wrongPair?.m === pv.id ? "wrong" : ""}`}>
              {pv.meaning}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════
   4. QUIZ MODE
   ═══════════════════════════════════════════════════════ */
function QuizMode() {
  const [questions] = useState(() => shuffle(QUIZ_QUESTIONS));
  const [current, setCurrent] = useState(0);
  const [selected, setSelected] = useState<number | null>(null);
  const [score, setScore] = useState(0);
  const [done, setDone] = useState(false);
  const q = questions[current];

  const handleSelect = (idx: number) => {
    if (selected !== null) return;
    setSelected(idx);
    if (idx === q.correct) setScore(prev => prev + 1);
    setTimeout(() => {
      if (current + 1 >= questions.length) setDone(true);
      else { setCurrent(prev => prev + 1); setSelected(null); }
    }, 1200);
  };

  const handleReset = () => { setCurrent(0); setSelected(null); setScore(0); setDone(false); };

  if (done) {
    const pct = Math.round(score / questions.length * 10);
    return (
      <div className="pv-result">
        <div className="pv-result-score" style={{ color: pct >= 8 ? "#10b981" : pct >= 6 ? "#f59e0b" : "#ef4444" }}>
          {pct}<span style={{ fontSize: 24, color: "var(--text-tertiary)" }}>/10</span>
        </div>
        <p className="pv-result-detail">{score}/{questions.length} câu đúng</p>
        <p className="pv-result-msg">{pct >= 8 ? "🎉 Xuất sắc!" : pct >= 6 ? "👍 Khá tốt!" : "💪 Cần ôn luyện thêm!"}</p>
        <button className="pv-btn pv-btn-primary" style={{ maxWidth: 200 }} onClick={handleReset}>🔄 Làm lại</button>
      </div>
    );
  }

  return (
    <div>
      <div className="pv-quiz-bar">
        <div className="pv-quiz-track"><div className="pv-quiz-fill" style={{ width: `${(current / questions.length) * 100}%` }} /></div>
        <span className="pv-quiz-count">{current + 1}/{questions.length}</span>
      </div>
      <div className="pv-quiz-question"><p>{q.question}</p></div>
      <div className="pv-quiz-opts">
        {q.options.map((opt, i) => {
          let cls = "";
          let keyCls = "";
          if (selected !== null) {
            if (i === q.correct) { cls = "correct"; keyCls = "correct"; }
            else if (i === selected) { cls = "wrong"; keyCls = "wrong"; }
            else cls = "dim";
          }
          return (
            <button key={i} onClick={() => handleSelect(i)} disabled={selected !== null} className={`pv-quiz-opt ${cls}`}>
              <span className={`pv-quiz-key ${keyCls}`}>{String.fromCharCode(65 + i)}</span>
              {opt}
            </button>
          );
        })}
      </div>
      <div className="pv-quiz-score">Điểm: <strong style={{ color: "#22c55e" }}>{score}</strong></div>
    </div>
  );
}
