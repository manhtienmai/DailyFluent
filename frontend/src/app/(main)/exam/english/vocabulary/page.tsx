"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { getLearnedWords } from "@/lib/vocab-progress";

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

  useEffect(() => {
    fetch(`${API_BASE}/api/v1/exam/english/vocab-topics`)
      .then(r => r.json())
      .then(data => {
        const list = Array.isArray(data) ? data : [];
        setTopics(list);
        // Read learned counts from localStorage
        const counts: Record<string, number> = {};
        for (const t of list) {
          counts[t.slug] = getLearnedWords(t.slug).length;
        }
        setLearnedCounts(counts);
      })
      .catch(() => {});
    setTimeout(() => setMounted(true), 50);
  }, []);

  const totalWords = topics.reduce((s, t) => s + t.word_count, 0);
  const totalLearned = Object.values(learnedCounts).reduce((s, c) => s + c, 0);
  const overallPct = totalWords > 0 ? Math.round((totalLearned / totalWords) * 100) : 0;

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
          <span className="vc-chip" style={{ background: "rgba(0,0,0,.05)", color: "var(--text-secondary)" }}>📚 {topics.length} chủ đề</span>
          <span className="vc-chip" style={{ background: "rgba(0,0,0,.05)", color: "var(--text-secondary)" }}>📝 {totalWords} từ</span>
        </div>
      </div>

      {/* Overall progress */}
      {totalWords > 0 && (
        <div className="vc-overall-progress">
          <div className="vc-overall-row">
            <span className="vc-overall-label">Tiến độ tổng</span>
            <span className="vc-overall-fraction">{totalLearned}/{totalWords} từ đã thuộc</span>
          </div>
          <div className="vc-overall-bar">
            <div className="vc-overall-fill" style={{ width: `${overallPct}%` }} />
          </div>
          <div className="vc-overall-pct">{overallPct}%</div>
        </div>
      )}

      <div className="vc-topics">
        {topics.map((topic, idx) => {
          const learned = learnedCounts[topic.slug] || 0;
          const pct = topic.word_count > 0 ? Math.round((learned / topic.word_count) * 100) : 0;
          return (
            <Link
              key={topic.slug}
              href={`/exam/english/vocabulary/${topic.slug}`}
              className="vc-topic-card"
              style={{ animationDelay: `${idx * 0.03}s` }}
            >
              <div className="vc-topic-emoji">{topic.emoji}</div>
              <h3 className="vc-topic-title">{topic.title}</h3>
              <p className="vc-topic-vi">{topic.title_vi}</p>
              {/* Mini progress bar */}
              <div className="vc-topic-progress">
                <div className="vc-topic-bar">
                  <div className="vc-topic-fill" style={{ width: `${pct}%` }} />
                </div>
                <span className="vc-topic-pct">{learned}/{topic.word_count}</span>
              </div>
            </Link>
          );
        })}
      </div>

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
        .vc-overall-pct {
          display: block; text-align: right; font-size: 11px; font-weight: 800;
          color: #22c55e; margin-top: 5px;
        }

        .vc-topics { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
        @media (min-width: 640px) { .vc-topics { grid-template-columns: repeat(3, 1fr); gap: 12px; } }
        @media (min-width: 1024px) { .vc-topics { grid-template-columns: repeat(4, 1fr); gap: 12px; } }
        .vc-topic-card {
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
        .vc-topic-emoji {
          font-size: 30px; width: 48px; height: 48px; border-radius: 14px;
          background: var(--bg-interactive); display: flex; align-items: center; justify-content: center;
          transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), background 0.3s;
        }
        .vc-topic-card:hover .vc-topic-emoji { transform: scale(1.12) rotate(-3deg); background: rgba(99,102,241,0.08); }
        .vc-topic-title { font-size: 14px; font-weight: 700; color: var(--text-primary); margin: 0; line-height: 1.3; transition: color 0.2s; }
        .vc-topic-card:hover .vc-topic-title { color: #6366f1; }
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
          .vc-topic-count { font-size: 10px; padding: 2px 8px; }
        }
      `}</style>
    </div>
  );
}

