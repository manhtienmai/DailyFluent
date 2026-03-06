"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

interface GrammarTopic {
  topic_id: string;
  emoji: string;
  title: string;
  title_vi: string;
  description: string;
  question_count: number;
  difficulty: "easy" | "medium" | "hard";
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

const DIFF_COLORS: Record<string, string> = {
  easy: "rgba(34,197,94,0.1)", medium: "rgba(245,158,11,0.1)", hard: "rgba(239,68,68,0.1)",
};
const DIFF_TEXT: Record<string, string> = {
  easy: "#22c55e", medium: "#f59e0b", hard: "#ef4444",
};
const DIFF_LABEL: Record<string, string> = { easy: "Cơ bản", medium: "Trung bình", hard: "Nâng cao" };

export default function GrammarTopicsPage() {
  const [mounted, setMounted] = useState(false);
  const [topics, setTopics] = useState<GrammarTopic[]>([]);

  useEffect(() => {
    fetch(`${API_BASE}/api/v1/exam/english/grammar-topics`)
      .then(r => r.json())
      .then(data => setTopics(Array.isArray(data) ? data : []))
      .catch(() => {});
    setTimeout(() => setMounted(true), 50);
  }, []);

  return (
    <div className="gr-page" style={{ opacity: mounted ? 1 : 0, transition: "opacity 0.5s" }}>
      <nav className="gr-breadcrumb">
        <Link href="/exam/english">English Lớp 10</Link>
        <span>/</span>
        <span>Ngữ pháp</span>
      </nav>

      <div className="gr-header">
        <h1 className="gr-title">📐 Ngữ pháp tiếng Anh</h1>
        <div className="gr-stats">
          <span className="gr-chip" style={{ background: "rgba(99,102,241,.08)", color: "#6366f1" }}>📚 {topics.length} chủ đề</span>
          <span className="gr-chip" style={{ background: "rgba(34,197,94,.08)", color: "#16a34a" }}>✏️ {topics.reduce((s, t) => s + t.question_count, 0)} câu</span>
          <span className="gr-chip" style={{ background: "rgba(168,85,247,.08)", color: "#9333ea" }}>🎯 3 cấp độ</span>
        </div>
      </div>

      <div className="gr-topics">
        {topics.map((topic, idx) => (
          <Link
            key={topic.topic_id}
            href={`/exam/english/grammar/${topic.topic_id}`}
            className="gr-topic-card"
            style={{ animationDelay: `${idx * 0.04}s` }}
          >
            <div className="gr-topic-emoji">{topic.emoji}</div>
            <div className="gr-topic-body">
              <div className="gr-topic-header">
                <h3 className="gr-topic-title">{topic.title}</h3>
                <span className="gr-topic-badge" style={{ background: DIFF_COLORS[topic.difficulty], color: DIFF_TEXT[topic.difficulty] }}>
                  {DIFF_LABEL[topic.difficulty]}
                </span>
              </div>
              <p className="gr-topic-vi">{topic.title_vi}</p>
              <p className="gr-topic-desc">{topic.description}</p>
            </div>
            <div className="gr-topic-right">
              <div className="gr-topic-count">{topic.question_count} câu</div>
              <div className="gr-topic-arrow">→</div>
            </div>
          </Link>
        ))}
      </div>

      <style jsx global>{`
        .gr-page { max-width: 100%; margin: 0 auto; padding: 24px 24px; }
        .gr-breadcrumb { font-size: 13px; color: var(--text-tertiary); margin-bottom: 16px; display: flex; align-items: center; gap: 6px; }
        .gr-breadcrumb a { color: var(--text-tertiary); text-decoration: none; }
        .gr-breadcrumb a:hover { color: var(--action-primary); }
        .gr-breadcrumb span:last-child { color: var(--text-primary); }
        .gr-title { font-size: 22px; font-weight: 900; color: var(--text-primary); margin: 0; }

        .gr-header { display: flex; align-items: baseline; justify-content: space-between; gap: 16px; margin-bottom: 16px; flex-wrap: wrap; }
        .gr-stats { display: flex; align-items: center; gap: 6px; }
        .gr-chip { display: inline-flex; align-items: center; gap: 4px; padding: 4px 10px; border-radius: 99px; font-size: 12px; font-weight: 600; white-space: nowrap; }

        .gr-topics { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
        @media (max-width: 768px) { .gr-topics { grid-template-columns: 1fr; } }
        .gr-topic-card {
          display: flex; align-items: center; gap: 14px;
          border-radius: 14px; border: 1px solid var(--border-default); background: var(--bg-surface);
          padding: 14px 16px; text-decoration: none; transition: all 0.25s;
          animation: grSlideUp 0.35s ease-out both;
        }
        .gr-topic-card:hover { box-shadow: var(--shadow-lg); transform: translateY(-2px); border-color: var(--action-primary); }

        .gr-topic-emoji { font-size: 32px; flex-shrink: 0; width: 48px; height: 48px; display: flex; align-items: center; justify-content: center; background: var(--bg-interactive); border-radius: 12px; transition: transform 0.3s; }
        .gr-topic-card:hover .gr-topic-emoji { transform: scale(1.08) rotate(4deg); }
        .gr-topic-body { flex: 1; min-width: 0; }
        .gr-topic-header { display: flex; align-items: center; gap: 8px; margin-bottom: 2px; flex-wrap: wrap; }
        .gr-topic-title { font-size: 14px; font-weight: 700; color: var(--text-primary); margin: 0; transition: color 0.2s; }
        .gr-topic-card:hover .gr-topic-title { color: var(--action-primary); }
        .gr-topic-badge { padding: 2px 8px; border-radius: 99px; font-size: 10px; font-weight: 700; flex-shrink: 0; }
        .gr-topic-vi { font-size: 12px; color: var(--text-secondary); font-weight: 500; margin: 0; }
        .gr-topic-desc { font-size: 11px; color: var(--text-tertiary); margin: 2px 0 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

        .gr-topic-right { flex-shrink: 0; text-align: right; }
        .gr-topic-count { font-size: 12px; color: var(--text-tertiary); font-weight: 600; }
        .gr-topic-arrow { font-size: 13px; color: var(--action-primary); font-weight: 700; opacity: 0; transition: opacity 0.2s; }
        .gr-topic-card:hover .gr-topic-arrow { opacity: 1; }

        @keyframes grSlideUp {
          from { opacity: 0; transform: translateY(12px); }
          to { opacity: 1; transform: translateY(0); }
        }

        @media (max-width: 640px) {
          .gr-page { padding: 16px; }
          .gr-breadcrumb { font-size: 12px; margin-bottom: 10px; }
          .gr-title { font-size: 18px; }
          .gr-header { gap: 8px; margin-bottom: 12px; }
          .gr-stats { gap: 4px; }
          .gr-chip { font-size: 11px; padding: 3px 8px; }
          .gr-topic-card { padding: 12px 14px; gap: 10px; }
          .gr-topic-emoji { font-size: 26px; width: 40px; height: 40px; border-radius: 10px; }
          .gr-topic-title { font-size: 13px; }
          .gr-topic-badge { font-size: 9px; padding: 2px 6px; }
          .gr-topic-vi { font-size: 11px; }
          .gr-topic-desc { display: none; }
          .gr-topic-count { font-size: 11px; }
        }
      `}</style>
    </div>
  );
}
