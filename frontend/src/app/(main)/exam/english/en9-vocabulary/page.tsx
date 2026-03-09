"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { fetchLearnedCountsAPI } from "@/lib/en9-vocab-progress";

interface VocabTopic {
  slug: string;
  title: string;
  title_vi: string;
  emoji: string;
  word_count: number;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

export default function EN9VocabularyPage() {
  const [topics, setTopics] = useState<VocabTopic[]>([]);
  const [mounted, setMounted] = useState(false);
  const [learnedCounts, setLearnedCounts] = useState<Record<string, number>>({});

  useEffect(() => {
    fetch(`${API_BASE}/api/v1/exam/english/en9-vocab-topics`)
      .then(r => r.json())
      .then(async (data) => {
        const list = Array.isArray(data) ? data : [];
        setTopics(list);
        const counts = await fetchLearnedCountsAPI(list.map((t: VocabTopic) => t.slug));
        setLearnedCounts(counts);
      })
      .catch(() => {});
    setTimeout(() => setMounted(true), 50);
  }, []);

  const totalWords = topics.reduce((s, t) => s + t.word_count, 0);
  const totalLearned = Object.values(learnedCounts).reduce((s, c) => s + c, 0);
  const overallPct = totalWords > 0 ? Math.round((totalLearned / totalWords) * 100) : 0;
  const completedCount = topics.filter(t => {
    const l = learnedCounts[t.slug] || 0;
    return t.word_count > 0 && l >= t.word_count;
  }).length;

  return (
    <div className="e9-page" style={{ opacity: mounted ? 1 : 0, transition: "opacity 0.5s" }}>
      <nav className="e9-breadcrumb">
        <Link href="/exam/english">English</Link>
        <span>/</span>
        <span>Từ vựng Lớp 9</span>
      </nav>

      {/* Hero banner */}
      <div className="e9-hero">
        <div className="e9-hero-left">
          <div className="e9-hero-icon">📚</div>
          <div>
            <h1 className="e9-hero-title">Từ vựng Tiếng Anh Lớp 9</h1>
            <p className="e9-hero-desc">Sách giáo khoa Tiếng Anh 9 — {topics.length} Units</p>
          </div>
        </div>
        <div className="e9-hero-stats">
          <div className="e9-hero-stat">
            <span className="e9-hero-stat-num">{topics.length}</span>
            <span className="e9-hero-stat-label">Units</span>
          </div>
          <div className="e9-hero-divider" />
          <div className="e9-hero-stat">
            <span className="e9-hero-stat-num">{totalWords}</span>
            <span className="e9-hero-stat-label">Từ vựng</span>
          </div>
          {completedCount > 0 && (
            <>
              <div className="e9-hero-divider" />
              <div className="e9-hero-stat">
                <span className="e9-hero-stat-num e9-hero-stat-green">{completedCount}</span>
                <span className="e9-hero-stat-label">Hoàn thành</span>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Overall progress */}
      {totalWords > 0 && (
        <div className="e9-progress-card">
          <div className="e9-progress-row">
            <span className="e9-progress-label">Tiến độ tổng</span>
            <span className="e9-progress-fraction">{totalLearned}/{totalWords} từ đã thuộc</span>
          </div>
          <div className="e9-progress-bar">
            <div className={`e9-progress-fill ${overallPct >= 50 ? 'e9-glow' : ''}`} style={{ width: `${overallPct}%` }} />
          </div>
          <div className="e9-progress-row" style={{ marginTop: 5 }}>
            <span className="e9-progress-pct">{overallPct}%</span>
            {totalLearned > 0 && (
              <span className="e9-motivation">
                {overallPct >= 80 ? '🏆 Xuất sắc!' :
                 overallPct >= 50 ? '🔥 Tiến bộ tuyệt vời!' :
                 overallPct >= 20 ? '💪 Tiếp tục nhé!' : '🌱 Khởi đầu tốt!'}
              </span>
            )}
          </div>
        </div>
      )}

      {/* Units grid */}
      <div className="e9-topics">
        {topics.map((topic, idx) => {
          const learned = learnedCounts[topic.slug] || 0;
          const pct = topic.word_count > 0 ? Math.round((learned / topic.word_count) * 100) : 0;
          const isComplete = pct === 100;
          return (
            <Link
              key={topic.slug}
              href={`/exam/english/en9-vocabulary/${topic.slug}`}
              className={`e9-topic-card ${isComplete ? 'e9-topic-complete' : ''}`}
              style={{ animationDelay: `${idx * 0.04}s` }}
            >
              {/* Unit number badge */}
              <div className="e9-unit-num">
                {isComplete ? '✓' : idx + 1}
              </div>
              <div className="e9-topic-emoji">{topic.emoji}</div>
              <h3 className="e9-topic-title">{topic.title}</h3>
              <p className="e9-topic-vi">{topic.title_vi}</p>
              <div className="e9-topic-progress">
                <div className="e9-topic-bar">
                  <div className="e9-topic-fill" style={{ width: `${pct}%` }} />
                </div>
                <span className={`e9-topic-pct ${isComplete ? 'e9-pct-done' : ''}`}>{learned}/{topic.word_count}</span>
              </div>
            </Link>
          );
        })}
      </div>

      <style jsx global>{`
        .e9-page { max-width: 100%; margin: 0 auto; padding: 24px 24px; }

        .e9-breadcrumb { font-size: 13px; color: var(--text-tertiary); margin-bottom: 16px; display: flex; align-items: center; gap: 6px; }
        .e9-breadcrumb a { color: var(--text-tertiary); text-decoration: none; transition: color 0.2s; position: relative; }
        .e9-breadcrumb a::after { content: ''; position: absolute; bottom: -1px; left: 0; width: 0; height: 1.5px; background: var(--action-primary); transition: width 0.25s ease; }
        .e9-breadcrumb a:hover { color: var(--action-primary); }
        .e9-breadcrumb a:hover::after { width: 100%; }
        .e9-breadcrumb span:last-child { color: var(--text-primary); }

        /* Hero banner */
        .e9-hero {
          padding: 24px; border-radius: 16px; margin-bottom: 16px;
          background: linear-gradient(135deg, rgba(59,130,246,0.08), rgba(99,102,241,0.06));
          border: 1px solid rgba(59,130,246,0.1);
          display: flex; align-items: center; justify-content: space-between;
          flex-wrap: wrap; gap: 16px;
          animation: e9SlideUp 0.4s ease both;
        }
        .e9-hero-left { display: flex; align-items: center; gap: 14px; }
        .e9-hero-icon {
          font-size: 28px; width: 52px; height: 52px; display: flex; align-items: center; justify-content: center;
          border-radius: 14px; background: rgba(59,130,246,0.12);
          box-shadow: 0 2px 8px rgba(59,130,246,0.1);
        }
        .e9-hero-title { font-size: 22px; font-weight: 900; color: var(--text-primary); margin: 0; }
        .e9-hero-desc { font-size: 13px; color: var(--text-secondary); margin: 4px 0 0; }

        .e9-hero-stats {
          display: flex; align-items: center; gap: 16px;
          padding: 10px 20px; border-radius: 12px;
          background: var(--bg-surface); border: 1px solid var(--border-default);
          box-shadow: var(--shadow-sm);
        }
        .e9-hero-stat { text-align: center; }
        .e9-hero-stat-num { display: block; font-size: 20px; font-weight: 800; color: #3b82f6; }
        .e9-hero-stat-green { color: #22c55e !important; }
        .e9-hero-stat-label { font-size: 11px; font-weight: 600; color: var(--text-tertiary); }
        .e9-hero-divider { width: 1px; height: 28px; background: var(--border-default); }

        /* Progress card */
        .e9-progress-card {
          margin-bottom: 18px; padding: 14px 18px; border-radius: 14px;
          background: var(--bg-surface); border: 1px solid var(--border-default);
          box-shadow: var(--shadow-sm);
          animation: e9SlideUp 0.4s ease 0.1s both;
        }
        .e9-progress-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
        .e9-progress-label { font-size: 13px; font-weight: 700; color: var(--text-primary); }
        .e9-progress-fraction { font-size: 12px; color: var(--text-tertiary); font-weight: 600; }
        .e9-progress-bar { height: 8px; border-radius: 99px; background: var(--bg-interactive); overflow: hidden; }
        .e9-progress-fill {
          height: 100%; border-radius: 99px;
          background: linear-gradient(90deg, #3b82f6, #6366f1);
          animation: e9ProgressGrow 0.8s ease-out;
        }
        .e9-progress-fill.e9-glow { box-shadow: 0 0 10px rgba(59,130,246,0.35); }
        .e9-progress-pct { font-size: 11px; font-weight: 800; color: #3b82f6; }
        .e9-motivation { font-size: 12px; font-weight: 700; color: #f59e0b; animation: e9MotivPulse 2s ease-in-out infinite; }
        @keyframes e9MotivPulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.7; } }

        /* Topics */
        .e9-topics { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
        @media (min-width: 640px) { .e9-topics { grid-template-columns: repeat(3, 1fr); gap: 12px; } }
        @media (min-width: 1024px) { .e9-topics { grid-template-columns: repeat(4, 1fr); gap: 12px; } }

        .e9-topic-card {
          position: relative; display: flex; flex-direction: column; align-items: center;
          gap: 6px; padding: 18px 12px 14px; border-radius: 14px;
          border: 1px solid var(--border-default); background: var(--bg-surface);
          text-decoration: none; color: inherit;
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          animation: e9SlideUp 0.4s ease both; text-align: center;
        }
        .e9-topic-card:hover {
          border-color: rgba(59,130,246,0.3);
          box-shadow: 0 8px 24px rgba(59,130,246,0.1), 0 2px 8px rgba(0,0,0,0.04);
          transform: translateY(-4px);
        }
        .e9-topic-card:active { transform: translateY(-1px) scale(0.98); }

        /* Complete state */
        .e9-topic-complete {
          border-color: rgba(34,197,94,0.25);
          background: linear-gradient(135deg, var(--bg-surface), rgba(34,197,94,0.04));
        }
        .e9-topic-complete:hover {
          border-color: rgba(34,197,94,0.4);
          box-shadow: 0 8px 24px rgba(34,197,94,0.12), 0 2px 8px rgba(0,0,0,0.04);
        }

        /* Unit number badge */
        .e9-unit-num {
          position: absolute; top: 8px; left: 8px;
          width: 24px; height: 24px; border-radius: 8px;
          background: linear-gradient(135deg, #3b82f6, #6366f1);
          color: white; font-size: 11px; font-weight: 800;
          display: flex; align-items: center; justify-content: center;
          box-shadow: 0 2px 6px rgba(59,130,246,0.3);
          transition: all 0.3s;
        }
        .e9-topic-complete .e9-unit-num {
          background: linear-gradient(135deg, #22c55e, #16a34a);
          box-shadow: 0 2px 6px rgba(34,197,94,0.3);
        }

        .e9-topic-emoji {
          font-size: 30px; width: 48px; height: 48px; border-radius: 14px;
          background: var(--bg-interactive); display: flex; align-items: center; justify-content: center;
          transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), background 0.3s;
        }
        .e9-topic-card:hover .e9-topic-emoji { transform: scale(1.12) rotate(-3deg); background: rgba(59,130,246,0.08); }
        .e9-topic-complete:hover .e9-topic-emoji { background: rgba(34,197,94,0.08); }

        .e9-topic-title { font-size: 14px; font-weight: 700; color: var(--text-primary); margin: 0; line-height: 1.3; transition: color 0.2s; }
        .e9-topic-card:hover .e9-topic-title { color: #3b82f6; }
        .e9-topic-complete:hover .e9-topic-title { color: #16a34a; }
        .e9-topic-vi { font-size: 11px; color: var(--text-tertiary); margin: 0; }

        .e9-topic-progress { width: 100%; margin-top: 6px; }
        .e9-topic-bar { height: 4px; border-radius: 99px; background: var(--bg-interactive); overflow: hidden; }
        .e9-topic-fill {
          height: 100%; border-radius: 99px;
          background: linear-gradient(90deg, #3b82f6, #6366f1);
          transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .e9-topic-complete .e9-topic-fill {
          background: linear-gradient(90deg, #22c55e, #16a34a);
        }
        .e9-topic-pct {
          display: block; text-align: right; font-size: 10px; font-weight: 700;
          color: #3b82f6; margin-top: 2px; transition: color 0.2s;
        }
        .e9-pct-done { color: #16a34a; font-weight: 800; }

        @keyframes e9SlideUp { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes e9ProgressGrow { from { width: 0; } }

        @media (max-width: 640px) {
          .e9-page { padding: 16px; }
          .e9-breadcrumb { font-size: 12px; margin-bottom: 10px; }
          .e9-hero { padding: 16px; border-radius: 14px; }
          .e9-hero-title { font-size: 18px; }
          .e9-hero-icon { width: 44px; height: 44px; font-size: 24px; }
          .e9-hero-stats { padding: 8px 14px; gap: 12px; }
          .e9-hero-stat-num { font-size: 16px; }
          .e9-progress-card { padding: 10px 14px; margin-bottom: 14px; }
          .e9-topics { gap: 8px; }
          .e9-topic-card { padding: 14px 10px 12px; gap: 4px; border-radius: 12px; }
          .e9-topic-emoji { font-size: 24px; width: 40px; height: 40px; border-radius: 10px; }
          .e9-topic-title { font-size: 12px; }
          .e9-topic-vi { font-size: 10px; }
          .e9-unit-num { width: 20px; height: 20px; font-size: 10px; border-radius: 6px; top: 6px; left: 6px; }
        }
      `}</style>
    </div>
  );
}
