"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

interface GrammarTopic {
  id: string;
  emoji: string;
  title: string;
  titleVi: string;
  desc: string;
  questionCount: number;
  difficulty: "easy" | "medium" | "hard";
}

const TOPICS: GrammarTopic[] = [
  { id: "tenses", emoji: "⏰", title: "Tenses", titleVi: "Các thì trong tiếng Anh", desc: "Present Simple, Past Simple, Present Perfect, Future Simple…", questionCount: 10, difficulty: "medium" },
  { id: "passive-voice", emoji: "🔄", title: "Passive Voice", titleVi: "Câu bị động", desc: "Chuyển đổi câu chủ động sang bị động ở các thì.", questionCount: 8, difficulty: "medium" },
  { id: "reported-speech", emoji: "💬", title: "Reported Speech", titleVi: "Câu tường thuật", desc: "Chuyển đổi lời nói trực tiếp sang gián tiếp.", questionCount: 8, difficulty: "hard" },
  { id: "conditionals", emoji: "🔀", title: "Conditionals", titleVi: "Câu điều kiện", desc: "If Type 0, 1, 2, 3 và câu điều kiện hỗn hợp.", questionCount: 8, difficulty: "hard" },
  { id: "relative-clauses", emoji: "🔗", title: "Relative Clauses", titleVi: "Mệnh đề quan hệ", desc: "Who, which, that, whose, where, when.", questionCount: 6, difficulty: "medium" },
  { id: "comparisons", emoji: "📊", title: "Comparisons", titleVi: "So sánh", desc: "So sánh hơn, nhất, ngang bằng.", questionCount: 6, difficulty: "easy" },
  { id: "tag-questions", emoji: "❓", title: "Tag Questions", titleVi: "Câu hỏi đuôi", desc: "Quy tắc thêm tag question vào câu.", questionCount: 6, difficulty: "easy" },
  { id: "word-forms", emoji: "🔤", title: "Word Forms", titleVi: "Dạng từ", desc: "Danh từ, tính từ, trạng từ, động từ — cách chuyển đổi.", questionCount: 8, difficulty: "medium" },
];

const DIFF_COLORS: Record<string, string> = {
  easy: "rgba(34,197,94,0.1)", medium: "rgba(245,158,11,0.1)", hard: "rgba(239,68,68,0.1)",
};
const DIFF_TEXT: Record<string, string> = {
  easy: "#22c55e", medium: "#f59e0b", hard: "#ef4444",
};
const DIFF_LABEL: Record<string, string> = { easy: "Cơ bản", medium: "Trung bình", hard: "Nâng cao" };

export default function GrammarTopicsPage() {
  const [mounted, setMounted] = useState(false);
  useEffect(() => { setTimeout(() => setMounted(true), 50); }, []);

  return (
    <div className="gr-page" style={{ opacity: mounted ? 1 : 0, transition: "opacity 0.5s" }}>
      <nav className="gr-breadcrumb">
        <Link href="/exam/english">English Lớp 10</Link>
        <span>/</span>
        <span>Ngữ pháp</span>
      </nav>

      <h1 className="gr-title">📐 Ngữ pháp tiếng Anh</h1>
      <p className="gr-subtitle">Ôn lại lý thuyết và làm bài tập cho các chủ đề ngữ pháp thi vào lớp 10.</p>

      <div className="gr-stats">
        <div className="gr-stat"><div className="gr-stat-num" style={{ color: "var(--action-primary)" }}>{TOPICS.length}</div><div className="gr-stat-label">Chủ đề</div></div>
        <div className="gr-stat"><div className="gr-stat-num" style={{ color: "#22c55e" }}>{TOPICS.reduce((s, t) => s + t.questionCount, 0)}</div><div className="gr-stat-label">Câu hỏi</div></div>
        <div className="gr-stat"><div className="gr-stat-num" style={{ color: "#a855f7" }}>3</div><div className="gr-stat-label">Cấp độ</div></div>
      </div>

      <div className="gr-topics">
        {TOPICS.map((topic, idx) => (
          <Link
            key={topic.id}
            href={`/exam/english/grammar/${topic.id}`}
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
              </div>
              <p className="gr-topic-vi">{topic.titleVi}</p>
              <p className="gr-topic-desc">{topic.desc}</p>
            </div>
            <div className="gr-topic-right">
              <div className="gr-topic-count">{topic.questionCount} câu</div>
              <div className="gr-topic-arrow">→</div>
            </div>
          </Link>
        ))}
      </div>

      <style jsx global>{`
        .gr-page { max-width: 800px; margin: 0 auto; padding: 24px 16px; }
        .gr-breadcrumb { font-size: 13px; color: var(--text-tertiary); margin-bottom: 16px; display: flex; align-items: center; gap: 6px; }
        .gr-breadcrumb a { color: var(--text-tertiary); text-decoration: none; }
        .gr-breadcrumb a:hover { color: var(--action-primary); }
        .gr-breadcrumb span:last-child { color: var(--text-primary); }
        .gr-title { font-size: 24px; font-weight: 900; color: var(--text-primary); margin-bottom: 4px; }
        .gr-subtitle { font-size: 13px; color: var(--text-tertiary); margin-bottom: 24px; }

        .gr-stats { display: flex; gap: 12px; margin-bottom: 24px; }
        .gr-stat { flex: 1; border-radius: 12px; background: var(--bg-surface); border: 1px solid var(--border-default); padding: 12px; text-align: center; }
        .gr-stat-num { font-size: 20px; font-weight: 900; }
        .gr-stat-label { font-size: 11px; color: var(--text-tertiary); margin-top: 2px; }

        .gr-topics { display: flex; flex-direction: column; gap: 12px; }
        .gr-topic-card {
          display: flex; align-items: center; gap: 16px;
          border-radius: 12px; border: 1px solid var(--border-default); background: var(--bg-surface);
          padding: 16px; text-decoration: none; transition: all 0.3s;
          animation: grSlideUp 0.4s ease-out both;
        }
        .gr-topic-card:hover { box-shadow: var(--shadow-lg); transform: translateY(-2px); border-color: var(--action-primary); }
        @media (max-width: 480px) { .gr-topic-card { gap: 12px; padding: 12px; } }

        .gr-topic-emoji { font-size: 28px; flex-shrink: 0; transition: transform 0.3s; }
        .gr-topic-card:hover .gr-topic-emoji { transform: scale(1.1) rotate(6deg); }
        .gr-topic-body { flex: 1; min-width: 0; }
        .gr-topic-header { display: flex; align-items: center; gap: 8px; margin-bottom: 2px; flex-wrap: wrap; }
        .gr-topic-title { font-size: 15px; font-weight: 700; color: var(--text-primary); margin: 0; transition: color 0.2s; }
        .gr-topic-card:hover .gr-topic-title { color: var(--action-primary); }
        .gr-topic-badge { padding: 2px 8px; border-radius: 99px; font-size: 10px; font-weight: 700; flex-shrink: 0; }
        .gr-topic-vi { font-size: 12px; color: var(--text-secondary); font-weight: 500; margin: 0; }
        .gr-topic-desc { font-size: 11px; color: var(--text-tertiary); margin: 2px 0 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

        .gr-topic-right { flex-shrink: 0; text-align: right; }
        .gr-topic-count { font-size: 12px; color: var(--text-tertiary); }
        .gr-topic-arrow { font-size: 13px; color: var(--action-primary); font-weight: 700; opacity: 0; transition: opacity 0.2s; }
        .gr-topic-card:hover .gr-topic-arrow { opacity: 1; }

        @keyframes grSlideUp {
          from { opacity: 0; transform: translateY(16px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}
