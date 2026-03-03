"use client";

import { useState, useEffect, useCallback } from "react";

interface Word { word: string; meaning: string; }

export default function TypingPracticePage() {
  const [words, setWords] = useState<Word[]>([]);
  const [current, setCurrent] = useState(0);
  const [input, setInput] = useState("");
  const [showResult, setShowResult] = useState(false);
  const [correct, setCorrect] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/v1/vocab/typing", { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((d: Word[]) => { setWords(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  const check = useCallback(() => {
    if (!words[current]) return;
    const isCorrect = input.trim().toLowerCase() === words[current].word.toLowerCase();
    if (isCorrect) setCorrect((c) => c + 1);
    setShowResult(true);
  }, [input, current, words]);

  const next = () => {
    setInput("");
    setShowResult(false);
    setCurrent((c) => c + 1);
  };

  if (loading) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Đang tải...</div>;
  if (!words.length) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Không có từ để luyện tập.</div>;

  if (current >= words.length) return (
    <div style={{ maxWidth: 500, margin: "0 auto", padding: "4rem 1rem", textAlign: "center" }}>
      <div className="text-5xl mb-4">🎉</div>
      <h1 className="text-xl font-bold mb-3" style={{ color: "var(--text-primary)" }}>Hoàn thành!</h1>
      <p className="text-lg font-bold mb-2" style={{ color: "#10b981" }}>{correct}/{words.length} đúng</p>
      <button onClick={() => { setCurrent(0); setCorrect(0); setShowResult(false); setInput(""); }} className="px-6 py-3 rounded-xl font-semibold text-white mt-4" style={{ background: "#6366f1", border: "none", cursor: "pointer" }}>Luyện lại</button>
    </div>
  );

  const w = words[current];

  return (
    <div style={{ maxWidth: 500, margin: "0 auto", padding: "2rem 1rem" }}>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-xl font-bold" style={{ color: "var(--text-primary)" }}>⌨️ Luyện gõ</h1>
        <span className="text-sm font-semibold" style={{ color: "var(--text-tertiary)" }}>{current + 1}/{words.length}</span>
      </div>

      <div className="h-2 rounded-full overflow-hidden mb-8" style={{ background: "var(--border-default)" }}>
        <div className="h-full rounded-full" style={{ background: "#6366f1", width: `${((current + 1) / words.length) * 100}%`, transition: "width 0.3s" }} />
      </div>

      <div className="p-8 rounded-2xl text-center mb-6" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
        <p className="text-sm mb-2" style={{ color: "var(--text-tertiary)" }}>Nghĩa:</p>
        <p className="text-xl font-bold" style={{ color: "var(--text-primary)" }}>{w.meaning}</p>
      </div>

      <input value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === "Enter" && (showResult ? next() : check())} placeholder="Gõ từ tiếng Anh..." autoFocus className="w-full p-4 rounded-xl text-center text-lg font-semibold border mb-4" style={{
        background: showResult ? (input.trim().toLowerCase() === w.word.toLowerCase() ? "rgba(16,185,129,.06)" : "rgba(239,68,68,.06)") : "var(--bg-interactive)",
        borderColor: showResult ? (input.trim().toLowerCase() === w.word.toLowerCase() ? "#10b981" : "#ef4444") : "var(--border-default)",
        color: "var(--text-primary)",
      }} disabled={showResult} />

      {showResult && (
        <div className="text-center mb-4">
          <p className="text-sm font-bold" style={{ color: input.trim().toLowerCase() === w.word.toLowerCase() ? "#10b981" : "#ef4444" }}>
            {input.trim().toLowerCase() === w.word.toLowerCase() ? "✅ Chính xác!" : `❌ Đáp án: ${w.word}`}
          </p>
        </div>
      )}

      <button onClick={showResult ? next : check} disabled={!input.trim() && !showResult} className="w-full py-3 rounded-xl font-bold text-white" style={{ background: "#6366f1", opacity: !input.trim() && !showResult ? 0.5 : 1, border: "none", cursor: "pointer" }}>
        {showResult ? "Tiếp theo →" : "Kiểm tra"}
      </button>
    </div>
  );
}
