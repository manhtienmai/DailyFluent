"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { getUserPref } from "@/lib/user-prefs";

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
const DIFF_ACCENT: Record<string, string> = {
  easy: "linear-gradient(180deg, #22c55e, #16a34a)", medium: "linear-gradient(180deg, #f59e0b, #d97706)", hard: "linear-gradient(180deg, #ef4444, #dc2626)",
};
const DIFF_LABEL: Record<string, string> = { easy: "Cơ bản", medium: "Trung bình", hard: "Nâng cao" };

export default function GrammarTopicsPage() {
  const [mounted, setMounted] = useState(false);
  const [topics, setTopics] = useState<GrammarTopic[]>([]);
  const [visited, setVisited] = useState<Set<string>>(new Set());
  const [showAll, setShowAll] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE}/api/v1/exam/english/grammar-topics`)
      .then(r => r.json())
      .then(data => setTopics(Array.isArray(data) ? data : []))
      .catch(() => {});
    // Load visited topics from API (falls back to localStorage)
    getUserPref<string[]>("grammar_visited").then(v => {
      if (v && Array.isArray(v)) setVisited(new Set(v));
    });
    setTimeout(() => setMounted(true), 50);
  }, []);

  const hasVisited = visited.size > 0;
  const displayTopics = (!hasVisited || showAll) ? topics : topics.filter(t => visited.has(t.topic_id));
  const totalQuestions = topics.reduce((s, t) => s + t.question_count, 0);

  return (
    <div className="gr-page" style={{ opacity: mounted ? 1 : 0, transition: "opacity 0.5s" }}>
      <nav className="gr-breadcrumb">
        <Link href="/exam/english">English Lớp 10</Link>
        <span>/</span>
        <span>Ngữ pháp</span>
      </nav>

      {/* Hero banner */}
      <div className="gr-hero">
        <div className="gr-hero-content">
          <h1 className="gr-hero-title">📐 Ngữ pháp tiếng Anh</h1>
          <p className="gr-hero-desc">Ôn tập ngữ pháp trọng tâm cho kỳ thi vào lớp 10</p>
        </div>
        <div className="gr-hero-stats">
          <div className="gr-hero-stat">
            <span className="gr-hero-stat-num">{topics.length}</span>
            <span className="gr-hero-stat-label">Chủ đề</span>
          </div>
          <div className="gr-hero-stat-divider" />
          <div className="gr-hero-stat">
            <span className="gr-hero-stat-num">{totalQuestions}</span>
            <span className="gr-hero-stat-label">Câu hỏi</span>
          </div>
          {hasVisited && (
            <>
              <div className="gr-hero-stat-divider" />
              <div className="gr-hero-stat">
                <span className="gr-hero-stat-num">{visited.size}</span>
                <span className="gr-hero-stat-label">Đã học</span>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Filter */}
      {hasVisited && (
        <div className="gr-filter-row">
          <button
            onClick={() => setShowAll(!showAll)}
            className={`gr-filter-btn ${showAll ? 'gr-filter-active' : ''}`}
          >
            {showAll ? `Tất cả (${topics.length})` : `Đang học (${visited.size})`}
          </button>
          <span className="gr-filter-hint">
            {showAll ? 'Hiển thị tất cả chủ đề' : 'Chỉ hiện chủ đề đã mở'}
          </span>
        </div>
      )}

      {displayTopics.length === 0 && hasVisited && !showAll ? (
        <div className="gr-empty">
          <div style={{ fontSize: 48, marginBottom: 12 }}>📚</div>
          <p style={{ fontSize: 15, fontWeight: 600, marginBottom: 4 }}>Chưa học chủ đề nào</p>
          <p style={{ fontSize: 13, color: 'var(--text-tertiary)', marginBottom: 16 }}>Bắt đầu bằng cách chọn một chủ đề bên dưới</p>
          <button onClick={() => setShowAll(true)} className="gr-empty-btn">Xem tất cả chủ đề</button>
        </div>
      ) : (
        <div className={`gr-topics ${displayTopics.length <= 3 ? 'gr-topics-single' : ''}`}>
          {displayTopics.map((topic, idx) => {
            const isVisited = visited.has(topic.topic_id);
            return (
              <Link
                key={topic.topic_id}
                href={`/exam/english/grammar/${topic.topic_id}`}
                className="gr-topic-card"
                style={{ animationDelay: `${idx * 0.06}s` }}
              >
                <div className="gr-topic-emoji">{topic.emoji}</div>
                <div className="gr-topic-body">
                  <div className="gr-topic-header">
                    <h3 className="gr-topic-title">{topic.title}</h3>
                    <span className="gr-topic-badge" style={{ background: DIFF_COLORS[topic.difficulty], color: DIFF_TEXT[topic.difficulty] }}>
                      {DIFF_LABEL[topic.difficulty]}
                    </span>
                    {isVisited && <span className="gr-visited-badge">✓ Đã học</span>}
                  </div>
                  <p className="gr-topic-vi">{topic.title_vi}</p>
                  <p className="gr-topic-desc">{topic.description}</p>
                </div>
                <div className="gr-topic-right">
                  <div className="gr-topic-count">{topic.question_count} câu</div>
                  <div className="gr-topic-arrow">→</div>
                </div>
              </Link>
            );
          })}
        </div>
      )}

      <style jsx global>{`
        .gr-page { max-width: 100%; margin: 0 auto; padding: 24px 24px; }
        .gr-breadcrumb { font-size: 13px; color: var(--text-tertiary); margin-bottom: 16px; display: flex; align-items: center; gap: 6px; }
        .gr-breadcrumb a { color: var(--text-tertiary); text-decoration: none; }
        .gr-breadcrumb a:hover { color: var(--action-primary); }
        .gr-breadcrumb span:last-child { color: var(--text-primary); }

        /* Hero banner */
        .gr-hero {
          padding: 24px; border-radius: 16px; margin-bottom: 20px;
          background: linear-gradient(135deg, rgba(99,102,241,0.08), rgba(139,92,246,0.06));
          border: 1px solid rgba(99,102,241,0.1);
          display: flex; align-items: center; justify-content: space-between;
          flex-wrap: wrap; gap: 16px;
          animation: grSlideUp 0.4s ease both;
        }
        .gr-hero-title { font-size: 22px; font-weight: 900; color: var(--text-primary); margin: 0; }
        .gr-hero-desc { font-size: 13px; color: var(--text-secondary); margin: 4px 0 0; }
        .gr-hero-stats {
          display: flex; align-items: center; gap: 16px;
          padding: 10px 20px; border-radius: 12px;
          background: var(--bg-surface); border: 1px solid var(--border-default);
          box-shadow: var(--shadow-sm);
        }
        .gr-hero-stat { text-align: center; }
        .gr-hero-stat-num { display: block; font-size: 20px; font-weight: 800; color: #6366f1; }
        .gr-hero-stat-label { font-size: 11px; font-weight: 600; color: var(--text-tertiary); }
        .gr-hero-stat-divider { width: 1px; height: 28px; background: var(--border-default); }

        /* Filter row */
        .gr-filter-row {
          display: flex; align-items: center; gap: 12px; margin-bottom: 16px;
          animation: grSlideUp 0.4s ease 0.1s both;
        }
        .gr-filter-btn {
          padding: 6px 16px; border-radius: 99px; font-size: 12px; font-weight: 700;
          border: 1px solid var(--border-default); background: var(--bg-surface);
          color: var(--text-secondary); cursor: pointer; transition: all 0.2s;
        }
        .gr-filter-btn:hover { border-color: #6366f1; color: #6366f1; }
        .gr-filter-active {
          background: var(--text-primary); color: white; border-color: var(--text-primary);
        }
        .gr-filter-active:hover { opacity: 0.9; color: white; }
        .gr-filter-hint { font-size: 11px; color: var(--text-tertiary); }

        /* Empty state */
        .gr-empty {
          text-align: center; padding: 48px 16px; color: var(--text-secondary);
          animation: grSlideUp 0.35s ease both;
        }
        .gr-empty-btn {
          padding: 10px 24px; border-radius: 12px; font-size: 13px; font-weight: 600;
          border: 1px solid var(--border-default); background: var(--bg-surface);
          color: var(--text-primary); cursor: pointer; transition: all 0.2s;
        }
        .gr-empty-btn:hover { border-color: #6366f1; box-shadow: var(--shadow-md); transform: translateY(-1px); }

        /* Topics grid - single column when few items */
        .gr-topics { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
        .gr-topics-single { grid-template-columns: 1fr; max-width: 640px; }
        @media (max-width: 768px) { .gr-topics { grid-template-columns: 1fr; } }

        .gr-topic-card {
          position: relative;
          display: flex; align-items: center; gap: 14px;
          border-radius: 14px; border: 1px solid var(--border-default); background: var(--bg-surface);
          padding: 14px 16px; text-decoration: none; transition: all 0.25s;
          animation: grSlideUp 0.35s ease-out both;
          overflow: hidden;
        }
        .gr-topic-card:hover { box-shadow: var(--shadow-lg); transform: translateY(-2px); border-color: var(--action-primary); }

        .gr-topic-emoji { font-size: 32px; flex-shrink: 0; width: 48px; height: 48px; display: flex; align-items: center; justify-content: center; background: var(--bg-interactive); border-radius: 12px; transition: transform 0.3s; }
        .gr-topic-card:hover .gr-topic-emoji { transform: scale(1.08) rotate(4deg); }
        .gr-topic-body { flex: 1; min-width: 0; }
        .gr-topic-header { display: flex; align-items: center; gap: 8px; margin-bottom: 2px; flex-wrap: wrap; }
        .gr-topic-title { font-size: 14px; font-weight: 700; color: var(--text-primary); margin: 0; transition: color 0.2s; }
        .gr-topic-card:hover .gr-topic-title { color: var(--action-primary); }
        .gr-topic-badge { padding: 2px 8px; border-radius: 99px; font-size: 10px; font-weight: 700; flex-shrink: 0; }
        .gr-visited-badge {
          padding: 2px 8px; border-radius: 99px; font-size: 10px; font-weight: 700;
          background: rgba(34,197,94,0.1); color: #16a34a; flex-shrink: 0;
        }
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
          .gr-hero { padding: 16px; border-radius: 14px; }
          .gr-hero-title { font-size: 18px; }
          .gr-hero-desc { font-size: 12px; }
          .gr-hero-stats { padding: 8px 14px; gap: 12px; }
          .gr-hero-stat-num { font-size: 16px; }
          .gr-filter-row { margin-bottom: 12px; }
          .gr-topic-card { padding: 12px 14px 12px 18px; gap: 10px; }
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
