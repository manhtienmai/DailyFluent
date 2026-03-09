"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { fetchLearnedCountsAPI } from "@/lib/vocab-progress";

interface VocabTopic {
  slug: string;
  title: string;
  title_vi: string;
  emoji: string;
  word_count: number;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

export default function VocabularyPage() {
  const [topics, setTopics] = useState<VocabTopic[]>([]);
  const [mounted, setMounted] = useState(false);
  const [learnedCounts, setLearnedCounts] = useState<Record<string, number>>({});
  const [search, setSearch] = useState("");

  useEffect(() => {
    fetch(`${API_BASE}/api/v1/exam/english/vocab-topics`)
      .then(r => r.json())
      .then(async (data) => {
        const list = Array.isArray(data) ? data : [];
        setTopics(list);
        // Fetch learned counts from API
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

  const filteredTopics = search.trim()
    ? topics.filter(t =>
        t.title.toLowerCase().includes(search.toLowerCase()) ||
        t.title_vi.toLowerCase().includes(search.toLowerCase())
      )
    : topics;

  return (
    <div className="vc-page" style={{ opacity: mounted ? 1 : 0, transition: "opacity 0.5s" }}>
      <nav className="vc-breadcrumb">
        <Link href="/exam/english">English Lớp 10</Link>
        <span>/</span>
        <span>Từ vựng</span>
      </nav>

      <div className="vc-header">
        <h1 className="vc-title">📖 Từ vựng theo chủ đề</h1>
        <div className="vc-stats">
          <span className="vc-chip vc-chip-default">📚 {topics.length} chủ đề</span>
          <span className="vc-chip vc-chip-default">📝 {totalWords} từ</span>
          {completedCount > 0 && (
            <span className="vc-chip vc-chip-success">✅ {completedCount} hoàn thành</span>
          )}
        </div>
      </div>

      {/* Search box */}
      <div className="vc-search-wrap">
        <span className="vc-search-icon">🔍</span>
        <input
          type="text"
          className="vc-search-input"
          placeholder="Tìm chủ đề..."
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
        {search && (
          <button className="vc-search-clear" onClick={() => setSearch("")}>✕</button>
        )}
      </div>

      {/* Overall progress */}
      {totalWords > 0 && (
        <div className="vc-overall-progress">
          <div className="vc-overall-row">
            <span className="vc-overall-label">Tiến độ tổng</span>
            <span className="vc-overall-fraction">{totalLearned}/{totalWords} từ đã thuộc</span>
          </div>
          <div className="vc-overall-bar">
            <div className={`vc-overall-fill ${overallPct >= 50 ? 'vc-glow' : ''}`} style={{ width: `${overallPct}%` }} />
          </div>
          <div className="vc-overall-row" style={{ marginTop: 5 }}>
            <span className="vc-overall-pct">{overallPct}%</span>
            {totalLearned > 0 && (
              <span className="vc-motivation">
                {overallPct >= 80 ? '🏆 Xuất sắc!' :
                 overallPct >= 50 ? '🔥 Tiến bộ tuyệt vời!' :
                 overallPct >= 20 ? '💪 Tiếp tục nhé!' : '🌱 Khởi đầu tốt!'}
              </span>
            )}
          </div>
        </div>
      )}

      {filteredTopics.length === 0 && search ? (
        <div className="vc-empty">
          <span style={{ fontSize: 32 }}>🔍</span>
          <p>Không tìm thấy chủ đề &quot;{search}&quot;</p>
        </div>
      ) : (
        <div className="vc-topics">
          {filteredTopics.map((topic, idx) => {
            const learned = learnedCounts[topic.slug] || 0;
            const pct = topic.word_count > 0 ? Math.round((learned / topic.word_count) * 100) : 0;
            const isComplete = pct === 100;
            return (
              <Link
                key={topic.slug}
                href={`/exam/english/vocabulary/${topic.slug}`}
                className={`vc-topic-card ${isComplete ? 'vc-topic-complete' : ''}`}
                style={{ animationDelay: `${idx * 0.03}s` }}
              >
                {isComplete && <div className="vc-complete-badge">✓</div>}
                <div className="vc-topic-emoji">{topic.emoji}</div>
                <h3 className="vc-topic-title">{topic.title}</h3>
                <p className="vc-topic-vi">{topic.title_vi}</p>
                {/* Mini progress bar */}
                <div className="vc-topic-progress">
                  <div className="vc-topic-bar">
                    <div className="vc-topic-fill" style={{ width: `${pct}%` }} />
                  </div>
                  <span className={`vc-topic-pct ${isComplete ? 'vc-pct-done' : ''}`}>{learned}/{topic.word_count}</span>
                </div>
              </Link>
            );
          })}
        </div>
      )}

      <style jsx global>{`
        .vc-page { max-width: 100%; margin: 0 auto; padding: 24px 24px; }
        .vc-breadcrumb { font-size: 13px; color: var(--text-tertiary); margin-bottom: 16px; display: flex; align-items: center; gap: 6px; }
        .vc-breadcrumb a { color: var(--text-tertiary); text-decoration: none; transition: color 0.2s; position: relative; }
        .vc-breadcrumb a::after { content: ''; position: absolute; bottom: -1px; left: 0; width: 0; height: 1.5px; background: var(--action-primary); transition: width 0.25s ease; }
        .vc-breadcrumb a:hover { color: var(--action-primary); }
        .vc-breadcrumb a:hover::after { width: 100%; }
        .vc-breadcrumb span:last-child { color: var(--text-primary); }
        .vc-title { font-size: 22px; font-weight: 900; color: var(--text-primary); margin: 0; }

        .vc-header { display: flex; align-items: baseline; justify-content: space-between; gap: 16px; margin-bottom: 16px; flex-wrap: wrap; }
        .vc-stats { display: flex; gap: 8px; flex-wrap: wrap; }
        .vc-chip {
          font-size: 12px; font-weight: 700; padding: 4px 12px; border-radius: 99px;
          transition: transform 0.2s, box-shadow 0.2s;
        }
        .vc-chip:hover { transform: translateY(-1px); box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
        .vc-chip-default { background: rgba(0,0,0,.05); color: var(--text-secondary); }
        .vc-chip-success { background: rgba(34,197,94,0.1); color: #16a34a; }

        /* Search */
        .vc-search-wrap {
          position: relative; margin-bottom: 16px;
        }
        .vc-search-icon {
          position: absolute; left: 14px; top: 50%; transform: translateY(-50%);
          font-size: 14px; pointer-events: none;
        }
        .vc-search-input {
          width: 100%; padding: 10px 36px 10px 38px; border-radius: 12px;
          border: 1px solid var(--border-default); background: var(--bg-surface);
          font-size: 13px; color: var(--text-primary); outline: none;
          transition: border-color 0.2s, box-shadow 0.2s;
        }
        .vc-search-input:focus {
          border-color: #6366f1;
          box-shadow: 0 0 0 3px rgba(99,102,241,0.1);
        }
        .vc-search-input::placeholder { color: var(--text-tertiary); }
        .vc-search-clear {
          position: absolute; right: 10px; top: 50%; transform: translateY(-50%);
          width: 24px; height: 24px; border: none; background: var(--bg-interactive);
          border-radius: 99px; font-size: 11px; cursor: pointer;
          display: flex; align-items: center; justify-content: center;
          color: var(--text-tertiary); transition: all 0.2s;
        }
        .vc-search-clear:hover { background: rgba(239,68,68,0.1); color: #ef4444; }

        /* Empty state */
        .vc-empty {
          text-align: center; padding: 48px 16px; color: var(--text-tertiary);
          animation: vcSlideUp 0.3s ease both;
        }
        .vc-empty p { font-size: 14px; margin-top: 8px; }

        /* Overall progress */
        .vc-overall-progress {
          margin-bottom: 18px; padding: 14px 18px; border-radius: 14px;
          background: var(--bg-surface); border: 1px solid var(--border-default);
          box-shadow: var(--shadow-sm); animation: vcSlideUp 0.4s ease both;
        }
        .vc-overall-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
        .vc-overall-label { font-size: 13px; font-weight: 700; color: var(--text-primary); }
        .vc-overall-fraction { font-size: 12px; color: var(--text-tertiary); font-weight: 600; }
        .vc-overall-bar {
          height: 8px; border-radius: 99px; background: var(--bg-interactive); overflow: hidden;
        }
        .vc-overall-fill {
          height: 100%; border-radius: 99px;
          background: linear-gradient(90deg, #22c55e, #16a34a);
          animation: vcProgressGrow 0.8s ease-out;
        }
        .vc-overall-fill.vc-glow {
          box-shadow: 0 0 10px rgba(34,197,94,0.4);
        }
        .vc-overall-pct {
          font-size: 11px; font-weight: 800; color: #22c55e;
        }
        .vc-motivation {
          font-size: 12px; font-weight: 700; color: #f59e0b;
          animation: motivPulse 2s ease-in-out infinite;
        }
        @keyframes motivPulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.7; } }

        .vc-topics { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
        @media (min-width: 640px) { .vc-topics { grid-template-columns: repeat(3, 1fr); gap: 12px; } }
        @media (min-width: 1024px) { .vc-topics { grid-template-columns: repeat(4, 1fr); gap: 12px; } }
        .vc-topic-card {
          position: relative;
          display: flex; flex-direction: column; align-items: center; gap: 6px;
          padding: 18px 12px 14px; border-radius: 14px; border: 1px solid var(--border-default);
          background: var(--bg-surface); text-decoration: none; color: inherit;
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          animation: vcSlideUp 0.4s ease both; text-align: center;
        }
        .vc-topic-card:hover {
          border-color: rgba(99,102,241,0.3);
          box-shadow: 0 8px 24px rgba(99,102,241,0.1), 0 2px 8px rgba(0,0,0,0.04);
          transform: translateY(-4px);
        }
        .vc-topic-card:active { transform: translateY(-1px) scale(0.98); }

        /* Complete state */
        .vc-topic-complete {
          border-color: rgba(34,197,94,0.25);
          background: linear-gradient(135deg, var(--bg-surface), rgba(34,197,94,0.04));
        }
        .vc-topic-complete:hover {
          border-color: rgba(34,197,94,0.4);
          box-shadow: 0 8px 24px rgba(34,197,94,0.12), 0 2px 8px rgba(0,0,0,0.04);
        }
        .vc-complete-badge {
          position: absolute; top: 8px; right: 8px;
          width: 22px; height: 22px; border-radius: 99px;
          background: linear-gradient(135deg, #22c55e, #16a34a);
          color: white; font-size: 11px; font-weight: 800;
          display: flex; align-items: center; justify-content: center;
          box-shadow: 0 2px 6px rgba(34,197,94,0.3);
        }

        .vc-topic-emoji {
          font-size: 30px; width: 48px; height: 48px; border-radius: 14px;
          background: var(--bg-interactive); display: flex; align-items: center; justify-content: center;
          transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), background 0.3s;
        }
        .vc-topic-card:hover .vc-topic-emoji { transform: scale(1.12) rotate(-3deg); background: rgba(99,102,241,0.08); }
        .vc-topic-complete:hover .vc-topic-emoji { background: rgba(34,197,94,0.08); }
        .vc-topic-title { font-size: 14px; font-weight: 700; color: var(--text-primary); margin: 0; line-height: 1.3; transition: color 0.2s; }
        .vc-topic-card:hover .vc-topic-title { color: #6366f1; }
        .vc-topic-complete:hover .vc-topic-title { color: #16a34a; }
        .vc-topic-vi { font-size: 11px; color: var(--text-tertiary); margin: 0; }

        /* Per-topic mini progress */
        .vc-topic-progress { width: 100%; margin-top: 6px; }
        .vc-topic-bar {
          height: 4px; border-radius: 99px; background: var(--bg-interactive); overflow: hidden;
        }
        .vc-topic-fill {
          height: 100%; border-radius: 99px;
          background: linear-gradient(90deg, #22c55e, #16a34a);
          transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .vc-topic-pct {
          display: block; text-align: right; font-size: 10px; font-weight: 700;
          color: #22c55e; margin-top: 2px; transition: color 0.2s;
        }
        .vc-pct-done { color: #16a34a; font-weight: 800; }

        @keyframes vcSlideUp { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes vcProgressGrow { from { width: 0; } }

        @media (max-width: 640px) {
          .vc-page { padding: 16px; }
          .vc-breadcrumb { font-size: 12px; margin-bottom: 10px; }
          .vc-title { font-size: 18px; }
          .vc-header { gap: 8px; margin-bottom: 12px; }
          .vc-chip { font-size: 11px; padding: 3px 8px; }
          .vc-overall-progress { padding: 10px 14px; margin-bottom: 14px; }
          .vc-topics { gap: 8px; }
          .vc-topic-card { padding: 14px 10px 12px; gap: 4px; border-radius: 12px; }
          .vc-topic-emoji { font-size: 24px; width: 40px; height: 40px; border-radius: 10px; }
          .vc-topic-title { font-size: 12px; }
          .vc-topic-vi { font-size: 10px; }
          .vc-search-input { font-size: 14px; }
        }
      `}</style>
    </div>
  );
}
