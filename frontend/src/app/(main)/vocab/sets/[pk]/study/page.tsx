"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

interface StudyWord {
  id: number;
  word: string;
  reading: string;
  meaning: string;
  example: string;
  example_translation: string;
  sino_vi: string;
}

export default function SetStudyPage() {
  const params = useParams();
  const pk = params.pk as string;

  const [words, setWords] = useState<StudyWord[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [showAnswer, setShowAnswer] = useState(false);
  const [score, setScore] = useState({ known: 0, unknown: 0 });
  const [done, setDone] = useState(false);

  const total = words.length;
  const current = words[currentIdx] || null;

  useEffect(() => {
    fetch(`/api/v1/vocab/sets/${pk}/study`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d) => { setWords(d.words || []); setLoading(false); })
      .catch(() => { setWords([]); setLoading(false); });
  }, [pk]);

  const grade = (known: boolean) => {
    if (known) setScore((s) => ({ ...s, known: s.known + 1 }));
    else setScore((s) => ({ ...s, unknown: s.unknown + 1 }));

    if (currentIdx < total - 1) {
      setCurrentIdx((i) => i + 1);
      setShowAnswer(false);
    } else {
      setDone(true);
    }
  };

  if (loading) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Đang tải...</div>;

  return (
    <div style={{ padding: "24px", minHeight: "100vh" }}>
      <div className="max-w-lg mx-auto">
        <div className="flex items-center gap-3 mb-5">
          <Link href={`/vocab/sets/${pk}`} className="p-2 rounded-lg" style={{ color: "var(--text-secondary)" }}>
            <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M15 18l-6-6 6-6" /></svg>
          </Link>
          <h1 className="font-bold text-lg flex-1" style={{ color: "var(--text-primary)" }}>📖 Học từ vựng</h1>
          {total > 0 && <span className="text-xs" style={{ color: "var(--text-tertiary)" }}>{currentIdx + 1}/{total}</span>}
        </div>

        {/* Progress */}
        {total > 0 && !done && (
          <div className="h-1.5 rounded-full mb-5 overflow-hidden" style={{ background: "var(--border-default)" }}>
            <div className="h-full rounded-full transition-all" style={{ width: `${(currentIdx / total) * 100}%`, background: "linear-gradient(90deg, #6366f1, #8b5cf6)" }} />
          </div>
        )}

        {total === 0 ? (
          <div className="text-center py-16" style={{ color: "var(--text-secondary)" }}>
            <p>Chưa có từ nào trong bộ này.</p>
          </div>
        ) : done ? (
          <div className="p-8 rounded-2xl text-center" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
            <div className="text-5xl mb-3">🎉</div>
            <h2 className="text-xl font-bold mb-3" style={{ color: "var(--text-primary)" }}>Hoàn thành!</h2>
            <div className="flex justify-center gap-6 mb-6">
              <div><div className="text-2xl font-bold" style={{ color: "#10b981" }}>{score.known}</div><div className="text-xs" style={{ color: "var(--text-tertiary)" }}>Biết</div></div>
              <div><div className="text-2xl font-bold" style={{ color: "#ef4444" }}>{score.unknown}</div><div className="text-xs" style={{ color: "var(--text-tertiary)" }}>Chưa biết</div></div>
            </div>
            <div className="flex justify-center gap-3">
              <button onClick={() => { setCurrentIdx(0); setDone(false); setScore({ known: 0, unknown: 0 }); setShowAnswer(false); }} className="px-5 py-2 rounded-xl text-sm font-semibold" style={{ background: "var(--bg-interactive)", color: "var(--text-primary)", border: "1px solid var(--border-default)" }}>Học lại</button>
              <Link href={`/vocab/sets/${pk}`} className="px-5 py-2 rounded-xl text-sm font-semibold text-white" style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6)", textDecoration: "none" }}>Quay lại</Link>
            </div>
          </div>
        ) : current && (
          <div className="p-6 rounded-2xl" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
            <div className="text-center mb-6">
              <div className="text-3xl font-bold" style={{ fontFamily: "'Noto Sans JP', sans-serif", color: "var(--text-primary)" }}>{current.word}</div>
              {current.reading && <div className="text-sm mt-1" style={{ fontFamily: "'Noto Sans JP', sans-serif", color: "var(--text-secondary)" }}>{current.reading}</div>}
            </div>

            {!showAnswer ? (
              <button onClick={() => setShowAnswer(true)} className="w-full py-3 rounded-xl text-sm font-semibold text-white" style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6)" }}>
                Xem đáp án
              </button>
            ) : (
              <>
                {current.sino_vi && <div className="text-xs mb-2"><span className="font-bold px-1.5 py-0.5 rounded" style={{ background: "rgba(245,158,11,.1)", color: "#b45309" }}>HV</span> <span style={{ color: "var(--text-primary)" }}>{current.sino_vi}</span></div>}
                <div className="text-base font-medium mb-3" style={{ color: "var(--text-primary)" }}>{current.meaning}</div>
                {current.example && (
                  <div className="p-3 rounded-xl mb-4" style={{ background: "var(--bg-interactive)", border: "1px solid var(--border-subtle)" }}>
                    <div className="text-sm" style={{ fontFamily: "'Noto Sans JP', sans-serif", color: "var(--text-primary)" }}>{current.example}</div>
                    {current.example_translation && <div className="text-xs mt-1" style={{ color: "var(--text-secondary)" }}>{current.example_translation}</div>}
                  </div>
                )}
                <div className="grid grid-cols-2 gap-3">
                  <button onClick={() => grade(false)} className="py-3 rounded-xl text-sm font-semibold" style={{ background: "rgba(254,226,226,.7)", color: "#dc2626", border: "1px solid rgba(252,165,165,.5)" }}>❌ Chưa biết</button>
                  <button onClick={() => grade(true)} className="py-3 rounded-xl text-sm font-semibold" style={{ background: "rgba(209,250,229,.7)", color: "#16a34a", border: "1px solid rgba(52,211,153,.5)" }}>✅ Đã biết</button>
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
