"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getLearnedWords, toggleLearnedWord } from "@/lib/vocab-progress";
import { useStudyTimer } from "@/hooks/useStudyTimer";

interface VocabWord {
  word: string;
  pos: string;
  ipa: string;
  meaning: string;
  audio_us?: string;
  audio_uk?: string;
}

/* ── Audio helper ───────────────────────────────────────── */
function playWordAudio(word: VocabWord, audioRef: React.MutableRefObject<HTMLAudioElement | null>) {
  const url = word.audio_us || word.audio_uk;
  if (url) {
    if (audioRef.current) { audioRef.current.pause(); }
    const audio = new Audio(url);
    audioRef.current = audio;
    audio.play().catch(() => {});
  } else {
    // Fallback: browser speech synthesis
    if (typeof window !== "undefined" && window.speechSynthesis) {
      window.speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(word.word);
      u.lang = "en-US";
      u.rate = 0.9;
      window.speechSynthesis.speak(u);
    }
  }
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

const POS_MAP: Record<string, string> = {
  n: "noun", v: "verb", adj: "adjective", adv: "adverb",
  prep: "preposition", conj: "conjunction", pron: "pronoun",
  det: "determiner", interj: "interjection",
};
function expandPos(pos: string): string {
  const key = pos.toLowerCase().trim();
  return POS_MAP[key] || pos;
}

type ViewMode = "list" | "flashcard" | "quiz";

/* ═══════════════════════════════════════════════════════ */
export default function VocabDetailPage() {
  const params = useParams();
  const topicId = params.topicId as string;

  const [topic, setTopic] = useState<VocabTopicData | null>(null);
  const [loading, setLoading] = useState(true);
  const [mode, setMode] = useState<ViewMode>("list");
  useStudyTimer();

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
      {mode === "flashcard" && <FlashcardMode words={topic.words} topicSlug={topicId} />}
      {mode === "quiz" && <QuizMode words={topic.words} />}

      <style jsx global>{`
        .vd-page { max-width: 100%; margin: 0 auto; padding: 24px; }
        .vd-breadcrumb { font-size: 13px; color: var(--text-tertiary); margin-bottom: 12px; display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
        .vd-breadcrumb a { color: var(--text-tertiary); text-decoration: none; transition: color 0.2s; position: relative; }
        .vd-breadcrumb a::after { content: ''; position: absolute; bottom: -1px; left: 0; width: 0; height: 1.5px; background: var(--action-primary); transition: width 0.25s ease; }
        .vd-breadcrumb a:hover { color: var(--action-primary); }
        .vd-breadcrumb a:hover::after { width: 100%; }
        .vd-breadcrumb span:last-child { color: var(--text-primary); }
        .vd-title { font-size: 24px; font-weight: 900; color: var(--text-primary); margin: 0; display: flex; align-items: center; gap: 8px; }

        .vd-modes { display: flex; gap: 6px; margin-bottom: 16px; flex-wrap: wrap; }
        .vd-mode-btn {
          padding: 7px 14px; border-radius: 99px; font-weight: 600; font-size: 13px;
          border: 1px solid var(--border-default); background: var(--bg-surface);
          color: var(--text-secondary); cursor: pointer;
          transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
          white-space: nowrap; position: relative; overflow: hidden;
        }
        .vd-mode-btn:hover { border-color: var(--text-primary); color: var(--text-primary); transform: translateY(-1px); box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
        .vd-mode-btn:active { transform: translateY(0) scale(0.97); }
        .vd-mode-btn.active { background: var(--text-primary); color: white; border-color: var(--text-primary); box-shadow: 0 2px 10px rgba(0,0,0,0.15); }

        /* Word list table */
        .vd-table-wrap { border-radius: 14px; border: 1px solid var(--border-default); overflow: hidden; background: var(--bg-surface); box-shadow: var(--shadow-sm); }
        .vd-table { width: 100%; border-collapse: collapse; }
        .vd-table th { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .05em; color: var(--text-tertiary); padding: 10px 14px; text-align: left; background: var(--bg-interactive); border-bottom: 1px solid var(--border-default); }
        .vd-table td { font-size: 13px; color: var(--text-primary); padding: 10px 14px; border-bottom: 1px solid var(--border-default); transition: background 0.2s, padding-left 0.2s; }
        .vd-table tr:last-child td { border-bottom: none; }
        .vd-table tr:hover td { background: var(--bg-interactive); padding-left: 18px; }
        .vd-word { font-weight: 700; color: var(--text-primary); }
        .vd-pos { font-size: 11px; font-weight: 600; color: var(--text-secondary); background: rgba(0,0,0,0.05); padding: 2px 8px; border-radius: 6px; display: inline-block; }
        .vd-ipa { font-size: 12px; color: var(--text-tertiary); font-style: italic; }
        .vd-meaning { color: var(--text-secondary); }
        .vd-speaker-btn {
          background: none; border: none; cursor: pointer; padding: 4px;
          color: var(--text-tertiary);
          transition: color 0.2s, transform 0.2s, background 0.2s;
          display: inline-flex; align-items: center; justify-content: center;
          border-radius: 50%; width: 28px; height: 28px; flex-shrink: 0;
        }
        .vd-speaker-btn:hover { color: var(--text-primary); transform: scale(1.2); background: rgba(0,0,0,0.06); }
        .vd-speaker-btn:active { transform: scale(0.9); }
        .vd-delete-btn {
          background: none; border: none; cursor: pointer; padding: 4px;
          color: var(--text-tertiary); transition: color 0.2s, transform 0.2s;
          display: inline-flex; align-items: center; justify-content: center;
          border-radius: 50%; width: 28px; height: 28px; flex-shrink: 0; opacity: 0;
        }
        .vd-table tr:hover .vd-delete-btn { opacity: 1; }
        .vd-delete-btn:hover { color: #ef4444; transform: scale(1.2); }
        .vd-delete-btn:active { transform: scale(0.9); }
        .vd-delete-btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .vd-fc-speaker {
          position: absolute; top: 12px; right: 12px;
          background: rgba(255,255,255,0.15); border: none; cursor: pointer;
          width: 36px; height: 36px; border-radius: 50%;
          display: flex; align-items: center; justify-content: center;
          color: rgba(255,255,255,0.8); transition: all 0.2s; z-index: 2;
        }
        .vd-fc-speaker:hover { background: rgba(255,255,255,0.3); color: #fff; transform: scale(1.15); }
        .vd-fc-speaker:active { transform: scale(0.9); }

        /* Flashcard */
        .vd-fc-wrap { perspective: 1000px; margin: 0 auto 16px; max-width: 400px; cursor: pointer; }
        .vd-fc-inner {
          position: relative; width: 100%; min-height: 200px;
          transition: transform 0.6s cubic-bezier(0.4, 0, 0.2, 1);
          transform-style: preserve-3d;
        }
        .vd-fc-inner.flipped { transform: rotateY(180deg); }
        .vd-fc-face {
          position: absolute; inset: 0; border-radius: 18px;
          -webkit-backface-visibility: hidden;
          backface-visibility: hidden;
          display: flex; flex-direction: column; align-items: center; justify-content: center;
          padding: 28px 20px; text-align: center;
        }
        .vd-fc-front {
          background: linear-gradient(135deg, #1e293b, #334155); color: white;
        }
        .vd-fc-back {
          background: var(--bg-surface); border: 2px solid var(--border-strong);
          transform: rotateY(180deg);
        }
        .vd-fc-word { font-size: 26px; font-weight: 900; margin-bottom: 6px; }
        .vd-fc-ipa { font-size: 14px; opacity: 0.8; }
        .vd-fc-hint { font-size: 12px; opacity: 0.6; margin-top: 10px; }
        .vd-fc-hint-subtle {
          position: absolute; bottom: 10px; left: 0; right: 0; text-align: center;
          font-size: 11px; letter-spacing: 0.5px; text-transform: lowercase;
          color: rgba(255,255,255,0.3); font-weight: 500;
          animation: vdPulse 2.5s ease-in-out infinite;
        }
        @keyframes vdPulse { 0%, 100% { opacity: 0.3; } 50% { opacity: 0.6; } }
        .vd-fc-meaning { font-size: 20px; font-weight: 800; color: var(--text-primary); margin-bottom: 6px; }
        .vd-fc-pos-tag { font-size: 12px; font-weight: 600; color: var(--text-secondary); background: rgba(0,0,0,0.06); padding: 3px 10px; border-radius: 6px; margin-bottom: 8px; }
        .vd-fc-pos-corner {
          position: absolute; top: 10px; right: 12px;
          font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;
          color: var(--text-secondary); background: rgba(0,0,0,0.05); padding: 2px 10px; border-radius: 6px;
        }

        .vd-fc-controls { display: flex; gap: 8px; justify-content: center; }
        .vd-fc-btn {
          flex: 1; max-width: 160px; padding: 11px; border-radius: 10px;
          font-weight: 700; font-size: 13px; border: none; cursor: pointer;
          transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .vd-fc-btn:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        .vd-fc-btn:active { transform: translateY(0) scale(0.97); }
        .vd-fc-prev { background: var(--bg-interactive); color: var(--text-secondary); }
        .vd-fc-prev:hover { background: var(--bg-interactive-hover); }
        .vd-fc-next { background: var(--text-primary); color: white; }
        .vd-fc-next:hover { opacity: 0.9; box-shadow: 0 4px 16px rgba(0,0,0,0.2); }
        .vd-fc-progress { text-align: center; font-size: 13px; color: var(--text-tertiary); margin-bottom: 12px; }

        /* Quiz */
        .vd-quiz-wrap { max-width: 560px; margin: 0 auto; }
        .vd-quiz-progress { display: flex; align-items: center; gap: 14px; margin-bottom: 20px; }
        .vd-quiz-track { flex: 1; height: 6px; background: var(--bg-interactive); border-radius: 99px; overflow: hidden; position: relative; }
        .vd-quiz-fill {
          height: 100%; border-radius: 99px;
          background: linear-gradient(90deg, #6366f1, #8b5cf6);
          transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
          box-shadow: 0 0 8px rgba(99,102,241,0.4);
        }
        .vd-quiz-count {
          font-size: 12px; font-weight: 800; letter-spacing: 0.5px;
          color: #6366f1; background: rgba(99,102,241,0.1);
          padding: 4px 12px; border-radius: 99px; white-space: nowrap;
        }
        .vd-quiz-q {
          background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
          border-radius: 20px; padding: 32px 24px;
          margin-bottom: 20px; text-align: center;
          box-shadow: 0 8px 32px rgba(30,41,59,0.25), 0 0 0 1px rgba(255,255,255,0.05) inset;
          animation: vdSlideDown 0.4s cubic-bezier(0.16, 1, 0.3, 1);
          position: relative; overflow: hidden;
        }
        .vd-quiz-q::before {
          content: ''; position: absolute; top: -50%; right: -50%; width: 100%; height: 100%;
          background: radial-gradient(circle, rgba(99,102,241,0.15) 0%, transparent 70%);
          pointer-events: none;
        }
        @keyframes vdSlideDown { from { opacity: 0; transform: translateY(-12px) scale(0.98); } to { opacity: 1; transform: translateY(0) scale(1); } }
        .vd-quiz-q-word { font-size: 28px; font-weight: 900; color: #fff; margin: 0 0 6px; position: relative; }
        .vd-quiz-q-ipa { font-size: 13px; color: rgba(255,255,255,0.5); margin: 0 0 4px; font-style: italic; }
        .vd-quiz-q-word-row { display: flex; align-items: center; justify-content: center; gap: 10px; margin-bottom: 8px; position: relative; }
        .vd-quiz-q .vd-speaker-btn { color: rgba(255,255,255,0.6); }
        .vd-quiz-q .vd-speaker-btn:hover { color: #fff; background: rgba(255,255,255,0.15); }
        .vd-quiz-q-ipa-big {
          font-size: 15px; color: rgba(255,255,255,0.7); margin: 0 0 8px;
          font-style: italic; font-weight: 500;
          background: rgba(255,255,255,0.08); display: inline-block;
          padding: 4px 16px; border-radius: 8px;
          letter-spacing: 0.3px; backdrop-filter: blur(4px);
        }
        .vd-quiz-q-pos {
          font-size: 11px; font-weight: 700; text-transform: uppercase;
          letter-spacing: 1px; color: rgba(255,255,255,0.45);
        }
        .vd-quiz-q-meaning { font-size: 20px; font-weight: 800; color: #fff; margin: 0 0 6px; line-height: 1.5; position: relative; }
        .vd-quiz-label {
          font-size: 12px; color: var(--text-tertiary); margin-bottom: 12px;
          text-align: center; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;
        }
        .vd-quiz-opts { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
        .vd-quiz-opt {
          display: flex; align-items: center; gap: 12px;
          border-radius: 14px; padding: 16px;
          text-align: left; font-size: 14px; font-weight: 600;
          border: 2px solid var(--border-default);
          background: var(--bg-surface); color: var(--text-primary); cursor: pointer;
          transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
          box-shadow: 0 1px 3px rgba(0,0,0,0.04);
          position: relative; overflow: hidden;
        }
        .vd-quiz-opt::after {
          content: ''; position: absolute; inset: 0; border-radius: 12px;
          background: linear-gradient(135deg, transparent 60%, rgba(99,102,241,0.03) 100%);
          pointer-events: none;
        }
        .vd-quiz-opt:hover {
          border-color: #6366f1; transform: translateY(-2px);
          box-shadow: 0 6px 20px rgba(99,102,241,0.12);
        }
        .vd-quiz-opt:active { transform: translateY(0) scale(0.98); }
        .vd-quiz-opt.correct {
          border-color: #22c55e; background: linear-gradient(135deg, rgba(34,197,94,0.06), rgba(34,197,94,0.12));
          color: #15803d; animation: vdCorrect 0.4s ease;
          box-shadow: 0 4px 16px rgba(34,197,94,0.15);
        }
        .vd-quiz-opt.wrong {
          border-color: #ef4444; background: linear-gradient(135deg, rgba(239,68,68,0.06), rgba(239,68,68,0.12));
          color: #dc2626; animation: vdShake 0.4s ease;
        }
        .vd-quiz-opt.dim { opacity: 0.4; pointer-events: none; }
        @keyframes vdCorrect { 0% { transform: scale(1); } 50% { transform: scale(1.02); } 100% { transform: scale(1); } }
        @keyframes vdShake { 0%, 100% { transform: translateX(0); } 20% { transform: translateX(-6px); } 40% { transform: translateX(5px); } 60% { transform: translateX(-3px); } 80% { transform: translateX(2px); } }
        .vd-quiz-key {
          flex-shrink: 0; width: 32px; height: 32px; border-radius: 10px;
          display: flex; align-items: center; justify-content: center;
          font-size: 12px; font-weight: 800;
          background: var(--bg-interactive); color: var(--text-tertiary);
          border: none; transition: all 0.25s;
        }
        .vd-quiz-opt:hover .vd-quiz-key { background: rgba(99,102,241,0.1); color: #6366f1; }
        .vd-quiz-key.correct { background: #22c55e; color: white; }
        .vd-quiz-key.wrong { background: #ef4444; color: white; }
        .vd-quiz-key.selected { background: var(--text-primary); color: white; }

        .vd-result { text-align: center; padding: 40px 20px; animation: vdFadeUp 0.5s ease; }
        @keyframes vdFadeUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
        .vd-result-icon { font-size: 64px; margin-bottom: 12px; animation: vdBounce 0.6s ease; }
        .vd-result-score { font-size: 52px; font-weight: 900; margin-bottom: 4px; animation: vdBounce 0.6s ease; }
        @keyframes vdBounce { 0% { transform: scale(0.5); opacity: 0; } 60% { transform: scale(1.1); } 100% { transform: scale(1); opacity: 1; } }
        .vd-result-label { font-size: 16px; font-weight: 700; color: var(--text-primary); margin-bottom: 4px; }
        .vd-result-detail { font-size: 14px; color: var(--text-secondary); margin-bottom: 24px; }
        .vd-result-btn {
          padding: 14px 32px; border-radius: 14px; font-weight: 700; font-size: 15px;
          border: none; cursor: pointer;
          background: linear-gradient(135deg, #6366f1, #8b5cf6); color: white;
          transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
          box-shadow: 0 4px 16px rgba(99,102,241,0.3);
        }
        .vd-result-btn:hover { transform: translateY(-2px); box-shadow: 0 6px 24px rgba(99,102,241,0.4); }
        .vd-result-btn:active { transform: translateY(0) scale(0.97); }
        .vd-quiz-next-wrap {
          text-align: center; margin-top: 20px; animation: vd-fadeIn 0.3s ease;
        }
        .vd-quiz-next-btn {
          padding: 12px 32px; border-radius: 12px; font-weight: 700; font-size: 14px;
          border: none; cursor: pointer;
          background: linear-gradient(135deg, #6366f1, #8b5cf6); color: white;
          transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
          box-shadow: 0 3px 12px rgba(99,102,241,0.25);
        }
        .vd-quiz-next-btn:hover { transform: translateY(-2px); box-shadow: 0 5px 20px rgba(99,102,241,0.35); }
        .vd-quiz-next-btn:active { transform: translateY(0) scale(0.97); }

        .vd-quiz-reveal-ipa {
          display: flex; align-items: center; justify-content: center; gap: 10px;
          margin-top: 14px; padding: 10px 16px; border-radius: 12px;
          background: rgba(99,102,241,0.06); border: 1px solid rgba(99,102,241,0.15);
          animation: vd-fadeIn 0.3s ease;
        }
        .vd-quiz-reveal-word { font-size: 16px; font-weight: 800; color: var(--text-primary); }
        .vd-quiz-reveal-phonetic { font-size: 13px; color: var(--text-tertiary); font-style: italic; }
        @keyframes vd-fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }

        /* Quiz sub-tabs */
        .vd-quiz-subtabs { display: flex; gap: 0; margin-bottom: 20px; border-radius: 10px; overflow: hidden; border: 1px solid var(--border-default); background: var(--bg-interactive); }
        .vd-quiz-subtab {
          flex: 1; padding: 9px 16px; font-size: 13px; font-weight: 700;
          border: none; background: transparent; color: var(--text-tertiary);
          cursor: pointer; transition: all 0.2s; text-align: center;
        }
        .vd-quiz-subtab:not(:last-child) { border-right: 1px solid var(--border-default); }
        .vd-quiz-subtab.active { background: var(--bg-surface); color: var(--text-primary); box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
        .vd-quiz-subtab:hover:not(.active) { color: var(--text-secondary); background: rgba(0,0,0,0.02); }

        /* Match game */
        .vd-match-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
        .vd-match-hearts { display: flex; gap: 4px; }
        .vd-match-heart { font-size: 22px; transition: transform 0.3s, opacity 0.3s, filter 0.3s; }
        .vd-match-heart.lost { opacity: 0.2; transform: scale(0.7); filter: grayscale(1); }
        .vd-match-score { font-size: 13px; font-weight: 700; color: var(--text-tertiary); }
        .vd-match-grid {
          display: grid; gap: 0;
          grid-template-columns: repeat(4, 1fr);
          border-radius: 14px; overflow: hidden;
          border: 1px solid var(--border-default);
          box-shadow: var(--shadow-sm);
        }
        .vd-match-tile {
          position: relative; padding: 16px 8px;
          font-size: 13px; font-weight: 600; text-align: center;
          border: none; border-right: 1px solid var(--border-default); border-bottom: 1px solid var(--border-default);
          background: var(--bg-surface); color: var(--text-primary); cursor: pointer;
          transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
          min-height: 64px; display: flex; align-items: center; justify-content: center;
          word-break: break-word; line-height: 1.35;
          user-select: none; border-radius: 0;
        }
        .vd-match-tile:nth-child(4n) { border-right: none; }
        .vd-match-grid > .vd-match-tile:nth-last-child(-n+4) { border-bottom: none; }
        .vd-match-tile:hover:not(.matched):not(.disabled) { background: rgba(99,102,241,0.04); }
        .vd-match-tile:active:not(.matched):not(.disabled) { background: rgba(99,102,241,0.08); }
        .vd-match-tile.selected { background: rgba(99,102,241,0.1); color: #6366f1; box-shadow: inset 0 0 0 2px #6366f1; }
        .vd-match-tile.en .vd-match-tag { color: #6366f1; }
        .vd-match-tile.vi .vd-match-tag { color: #f59e0b; }
        .vd-match-tile.matched { background: rgba(34,197,94,0.08); color: #15803d; opacity: 0.6; cursor: default; pointer-events: none; }
        .vd-match-tile.wrong { animation: vdShake 0.45s ease; background: rgba(239,68,68,0.08); box-shadow: inset 0 0 0 2px #ef4444; }
        .vd-match-tile .vd-match-tag {
          position: absolute; top: 3px; right: 5px; font-size: 9px; font-weight: 700;
          text-transform: uppercase; letter-spacing: 0.5px;
          opacity: 0.6;
        }
        .vd-match-tile.disabled { opacity: 0.5; cursor: default; pointer-events: none; }
        .vd-match-msg {
          text-align: center; padding: 32px 16px;
          animation: vdFadeUp 0.5s ease;
        }
        .vd-match-msg-icon { font-size: 56px; margin-bottom: 12px; }
        .vd-match-msg-title { font-size: 22px; font-weight: 900; color: var(--text-primary); margin-bottom: 6px; }
        .vd-match-msg-sub { font-size: 14px; color: var(--text-secondary); margin-bottom: 20px; }

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
          .vd-table th:nth-child(5), .vd-table td:nth-child(5) { display: none; }
          .vd-fc-wrap { max-width: 100%; }
          .vd-fc-inner { min-height: 180px; }
          .vd-fc-face { padding: 24px 16px; }
          .vd-fc-word { font-size: 22px; }
          .vd-fc-meaning { font-size: 18px; }
          .vd-fc-controls { gap: 6px; }
          .vd-fc-btn { max-width: none; padding: 10px; font-size: 13px; }
          .vd-fc-progress { margin-bottom: 10px; font-size: 12px; }
          .vd-quiz-q { padding: 20px 16px; border-radius: 16px; }
          .vd-quiz-q-word { font-size: 22px; }
          .vd-quiz-opts { grid-template-columns: 1fr; gap: 8px; }
          .vd-quiz-opt { padding: 12px; font-size: 13px; border-radius: 12px; }
          .vd-quiz-key { width: 28px; height: 28px; font-size: 11px; border-radius: 8px; }
          .vd-match-grid { grid-template-columns: repeat(3, 1fr); }
          .vd-match-tile { padding: 10px 6px; font-size: 12px; min-height: 50px; }
          .vd-match-tile:nth-child(4n) { border-right: 1px solid var(--border-default); }
          .vd-match-tile:nth-child(3n) { border-right: none; }
          .vd-match-grid > .vd-match-tile:nth-last-child(-n+4) { border-bottom: 1px solid var(--border-default); }
          .vd-match-grid > .vd-match-tile:nth-last-child(-n+3) { border-bottom: none; }
        }
      `}</style>
    </div>
  );
}

/* ─── Word List ─────────────────────────────────────── */
function WordList({ words }: { words: VocabWord[] }) {
  const audioRef = useRef<HTMLAudioElement | null>(null);

  return (
    <div className="vd-table-wrap">
      <table className="vd-table">
        <thead>
          <tr>
            <th>STT</th>
            <th style={{ width: 40 }}></th>
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
              <td style={{ padding: "10px 4px 10px 0" }}>
                <button
                  className="vd-speaker-btn"
                  onClick={() => playWordAudio(w, audioRef)}
                  title="Nghe phát âm"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
                    <path d="M19.07 4.93a10 10 0 010 14.14M15.54 8.46a5 5 0 010 7.07" />
                  </svg>
                </button>
              </td>
              <td className="vd-word">{w.word}</td>
              <td><span className="vd-pos">{expandPos(w.pos)}</span></td>
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
function FlashcardMode({ words, topicSlug }: { words: VocabWord[]; topicSlug: string }) {
  const [idx, setIdx] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [learnedWords, setLearnedWords] = useState<Set<string>>(() => {
    return new Set(getLearnedWords(topicSlug));
  });
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const w = words[idx];
  const prev = () => { setFlipped(false); setIdx((idx - 1 + words.length) % words.length); };
  const next = () => { setFlipped(false); setIdx((idx + 1) % words.length); };

  // Auto-play audio when card changes
  useEffect(() => {
    if (words[idx]) {
      // Small delay so the card transition starts first
      const t = setTimeout(() => playWordAudio(words[idx], audioRef), 200);
      return () => clearTimeout(t);
    }
  }, [idx, words]);

  return (
    <div>
      <div className="vd-fc-progress">
        {idx + 1} / {words.length}
        {learnedWords.size > 0 && <span style={{ marginLeft: 12, color: "#22c55e", fontWeight: 700 }}>✓ {learnedWords.size} đã thuộc</span>}
      </div>

      <div className="vd-fc-wrap" onClick={() => setFlipped(!flipped)}>
        <div className={`vd-fc-inner ${flipped ? "flipped" : ""}`}>
          <div className="vd-fc-face vd-fc-front">
            {/* Speaker button */}
            <button
              className="vd-fc-speaker"
              onClick={(e) => { e.stopPropagation(); playWordAudio(w, audioRef); }}
              title="Nghe phát âm"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
                <path d="M19.07 4.93a10 10 0 010 14.14M15.54 8.46a5 5 0 010 7.07" />
              </svg>
            </button>
            <div className="vd-fc-word">{w.word}</div>
            <div className="vd-fc-ipa">{w.ipa}</div>
            <div className="vd-fc-hint-subtle">nhấn để xem nghĩa</div>
          </div>
          <div className="vd-fc-face vd-fc-back">
            <div className="vd-fc-pos-corner">{expandPos(w.pos)}</div>
            <div className="vd-fc-meaning">{w.meaning}</div>
          </div>
        </div>
      </div>

      <div className="vd-fc-controls">
        <button className="vd-fc-btn vd-fc-prev" onClick={prev}>← Trước</button>
        <button
          className="vd-fc-btn"
          style={{
            background: learnedWords.has(w.word) ? "rgba(34,197,94,0.1)" : "var(--bg-interactive)",
            color: learnedWords.has(w.word) ? "#15803d" : "var(--text-secondary)",
          }}
          onClick={() => {
            const updated = toggleLearnedWord(topicSlug, w.word);
            setLearnedWords(new Set(updated));
          }}
        >
          {learnedWords.has(w.word) ? "✓ Đã thuộc" : "Đã thuộc"}
        </button>
        <button className="vd-fc-btn vd-fc-next" onClick={next}>Tiếp →</button>
      </div>
    </div>
  );
}

/* ─── Quiz Mode ─────────────────────────────────────── */
type QuizType = "en_to_vi" | "vi_to_en";

interface QuizQ {
  type: QuizType;
  prompt: string;        // word (en_to_vi) or meaning (vi_to_en)
  ipa: string;
  pos: string;
  correctAnswer: string; // meaning (en_to_vi) or word (vi_to_en)
  options: string[];
  correctIdx: number;
  audioWord: VocabWord;  // for audio playback
}

function QuizMode({ words }: { words: VocabWord[] }) {
  const [subMode, setSubMode] = useState<"quiz" | "match">("quiz");

  return (
    <div>
      <div className="vd-quiz-subtabs">
        <button className={`vd-quiz-subtab ${subMode === "quiz" ? "active" : ""}`} onClick={() => setSubMode("quiz")}>
          ✍️ Trắc nghiệm
        </button>
        <button className={`vd-quiz-subtab ${subMode === "match" ? "active" : ""}`} onClick={() => setSubMode("match")}>
          🧩 Ghép từ
        </button>
      </div>
      {subMode === "quiz" ? <QuizQuestions words={words} /> : <MatchMode words={words} />}
    </div>
  );
}

function QuizQuestions({ words }: { words: VocabWord[] }) {
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const [questions] = useState<QuizQ[]>(() => {
    return shuffle(words).map(w => {
      const type: QuizType = Math.random() < 0.5 ? "en_to_vi" : "vi_to_en";

      if (type === "en_to_vi") {
        const wrongOpts = shuffle(words.filter(x => x.meaning !== w.meaning)).slice(0, 3);
        const options = shuffle([w, ...wrongOpts]);
        return {
          type,
          prompt: w.word,
          ipa: w.ipa,
          pos: w.pos,
          correctAnswer: w.meaning,
          options: options.map(o => o.meaning),
          correctIdx: options.findIndex(o => o.meaning === w.meaning),
          audioWord: w,
        };
      } else {
        const wrongOpts = shuffle(words.filter(x => x.word !== w.word)).slice(0, 3);
        const options = shuffle([w, ...wrongOpts]);
        return {
          type,
          prompt: w.meaning,
          ipa: w.ipa,
          pos: w.pos,
          correctAnswer: w.word,
          options: options.map(o => o.word),
          correctIdx: options.findIndex(o => o.word === w.word),
          audioWord: w,
        };
      }
    });
  });

  const [current, setCurrent] = useState(0);
  const [selected, setSelected] = useState<number | null>(null);
  const [correct, setCorrect] = useState(0);
  const [done, setDone] = useState(false);

  const q = questions[current];

  // Auto-play audio for en_to_vi questions when question changes
  useEffect(() => {
    if (q && q.type === "en_to_vi") {
      const t = setTimeout(() => playWordAudio(q.audioWord, audioRef), 200);
      return () => clearTimeout(t);
    }
  }, [current, q]);

  const handleSelect = (idx: number) => {
    if (selected !== null) return;
    setSelected(idx);
    if (idx === q.correctIdx) setCorrect(c => c + 1);
    // Always auto-play the correct word's audio after answering
    setTimeout(() => playWordAudio(q.audioWord, audioRef), 300);
  };

  const handleNext = () => {
    if (current + 1 >= questions.length) { setDone(true); }
    else { setCurrent(c => c + 1); setSelected(null); }
  };

  if (done) {
    const pct = Math.round(correct / questions.length * 100);
    const emoji = pct >= 90 ? "🏆" : pct >= 80 ? "🎉" : pct >= 60 ? "👍" : "💪";
    const label = pct >= 90 ? "Xuất sắc!" : pct >= 80 ? "Tuyệt vời!" : pct >= 60 ? "Khá tốt!" : "Cần ôn thêm!";
    return (
      <div className="vd-result">
        <div className="vd-result-icon">{emoji}</div>
        <div className="vd-result-score" style={{ color: pct >= 80 ? "#10b981" : pct >= 60 ? "#f59e0b" : "#ef4444" }}>
          {pct}%
        </div>
        <div className="vd-result-label">{label}</div>
        <div className="vd-result-detail">
          {correct}/{questions.length} câu đúng
        </div>
        <button className="vd-result-btn" onClick={() => { setCurrent(0); setSelected(null); setCorrect(0); setDone(false); }}>
          🔄 Làm lại
        </button>
      </div>
    );
  }

  return (
    <div className="vd-quiz-wrap">
      <div className="vd-quiz-progress">
        <div className="vd-quiz-track">
          <div className="vd-quiz-fill" style={{ width: `${((current + (selected !== null ? 1 : 0)) / questions.length) * 100}%` }} />
        </div>
        <div className="vd-quiz-count">{current + 1} / {questions.length}</div>
      </div>

      <div className="vd-quiz-q">
        {q.type === "en_to_vi" ? (
          <>
            <div className="vd-quiz-q-word-row">
              <button
                className="vd-speaker-btn"
                onClick={() => playWordAudio(q.audioWord, audioRef)}
                title="Nghe phát âm"
              >
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
                  <path d="M19.07 4.93a10 10 0 010 14.14M15.54 8.46a5 5 0 010 7.07" />
                </svg>
              </button>
              <span className="vd-quiz-q-word">{q.prompt}</span>
            </div>
            <p className="vd-quiz-q-ipa-big">{q.ipa}</p>
            <p className="vd-quiz-q-pos">{expandPos(q.pos)}</p>
          </>
        ) : (
          <>
            <p className="vd-quiz-q-meaning">{q.prompt}</p>
            <p className="vd-quiz-q-pos">{expandPos(q.pos)}</p>
          </>
        )}
      </div>

      <p className="vd-quiz-label">
        {q.type === "en_to_vi" ? "CHỌN NGHĨA ĐÚNG" : "CHỌN TỪ TIẾNG ANH ĐÚNG"}
      </p>
      <div className="vd-quiz-opts">
        {q.options.map((opt, j) => {
          let cls = "vd-quiz-opt";
          let keyCls = "vd-quiz-key";
          if (selected !== null) {
            if (j === q.correctIdx) { cls += " correct"; keyCls += " correct"; }
            else if (j === selected) { cls += " wrong"; keyCls += " wrong"; }
            else { cls += " dim"; }
          }
          return (
            <button key={j} className={cls} onClick={() => handleSelect(j)} disabled={selected !== null}>
              <span className={keyCls}>{String.fromCharCode(65 + j)}</span>
              {opt}
            </button>
          );
        })}
      </div>

      {selected !== null && (
        <div className="vd-quiz-next-wrap">
          <button className="vd-quiz-next-btn" onClick={handleNext}>
            {current + 1 >= questions.length ? "📊 Xem kết quả" : "Tiếp theo →"}
          </button>
        </div>
      )}
    </div>
  );
}

/* ─── Match Game Mode ─────────────────────────────── */
interface MatchTile {
  id: number;
  text: string;
  pairId: number;
  type: "en" | "vi";
}

function MatchMode({ words }: { words: VocabWord[] }) {
  const MAX_MISTAKES = 3;
  const GRID_PAIRS = Math.min(8, words.length);

  const [tiles, setTiles] = useState<MatchTile[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [matched, setMatched] = useState<Set<number>>(new Set());
  const [wrongIds, setWrongIds] = useState<Set<number>>(new Set());
  const [mistakes, setMistakes] = useState(0);
  const [gameOver, setGameOver] = useState(false);
  const [won, setWon] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Initialize / restart
  const initGame = useCallback(() => {
    const picked = shuffle(words).slice(0, GRID_PAIRS);
    const tileList: MatchTile[] = [];
    picked.forEach((w, i) => {
      tileList.push({ id: i * 2, text: w.word, pairId: i, type: "en" });
      tileList.push({ id: i * 2 + 1, text: w.meaning, pairId: i, type: "vi" });
    });
    setTiles(shuffle(tileList));
    setSelected(null);
    setMatched(new Set());
    setWrongIds(new Set());
    setMistakes(0);
    setGameOver(false);
    setWon(false);
  }, [words, GRID_PAIRS]);

  useEffect(() => { initGame(); }, [initGame]);

  const handleTileClick = (tile: MatchTile) => {
    if (gameOver || matched.has(tile.id) || wrongIds.size > 0) return;

    if (selected === null) {
      setSelected(tile.id);
      // Play audio if it's an English tile
      if (tile.type === "en") {
        const w = words.find(w => w.word === tile.text);
        if (w) playWordAudio(w, audioRef);
      }
      return;
    }

    const firstTile = tiles.find(t => t.id === selected)!;
    if (firstTile.id === tile.id) { setSelected(null); return; } // deselect
    if (firstTile.type === tile.type) {
      // Same type clicked — switch selection
      setSelected(tile.id);
      if (tile.type === "en") {
        const w = words.find(w => w.word === tile.text);
        if (w) playWordAudio(w, audioRef);
      }
      return;
    }

    // Check match
    if (firstTile.pairId === tile.pairId) {
      // Correct match!
      const newMatched = new Set(matched);
      newMatched.add(firstTile.id);
      newMatched.add(tile.id);
      setMatched(newMatched);
      setSelected(null);
      // Check win
      if (newMatched.size === tiles.length) {
        setWon(true);
        setGameOver(true);
      }
    } else {
      // Wrong match
      const newMistakes = mistakes + 1;
      setMistakes(newMistakes);
      setWrongIds(new Set([firstTile.id, tile.id]));
      setTimeout(() => {
        setWrongIds(new Set());
        setSelected(null);
        if (newMistakes >= MAX_MISTAKES) {
          setGameOver(true);
        }
      }, 700);
    }
  };

  if (tiles.length === 0) return null;

  // Game over / win screen
  if (gameOver) {
    return (
      <div className="vd-match-msg">
        <div className="vd-match-msg-icon">{won ? "🎉" : "😢"}</div>
        <div className="vd-match-msg-title">
          {won ? "Tuyệt vời!" : "Hết lượt!"}
        </div>
        <div className="vd-match-msg-sub">
          {won
            ? `Ghép đúng tất cả ${GRID_PAIRS} cặp từ${mistakes === 0 ? " — Hoàn hảo! ✨" : ` với ${mistakes} lỗi`}`
            : `Đã sai ${MAX_MISTAKES} lần. Thử lại nhé!`}
        </div>
        <button className="vd-result-btn" onClick={initGame}>🔄 Chơi lại</button>
      </div>
    );
  }

  return (
    <div>
      <div className="vd-match-header">
        <div className="vd-match-hearts">
          {Array.from({ length: MAX_MISTAKES }).map((_, i) => (
            <span key={i} className={`vd-match-heart ${i < mistakes ? "lost" : ""}`}>❤️</span>
          ))}
        </div>
        <div className="vd-match-score">
          {matched.size / 2} / {GRID_PAIRS} cặp
        </div>
      </div>

      <div className="vd-match-grid">
        {tiles.map(tile => {
          const isMatched = matched.has(tile.id);
          const isSelected = selected === tile.id;
          const isWrong = wrongIds.has(tile.id);
          let cls = `vd-match-tile ${tile.type}`;
          if (isMatched) cls += " matched";
          if (isSelected) cls += " selected";
          if (isWrong) cls += " wrong";

          return (
            <button
              key={tile.id}
              className={cls}
              onClick={() => handleTileClick(tile)}
              disabled={isMatched}
            >
              <span className="vd-match-tag">{tile.type === "en" ? "EN" : "VI"}</span>
              {tile.text}
            </button>
          );
        })}
      </div>
    </div>
  );
}
