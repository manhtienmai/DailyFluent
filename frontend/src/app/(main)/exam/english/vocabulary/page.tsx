"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

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

  useEffect(() => {
    fetch(`${API_BASE}/api/v1/exam/english/vocab-topics`)
      .then(r => r.json())
      .then(data => setTopics(Array.isArray(data) ? data : []))
      .catch(() => {});
    setTimeout(() => setMounted(true), 50);
  }, []);

  const totalWords = topics.reduce((s, t) => s + t.word_count, 0);

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

      <div className="vc-topics">
        {topics.map((topic, idx) => (
          <Link
            key={topic.slug}
            href={`/exam/english/vocabulary/${topic.slug}`}
            className="vc-topic-card"
            style={{ animationDelay: `${idx * 0.03}s` }}
          >
            <div className="vc-topic-emoji">{topic.emoji}</div>
            <h3 className="vc-topic-title">{topic.title}</h3>
            <p className="vc-topic-vi">{topic.title_vi}</p>
            <div className="vc-topic-count">{topic.word_count} từ</div>
          </Link>
        ))}
      </div>

      <style jsx global>{`
        .vc-page { max-width: 100%; margin: 0 auto; padding: 24px 24px; }
        .vc-breadcrumb { font-size: 13px; color: var(--text-tertiary); margin-bottom: 16px; display: flex; align-items: center; gap: 6px; }
        .vc-breadcrumb a { color: var(--text-tertiary); text-decoration: none; }
        .vc-breadcrumb a:hover { color: var(--action-primary); }
        .vc-breadcrumb span:last-child { color: var(--text-primary); }
        .vc-title { font-size: 22px; font-weight: 900; color: var(--text-primary); margin: 0; }

        .vc-header { display: flex; align-items: baseline; justify-content: space-between; gap: 16px; margin-bottom: 16px; flex-wrap: wrap; }
        .vc-stats { display: flex; gap: 8px; flex-wrap: wrap; }
        .vc-chip { font-size: 12px; font-weight: 700; padding: 4px 12px; border-radius: 99px; }

        .vc-topics { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
        @media (min-width: 640px) { .vc-topics { grid-template-columns: repeat(3, 1fr); gap: 12px; } }
        @media (min-width: 1024px) { .vc-topics { grid-template-columns: repeat(4, 1fr); gap: 12px; } }
        .vc-topic-card {
          display: flex; flex-direction: column; align-items: center; gap: 6px;
          padding: 18px 12px 14px; border-radius: 14px; border: 1px solid var(--border-default);
          background: var(--bg-surface); text-decoration: none; color: inherit;
          transition: all 0.25s ease; animation: vcSlideUp 0.4s ease both; text-align: center;
        }
        .vc-topic-card:hover {
          border-color: var(--border-strong); box-shadow: 0 4px 16px rgba(0,0,0,0.06);
          transform: translateY(-3px);
        }
        .vc-topic-emoji { font-size: 30px; width: 48px; height: 48px; border-radius: 14px; background: var(--bg-interactive); display: flex; align-items: center; justify-content: center; }
        .vc-topic-title { font-size: 14px; font-weight: 700; color: var(--text-primary); margin: 0; line-height: 1.3; }
        .vc-topic-vi { font-size: 11px; color: var(--text-tertiary); margin: 0; }
        .vc-topic-count { font-size: 11px; font-weight: 700; color: var(--text-secondary); background: rgba(0,0,0,0.05); padding: 2px 10px; border-radius: 99px; margin-top: 2px; }

        @keyframes vcSlideUp { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }

        @media (max-width: 640px) {
          .vc-page { padding: 16px; }
          .vc-breadcrumb { font-size: 12px; margin-bottom: 10px; }
          .vc-title { font-size: 18px; }
          .vc-header { gap: 8px; margin-bottom: 12px; }
          .vc-chip { font-size: 11px; padding: 3px 8px; }
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
