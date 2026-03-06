"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";

interface VocabWord {
  word: string;
  pos: string;
  ipa: string;
  meaning: string;
}

interface VocabTopicData {
  slug: string;
  title: string;
  title_vi: string;
  emoji: string;
  word_count: number;
  words: VocabWord[];
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

function shuffle<T>(arr: T[]): T[] {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

type ViewMode = "list" | "flashcard" | "quiz";

/* ═══════════════════════════════════════════════════════ */
export default function VocabDetailPage() {
  const params = useParams();
  const topicId = params.topicId as string;

  const [topic, setTopic] = useState<VocabTopicData | null>(null);
  const [loading, setLoading] = useState(true);
  const [mode, setMode] = useState<ViewMode>("list");

  useEffect(() => {
    setLoading(true);
    fetch(`${API_BASE}/api/v1/exam/english/vocab-topics/${topicId}`)
      .then(r => r.ok ? r.json() : null)
      .then(data => { if (data) setTopic(data); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [topicId]);

  if (loading) {
    return (
      <div className="vd-page" style={{ textAlign: "center", paddingTop: 48 }}>
        <div style={{ fontSize: 48, marginBottom: 16 }}>⏳</div>
        <p style={{ fontSize: 14, color: "var(--text-tertiary)" }}>Đang tải...</p>
      </div>
    );
  }

  if (!topic) {
    return (
      <div className="vd-page" style={{ textAlign: "center", paddingTop: 48 }}>
        <div style={{ fontSize: 48, marginBottom: 16 }}>📖</div>
        <h2 style={{ fontSize: 20, fontWeight: 700, color: "var(--text-primary)", marginBottom: 8 }}>Chủ đề không tồn tại</h2>
        <Link href="/exam/english/vocabulary" style={{ color: "var(--action-primary)", fontSize: 14 }}>← Quay lại</Link>
      </div>
    );
  }

  return (
    <div className="vd-page">
      <nav className="vd-breadcrumb">
        <Link href="/exam/english">English Lớp 10</Link>
        <span>/</span>
        <Link href="/exam/english/vocabulary">Từ vựng</Link>
        <span>/</span>
        <span>{topic.title}</span>
      </nav>

      <div style={{ marginBottom: 20 }}>
        <h1 className="vd-title">
          <span style={{ fontSize: 26 }}>{topic.emoji}</span>
          {topic.title}
        </h1>
        <p style={{ fontSize: 14, color: "var(--text-secondary)", margin: 0 }}>
          {topic.title_vi} — {topic.word_count} từ vựng
        </p>
      </div>

      {/* Mode buttons */}
      <div className="vd-modes">
        <button className={`vd-mode-btn ${mode === "list" ? "active" : ""}`} onClick={() => setMode("list")}>
          📋 Danh sách
        </button>
        <button className={`vd-mode-btn ${mode === "flashcard" ? "active" : ""}`} onClick={() => setMode("flashcard")}>
          📚 Học Flashcard
        </button>
        <button className={`vd-mode-btn ${mode === "quiz" ? "active" : ""}`} onClick={() => setMode("quiz")}>
          ✍️ Kiểm tra
        </button>
      </div>

      {mode === "list" && <WordList words={topic.words} />}
      {mode === "flashcard" && <FlashcardMode words={topic.words} />}
      {mode === "quiz" && <QuizMode words={topic.words} />}

      <style jsx global>{`
        .vd-page { max-width: 100%; margin: 0 auto; padding: 24px; }
        .vd-breadcrumb { font-size: 13px; color: var(--text-tertiary); margin-bottom: 12px; display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
        .vd-breadcrumb a { color: var(--text-tertiary); text-decoration: none; }
        .vd-breadcrumb a:hover { color: var(--action-primary); }
        .vd-breadcrumb span:last-child { color: var(--text-primary); }
        .vd-title { font-size: 24px; font-weight: 900; color: var(--text-primary); margin: 0; display: flex; align-items: center; gap: 8px; }

        .vd-modes { display: flex; gap: 6px; margin-bottom: 16px; flex-wrap: wrap; }
        .vd-mode-btn {
          padding: 7px 14px; border-radius: 99px; font-weight: 600; font-size: 13px;
          border: 1px solid var(--border-default); background: var(--bg-surface);
          color: var(--text-secondary); cursor: pointer; transition: all 0.2s;
          white-space: nowrap;
        }
        .vd-mode-btn:hover { border-color: var(--text-primary); color: var(--text-primary); }
        .vd-mode-btn.active { background: var(--text-primary); color: white; border-color: var(--text-primary); }

        /* Word list table */
        .vd-table-wrap { border-radius: 14px; border: 1px solid var(--border-default); overflow: hidden; background: var(--bg-surface); box-shadow: var(--shadow-sm); }
        .vd-table { width: 100%; border-collapse: collapse; }
        .vd-table th { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .05em; color: var(--text-tertiary); padding: 10px 14px; text-align: left; background: var(--bg-interactive); border-bottom: 1px solid var(--border-default); }
        .vd-table td { font-size: 13px; color: var(--text-primary); padding: 10px 14px; border-bottom: 1px solid var(--border-default); }
        .vd-table tr:last-child td { border-bottom: none; }
        .vd-table tr:hover td { background: var(--bg-interactive); }
        .vd-word { font-weight: 700; color: var(--text-primary); }
        .vd-pos { font-size: 11px; font-weight: 600; color: var(--text-secondary); background: rgba(0,0,0,0.05); padding: 2px 8px; border-radius: 6px; display: inline-block; }
        .vd-ipa { font-size: 12px; color: var(--text-tertiary); font-style: italic; }
        .vd-meaning { color: var(--text-secondary); }

        /* Flashcard */
        .vd-fc-wrap { perspective: 1000px; margin: 0 auto 16px; max-width: 400px; cursor: pointer; }
        .vd-fc-inner { position: relative; width: 100%; min-height: 200px; transition: transform 0.5s; transform-style: preserve-3d; }
        .vd-fc-inner.flipped { transform: rotateY(180deg); }
        .vd-fc-face { position: absolute; inset: 0; border-radius: 18px; backface-visibility: hidden; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 28px 20px; text-align: center; }
        .vd-fc-front { background: linear-gradient(135deg, #1e293b, #334155); color: white; }
        .vd-fc-back { background: var(--bg-surface); border: 2px solid var(--border-strong); transform: rotateY(180deg); }
        .vd-fc-word { font-size: 26px; font-weight: 900; margin-bottom: 6px; }
        .vd-fc-ipa { font-size: 14px; opacity: 0.8; }
        .vd-fc-hint { font-size: 12px; opacity: 0.6; margin-top: 10px; }
        .vd-fc-meaning { font-size: 20px; font-weight: 800; color: var(--text-primary); margin-bottom: 6px; }
        .vd-fc-pos-tag { font-size: 12px; font-weight: 600; color: var(--text-secondary); background: rgba(0,0,0,0.06); padding: 3px 10px; border-radius: 6px; margin-bottom: 8px; }

        .vd-fc-controls { display: flex; gap: 8px; justify-content: center; }
        .vd-fc-btn { flex: 1; max-width: 160px; padding: 11px; border-radius: 10px; font-weight: 700; font-size: 13px; border: none; cursor: pointer; transition: all 0.2s; }
        .vd-fc-btn:active { transform: scale(0.97); }
        .vd-fc-prev { background: var(--bg-interactive); color: var(--text-secondary); }
        .vd-fc-prev:hover { background: var(--bg-interactive-hover); }
        .vd-fc-next { background: var(--text-primary); color: white; }
        .vd-fc-next:hover { opacity: 0.9; }
        .vd-fc-progress { text-align: center; font-size: 13px; color: var(--text-tertiary); margin-bottom: 12px; }

        /* Quiz */
        .vd-quiz-progress { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
        .vd-quiz-track { flex: 1; height: 8px; background: var(--bg-interactive); border-radius: 99px; overflow: hidden; }
        .vd-quiz-fill { height: 100%; background: var(--text-primary); border-radius: 99px; transition: width 0.3s; }
        .vd-quiz-count { font-size: 12px; color: var(--text-tertiary); font-weight: 700; }
        .vd-quiz-q { background: var(--bg-surface); border-radius: 14px; padding: 20px; border: 1px solid var(--border-default); margin-bottom: 12px; text-align: center; box-shadow: var(--shadow-sm); }
        .vd-quiz-q-word { font-size: 22px; font-weight: 900; color: var(--text-primary); margin: 0 0 4px; }
        .vd-quiz-q-ipa { font-size: 13px; color: var(--text-tertiary); margin: 0 0 4px; font-style: italic; }
        .vd-quiz-q-pos { font-size: 12px; color: var(--text-secondary); font-weight: 600; }
        .vd-quiz-label { font-size: 13px; color: var(--text-tertiary); margin-bottom: 10px; text-align: center; }
        .vd-quiz-opts { display: grid; gap: 8px; }
        .vd-quiz-opt {
          display: flex; align-items: center; gap: 10px; border-radius: 10px; padding: 12px 14px;
          text-align: left; font-size: 14px; border: 1px solid var(--border-default);
          background: var(--bg-surface); color: var(--text-primary); cursor: pointer; transition: all 0.2s;
        }
        .vd-quiz-opt:hover { border-color: var(--text-secondary); }
        .vd-quiz-opt.correct { border-color: #22c55e; background: rgba(34,197,94,0.08); color: #15803d; font-weight: 600; }
        .vd-quiz-opt.wrong { border-color: #ef4444; background: rgba(239,68,68,0.08); color: #dc2626; }
        .vd-quiz-opt.dim { color: var(--text-disabled); }
        .vd-quiz-key {
          flex-shrink: 0; width: 30px; height: 30px; border-radius: 50%;
          display: flex; align-items: center; justify-content: center;
          font-size: 12px; font-weight: 700; border: 1px solid var(--border-default); color: var(--text-tertiary);
        }
        .vd-quiz-key.correct { background: #22c55e; color: white; border-color: #22c55e; }
        .vd-quiz-key.wrong { background: #ef4444; color: white; border-color: #ef4444; }
        .vd-quiz-key.selected { background: var(--text-primary); color: white; border-color: var(--text-primary); }

        .vd-result { text-align: center; padding: 32px 16px; }
        .vd-result-score { font-size: 48px; font-weight: 900; margin-bottom: 8px; }
        .vd-result-detail { font-size: 14px; color: var(--text-secondary); margin-bottom: 20px; }
        .vd-result-btn { padding: 12px 28px; border-radius: 12px; font-weight: 700; font-size: 14px; border: none; cursor: pointer; background: var(--text-primary); color: white; transition: all 0.2s; }
        .vd-result-btn:hover { opacity: 0.85; }

        @media (max-width: 640px) {
          .vd-page { padding: 16px; }
          .vd-breadcrumb { font-size: 12px; margin-bottom: 10px; }
          .vd-title { font-size: 20px; gap: 6px; }
          .vd-title span:first-child { font-size: 22px !important; }
          .vd-modes { gap: 6px; margin-bottom: 14px; }
          .vd-mode-btn { padding: 6px 12px; font-size: 12px; }
          .vd-table th { padding: 8px 10px; font-size: 10px; }
          .vd-table td { padding: 8px 10px; font-size: 12px; }
          .vd-table th:nth-child(1), .vd-table td:nth-child(1) { display: none; }
          .vd-table th:nth-child(4), .vd-table td:nth-child(4) { display: none; }
          .vd-fc-wrap { max-width: 100%; }
          .vd-fc-inner { min-height: 180px; }
          .vd-fc-face { padding: 24px 16px; }
          .vd-fc-word { font-size: 22px; }
          .vd-fc-meaning { font-size: 18px; }
          .vd-fc-controls { gap: 6px; }
          .vd-fc-btn { max-width: none; padding: 10px; font-size: 13px; }
          .vd-fc-progress { margin-bottom: 10px; font-size: 12px; }
          .vd-quiz-q { padding: 16px; }
          .vd-quiz-q-word { font-size: 20px; }
          .vd-quiz-opt { padding: 10px 12px; font-size: 13px; }
          .vd-quiz-key { width: 26px; height: 26px; font-size: 11px; }
        }
      `}</style>
    </div>
  );
}

/* ─── Word List ─────────────────────────────────────── */
function WordList({ words }: { words: VocabWord[] }) {
  return (
    <div className="vd-table-wrap">
      <table className="vd-table">
        <thead>
          <tr>
            <th>STT</th>
            <th>Từ vựng</th>
            <th>Loại</th>
            <th>Phiên âm</th>
            <th>Nghĩa</th>
          </tr>
        </thead>
        <tbody>
          {words.map((w, i) => (
            <tr key={i}>
              <td style={{ color: "var(--text-tertiary)", fontWeight: 600, width: 40 }}>{i + 1}</td>
              <td className="vd-word">{w.word}</td>
              <td><span className="vd-pos">{w.pos}</span></td>
              <td className="vd-ipa">{w.ipa}</td>
              <td className="vd-meaning">{w.meaning}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/* ─── Flashcard Mode ────────────────────────────────── */
function FlashcardMode({ words }: { words: VocabWord[] }) {
  const [idx, setIdx] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [learned, setLearned] = useState<Set<number>>(new Set());

  const w = words[idx];
  const prev = () => { setFlipped(false); setIdx((idx - 1 + words.length) % words.length); };
  const next = () => { setFlipped(false); setIdx((idx + 1) % words.length); };

  return (
    <div>
      <div className="vd-fc-progress">
        {idx + 1} / {words.length}
        {learned.size > 0 && <span style={{ marginLeft: 12, color: "#22c55e", fontWeight: 700 }}>✓ {learned.size} đã thuộc</span>}
      </div>

      <div className="vd-fc-wrap" onClick={() => setFlipped(!flipped)}>
        <div className={`vd-fc-inner ${flipped ? "flipped" : ""}`}>
          <div className="vd-fc-face vd-fc-front">
            <div className="vd-fc-word">{w.word}</div>
            <div className="vd-fc-ipa">{w.ipa}</div>
            <div className="vd-fc-hint">Nhấn để xem nghĩa</div>
          </div>
          <div className="vd-fc-face vd-fc-back">
            <div className="vd-fc-pos-tag">{w.pos}</div>
            <div className="vd-fc-meaning">{w.meaning}</div>
            <div style={{ fontSize: 13, color: "var(--text-tertiary)", marginTop: 8 }}>{w.ipa}</div>
          </div>
        </div>
      </div>

      <div className="vd-fc-controls">
        <button className="vd-fc-btn vd-fc-prev" onClick={prev}>← Trước</button>
        <button
          className="vd-fc-btn"
          style={{
            background: learned.has(idx) ? "rgba(34,197,94,0.1)" : "var(--bg-interactive)",
            color: learned.has(idx) ? "#15803d" : "var(--text-secondary)",
          }}
          onClick={() => {
            setLearned(prev => {
              const s = new Set(prev);
              if (s.has(idx)) s.delete(idx); else s.add(idx);
              return s;
            });
          }}
        >
          {learned.has(idx) ? "✓ Đã thuộc" : "Đánh dấu"}
        </button>
        <button className="vd-fc-btn vd-fc-next" onClick={next}>Tiếp →</button>
      </div>
    </div>
  );
}

/* ─── Quiz Mode ─────────────────────────────────────── */
function QuizMode({ words }: { words: VocabWord[] }) {
  const [questions] = useState(() => {
    return shuffle(words).map(w => {
      const wrongOpts = shuffle(words.filter(x => x.meaning !== w.meaning)).slice(0, 3);
      const options = shuffle([w, ...wrongOpts]);
      return {
        word: w.word,
        ipa: w.ipa,
        pos: w.pos,
        correctMeaning: w.meaning,
        options: options.map(o => o.meaning),
        correctIdx: options.findIndex(o => o.meaning === w.meaning),
      };
    });
  });

  const [current, setCurrent] = useState(0);
  const [selected, setSelected] = useState<number | null>(null);
  const [correct, setCorrect] = useState(0);
  const [done, setDone] = useState(false);

  const q = questions[current];

  const handleSelect = (idx: number) => {
    if (selected !== null) return;
    setSelected(idx);
    if (idx === q.correctIdx) setCorrect(c => c + 1);
  };

  const handleNext = () => {
    if (current + 1 >= questions.length) { setDone(true); }
    else { setCurrent(c => c + 1); setSelected(null); }
  };

  if (done) {
    const pct = Math.round(correct / questions.length * 100);
    return (
      <div className="vd-result">
        <div className="vd-result-score" style={{ color: pct >= 80 ? "#10b981" : pct >= 60 ? "#f59e0b" : "#ef4444" }}>
          {pct}%
        </div>
        <div className="vd-result-detail">
          {correct}/{questions.length} câu đúng
          {pct >= 80 ? " — Xuất sắc! 🎉" : pct >= 60 ? " — Khá tốt! 👍" : " — Cần ôn thêm! 💪"}
        </div>
        <button className="vd-result-btn" onClick={() => { setCurrent(0); setSelected(null); setCorrect(0); setDone(false); }}>
          🔄 Làm lại
        </button>
      </div>
    );
  }

  return (
    <div>
      <div className="vd-quiz-progress">
        <div className="vd-quiz-track">
          <div className="vd-quiz-fill" style={{ width: `${(current / questions.length) * 100}%` }} />
        </div>
        <div className="vd-quiz-count">{current + 1}/{questions.length}</div>
      </div>

      <div className="vd-quiz-q">
        <p className="vd-quiz-q-word">{q.word}</p>
        <p className="vd-quiz-q-ipa">{q.ipa}</p>
        <p className="vd-quiz-q-pos">{q.pos}</p>
      </div>

      <p className="vd-quiz-label">Chọn nghĩa đúng:</p>
      <div className="vd-quiz-opts">
        {q.options.map((opt, j) => {
          let cls = "vd-quiz-opt";
          let keyCls = "vd-quiz-key";
          if (selected !== null) {
            if (j === q.correctIdx) { cls += " correct"; keyCls += " correct"; }
            else if (j === selected) { cls += " wrong"; keyCls += " wrong"; }
            else { cls += " dim"; }
          } else if (j === selected) { keyCls += " selected"; }
          return (
            <button key={j} className={cls} onClick={() => handleSelect(j)} disabled={selected !== null}>
              <span className={keyCls}>{String.fromCharCode(65 + j)}</span>
              {opt}
            </button>
          );
        })}
      </div>

      {selected !== null && (
        <div style={{ textAlign: "center", marginTop: 16 }}>
          <button className="vd-fc-btn vd-fc-next" onClick={handleNext} style={{ maxWidth: 200, margin: "0 auto" }}>
            {current + 1 >= questions.length ? "Xem kết quả" : "Tiếp →"}
          </button>
        </div>
      )}
    </div>
  );
}
