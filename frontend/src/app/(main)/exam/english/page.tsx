"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { fetchLearnedCountsAPI } from "@/lib/vocab-progress";

interface ExamItem {
  id: number;
  title: string;
  slug: string;
  description: string;
  total_questions: number;
  time_limit_minutes: number;
  attempted: boolean;
  best_score: number | null;
}

interface VocabTopic {
  slug: string;
  title: string;
  title_vi: string;
  emoji: string;
  word_count: number;
}

export default function EnglishExamListPage() {
  const [items, setItems] = useState<ExamItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [isVip, setIsVip] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [vocabTopics, setVocabTopics] = useState<VocabTopic[]>([]);
  const [learnedCounts, setLearnedCounts] = useState<Record<string, number>>({});

  useEffect(() => {
    fetch("/api/v1/exam/english/", { credentials: "include" })
      .then((r) => r.json())
      .then((d) => {
        setItems(d.items || []);
        setIsVip(d.is_vip || false);
      })
      .catch(() => {})
      .finally(() => setLoading(false));

    // Fetch vocab topics + progress from API
    fetch("/api/v1/exam/english/vocab-topics")
      .then(r => r.json())
      .then(async (data) => {
        const list = Array.isArray(data) ? data : [];
        setVocabTopics(list);
        // Fetch progress from server API
        const counts = await fetchLearnedCountsAPI(list.map((t: VocabTopic) => t.slug));
        setLearnedCounts(counts);
      })
      .catch(() => {});

    setTimeout(() => setMounted(true), 50);
  }, []);

  const totalWords = vocabTopics.reduce((s, t) => s + t.word_count, 0);
  const totalLearned = Object.values(learnedCounts).reduce((s, c) => s + c, 0);

  return (
    <div className={`mx-auto max-w-4xl px-4 py-6 transition-all duration-500 ${mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"}`}>
      {/* Breadcrumb */}
      <nav className="mb-5 flex items-center gap-1.5 text-sm" style={{ color: 'var(--text-tertiary)' }}>
        <Link href="/exam/" className="no-underline hover:text-blue-500 transition-colors duration-200" style={{ color: 'var(--text-tertiary)' }}>Luyện thi</Link>
        <span style={{ color: 'var(--border-default)' }}>/</span>
        <span className="font-semibold" style={{ color: 'var(--text-primary)' }}>English Lớp 10</span>
      </nav>

      <div className="mb-8">
        <h1 className="text-2xl font-extrabold tracking-tight mb-2" style={{ color: 'var(--text-primary)' }}>
          Luyện thi tiếng Anh vào 10
        </h1>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="relative">
            <div className="h-10 w-10 animate-spin rounded-full border-3 border-blue-500 border-t-transparent" />
            <div className="absolute inset-0 h-10 w-10 animate-ping rounded-full border border-blue-300 opacity-30" />
          </div>
        </div>
      ) : items.length === 0 ? (
        <div className="rounded-xl border border-dashed p-10 text-center animate-[fadeIn_0.5s_ease]" style={{ borderColor: 'var(--border-default)', color: 'var(--text-tertiary)' }}>
          <p className="text-lg mb-1">📭 Chưa có đề thi nào</p>
          <p className="text-sm">Vui lòng thêm đề thi qua trang admin.</p>
        </div>
      ) : (
        <>
        {/* Learning tools */}
        <div className="mb-8">
          <h2 className="text-sm font-bold uppercase tracking-wider mb-3" style={{ color: 'var(--text-tertiary)' }}>📖 Công cụ học tập</h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <Link href="/exam/english/phrasal-verbs" className="group rounded-xl border p-4 no-underline transition-all duration-300 hover:shadow-lg hover:-translate-y-1" style={{ background: 'var(--bg-surface)', borderColor: 'var(--border-default)' }}>
              <div className="text-2xl mb-2 transition-transform duration-300 group-hover:scale-110">🔤</div>
              <div className="text-sm font-bold group-hover:text-blue-500 transition-colors" style={{ color: 'var(--text-primary)' }}>Phrasal Verbs</div>
              <div className="text-[11px] mt-0.5" style={{ color: 'var(--text-tertiary)' }}>4 trò chơi</div>
            </Link>
            <Link href="/exam/english/grammar" className="group rounded-xl border p-4 no-underline transition-all duration-300 hover:shadow-lg hover:-translate-y-1" style={{ background: 'var(--bg-surface)', borderColor: 'var(--border-default)' }}>
              <div className="text-2xl mb-2 transition-transform duration-300 group-hover:scale-110">📐</div>
              <div className="text-sm font-bold group-hover:text-blue-500 transition-colors" style={{ color: 'var(--text-primary)' }}>Ngữ pháp</div>
              <div className="text-[11px] mt-0.5" style={{ color: 'var(--text-tertiary)' }}>Ôn lý thuyết + BT</div>
            </Link>
            <Link href="/exam/english/vocabulary" className="group rounded-xl border p-4 no-underline transition-all duration-300 hover:shadow-lg hover:-translate-y-1" style={{ background: 'var(--bg-surface)', borderColor: 'var(--border-default)' }}>
              <div className="text-2xl mb-2 transition-transform duration-300 group-hover:scale-110">📖</div>
              <div className="text-sm font-bold group-hover:text-blue-500 transition-colors" style={{ color: 'var(--text-primary)' }}>Từ vựng</div>
              <div className="text-[11px] mt-0.5" style={{ color: 'var(--text-tertiary)' }}>19 chủ đề, 285 từ</div>
            </Link>
            <Link href="/exam/english/en9-vocabulary" className="group rounded-xl border p-4 no-underline transition-all duration-300 hover:shadow-lg hover:-translate-y-1" style={{ background: 'var(--bg-surface)', borderColor: 'var(--border-default)' }}>
              <div className="text-2xl mb-2 transition-transform duration-300 group-hover:scale-110">📚</div>
              <div className="text-sm font-bold group-hover:text-blue-500 transition-colors" style={{ color: 'var(--text-primary)' }}>Từ vựng lớp 9</div>
              <div className="text-[11px] mt-0.5" style={{ color: 'var(--text-tertiary)' }}>10 units SGK</div>
            </Link>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {items.map((exam, idx) => (
            <div
              key={exam.id}
              className="relative"
              style={{
                animation: `slideUp 0.4s ease-out ${idx * 0.08}s both`,
              }}
            >
              {isVip ? (
                <Link
                  href={`/exam/english/${exam.slug}`}
                  className="group flex flex-col overflow-hidden rounded-xl border p-5 no-underline transition-all duration-300 hover:shadow-xl hover:-translate-y-1 active:scale-[0.98]"
                  style={{ background: 'var(--bg-surface)', borderColor: 'var(--border-default)' }}
                >
                  <ExamCardContent exam={exam} />
                  <div className="mt-3 rounded-lg bg-blue-500/10 px-3 py-2 text-center text-sm font-semibold text-blue-500 transition-all duration-300 group-hover:bg-blue-500 group-hover:text-white group-hover:shadow-md group-hover:shadow-blue-500/25">
                    {exam.attempted ? "Làm lại" : "Bắt đầu"}
                  </div>
                </Link>
              ) : (
                <div className="flex flex-col overflow-hidden rounded-xl border p-5 opacity-75 transition-opacity duration-300 hover:opacity-90" style={{ background: 'var(--bg-surface)', borderColor: 'var(--border-default)' }}>
                  <ExamCardContent exam={exam} />
                  <div className="mt-3 rounded-lg px-3 py-2.5 text-center text-sm" style={{ background: 'var(--bg-interactive)' }}>
                    <div className="flex items-center justify-center gap-1.5 font-semibold mb-1" style={{ color: 'var(--text-disabled)' }}>
                      <span>🔒</span> Đề thi bị khóa
                    </div>
                    <div className="text-xs" style={{ color: 'var(--text-tertiary)' }}>
                      Liên hệ admin để truy cập bài thi
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
        </>
      )}

      {/* ── Từ vựng Tiếng Anh 10 – Vocab Topics Section ── */}
      {vocabTopics.length > 0 && (
        <div className="en9-section" style={{ animation: 'slideUp 0.5s ease-out 0.3s both' }}>
          {/* Gradient header */}
          <div className="en9-gradient-header">
            <div className="en9-header-left">
              <span className="en9-icon">📚</span>
              <div>
                <h2 className="en9-title">Tiếng Anh 9 lên 10</h2>
                <p className="en9-subtitle">{vocabTopics.length} chủ đề · {totalWords} từ vựng</p>
              </div>
            </div>
            <Link href="/exam/english/vocabulary" className="en9-view-all">
              Xem tất cả →
            </Link>
          </div>

          {/* Progress bar */}
          {totalWords > 0 && (
            <div className="en9-progress">
              <div className="en9-progress-info">
                <span className="en9-progress-label">Đã thuộc {totalLearned}/{totalWords} từ</span>
                {totalLearned > 0 && (
                  <span className="en9-motivation">
                    {Math.round((totalLearned / totalWords) * 100) >= 80 ? '🏆 Xuất sắc!' :
                     Math.round((totalLearned / totalWords) * 100) >= 50 ? '🔥 Tiến bộ tuyệt vời!' :
                     Math.round((totalLearned / totalWords) * 100) >= 20 ? '💪 Tiếp tục nhé!' : '🌱 Khởi đầu tốt!'}
                  </span>
                )}
              </div>
              <div className="en9-progress-bar">
                <div className={`en9-progress-fill ${Math.round((totalLearned / totalWords) * 100) >= 50 ? 'en9-glow' : ''}`} style={{ width: `${Math.round((totalLearned / totalWords) * 100)}%` }} />
              </div>
              <span className="en9-progress-pct">{Math.round((totalLearned / totalWords) * 100)}%</span>
            </div>
          )}

          <div className="en9-topics-grid">
            {vocabTopics.map((topic, idx) => {
              const learned = learnedCounts[topic.slug] || 0;
              const pct = topic.word_count > 0 ? Math.round((learned / topic.word_count) * 100) : 0;
              const isComplete = pct === 100;
              return (
                <Link
                  key={topic.slug}
                  href={`/exam/english/vocabulary/${topic.slug}`}
                  className={`en9-topic-card ${isComplete ? 'en9-topic-complete' : ''}`}
                  style={{ animationDelay: `${0.4 + idx * 0.03}s` }}
                >
                  <div className="en9-topic-emoji">{topic.emoji}</div>
                  <div className="en9-topic-info">
                    <h3 className="en9-topic-title">
                      {topic.title}
                      {isComplete && <span className="en9-check"> ✓</span>}
                    </h3>
                    <p className="en9-topic-vi">{topic.title_vi}</p>
                  </div>
                  <div className="en9-topic-right">
                    <span className="en9-topic-count">{learned}/{topic.word_count}</span>
                    <div className="en9-topic-bar">
                      <div className="en9-topic-fill" style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>
        </div>
      )}

      {/* Global keyframes */}
      <style jsx global>{`
        @keyframes slideUp {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }

        /* ── Tiếng anh 9 Section ── */
        .en9-section {
          margin-top: 40px;
          border-radius: 16px;
          background: var(--bg-surface);
          border: 1px solid var(--border-default);
          box-shadow: var(--shadow-sm);
          overflow: hidden;
        }
        .en9-gradient-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 20px 24px;
          background: linear-gradient(135deg, rgba(99,102,241,0.08) 0%, rgba(139,92,246,0.06) 100%);
          border-bottom: 1px solid rgba(99,102,241,0.08);
          flex-wrap: wrap;
          gap: 12px;
        }
        .en9-header-left {
          display: flex;
          align-items: center;
          gap: 12px;
        }
        .en9-icon {
          font-size: 28px;
          width: 48px;
          height: 48px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 14px;
          background: rgba(99, 102, 241, 0.12);
          box-shadow: 0 2px 8px rgba(99,102,241,0.1);
        }
        .en9-title {
          font-size: 18px;
          font-weight: 800;
          color: var(--text-primary);
          margin: 0;
        }
        .en9-subtitle {
          font-size: 12px;
          color: var(--text-tertiary);
          margin: 2px 0 0;
        }
        .en9-view-all {
          font-size: 13px;
          font-weight: 600;
          color: white;
          text-decoration: none;
          transition: all 0.2s;
          padding: 8px 16px;
          border-radius: 10px;
          background: linear-gradient(135deg, #6366f1, #8b5cf6);
          box-shadow: 0 2px 8px rgba(99,102,241,0.25);
        }
        .en9-view-all:hover {
          transform: translateY(-1px);
          box-shadow: 0 4px 12px rgba(99,102,241,0.35);
        }

        /* Progress */
        .en9-progress {
          padding: 12px 24px 0;
          margin-bottom: 8px;
        }
        .en9-progress-info {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 8px;
        }
        .en9-progress-label {
          font-size: 12px;
          font-weight: 600;
          color: var(--text-secondary);
        }
        .en9-motivation {
          font-size: 12px;
          font-weight: 700;
          color: #f59e0b;
          animation: motivPulse 2s ease-in-out infinite;
        }
        @keyframes motivPulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.7; } }
        .en9-progress-bar {
          height: 6px;
          border-radius: 99px;
          background: var(--bg-interactive);
          overflow: hidden;
        }
        .en9-progress-fill {
          height: 100%;
          border-radius: 99px;
          background: linear-gradient(90deg, #22c55e, #16a34a);
          transition: width 0.8s ease-out;
        }
        .en9-progress-fill.en9-glow {
          box-shadow: 0 0 8px rgba(34,197,94,0.4);
        }
        .en9-progress-pct {
          display: block;
          text-align: right;
          font-size: 11px;
          font-weight: 800;
          color: #22c55e;
          margin-top: 4px;
        }
        .en9-check {
          color: #22c55e;
          font-weight: 800;
        }
        .en9-topic-complete {
          border-color: rgba(34,197,94,0.2) !important;
          background: linear-gradient(135deg, var(--bg-surface), rgba(34,197,94,0.03)) !important;
        }

        /* Topics grid */
        .en9-topics-grid {
          display: grid;
          grid-template-columns: 1fr;
          gap: 4px;
          padding: 12px 24px 24px;
        }
        .en9-topic-card {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 10px 14px;
          border-radius: 12px;
          text-decoration: none;
          color: inherit;
          transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
          animation: slideUp 0.4s ease both;
          border: 1px solid transparent;
        }
        .en9-topic-card:hover {
          background: var(--bg-interactive);
          border-color: var(--border-default);
          transform: translateX(4px);
        }
        .en9-topic-emoji {
          font-size: 22px;
          width: 38px;
          height: 38px;
          border-radius: 10px;
          background: var(--bg-interactive);
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
          transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        .en9-topic-card:hover .en9-topic-emoji {
          transform: scale(1.1) rotate(-3deg);
        }
        .en9-topic-info {
          flex: 1;
          min-width: 0;
        }
        .en9-topic-title {
          font-size: 13px;
          font-weight: 700;
          color: var(--text-primary);
          margin: 0;
          line-height: 1.3;
          transition: color 0.2s;
        }
        .en9-topic-card:hover .en9-topic-title {
          color: #6366f1;
        }
        .en9-topic-vi {
          font-size: 11px;
          color: var(--text-tertiary);
          margin: 1px 0 0;
        }
        .en9-topic-right {
          display: flex;
          flex-direction: column;
          align-items: flex-end;
          gap: 4px;
          flex-shrink: 0;
          min-width: 70px;
        }
        .en9-topic-count {
          font-size: 10px;
          font-weight: 700;
          color: var(--text-tertiary);
        }
        .en9-topic-bar {
          width: 60px;
          height: 3px;
          border-radius: 99px;
          background: var(--bg-interactive);
          overflow: hidden;
        }
        .en9-topic-fill {
          height: 100%;
          border-radius: 99px;
          background: linear-gradient(90deg, #22c55e, #16a34a);
          transition: width 0.6s ease;
        }

        @media (min-width: 640px) {
          .en9-topics-grid {
            grid-template-columns: 1fr 1fr;
          }
        }
        @media (max-width: 640px) {
          .en9-section {
            margin-top: 28px;
            border-radius: 14px;
          }
          .en9-gradient-header { padding: 16px; }
          .en9-progress { padding: 10px 16px 0; }
          .en9-topics-grid { padding: 8px 16px 16px; }
          .en9-icon { width: 40px; height: 40px; font-size: 22px; border-radius: 10px; }
          .en9-title { font-size: 16px; }
          .en9-topic-emoji { width: 32px; height: 32px; font-size: 18px; border-radius: 8px; }
          .en9-topic-title { font-size: 12px; }
          .en9-topic-card { padding: 8px 10px; gap: 10px; }
        }
      `}</style>
    </div>
  );
}

function ExamCardContent({ exam }: { exam: ExamItem }) {
  return (
    <>
      {/* Score badge with glow */}
      {exam.attempted && exam.best_score !== null && (
        <div className={`absolute top-3 right-3 rounded-full px-2.5 py-0.5 text-xs font-bold transition-all duration-300 ${
          exam.best_score >= 80 ? "bg-emerald-100 text-emerald-600 dark:bg-emerald-900/40 dark:text-emerald-400 shadow-sm shadow-emerald-500/20" :
          exam.best_score >= 60 ? "bg-amber-100 text-amber-600 dark:bg-amber-900/40 dark:text-amber-400 shadow-sm shadow-amber-500/20" :
          "bg-red-100 text-red-600 dark:bg-red-900/40 dark:text-red-400 shadow-sm shadow-red-500/20"
        }`}>
          {exam.best_score}%
        </div>
      )}

      <div className="mb-3 text-3xl transition-transform duration-300 group-hover:scale-110 group-hover:rotate-3">📝</div>
      <h3 className="text-base font-bold mb-1 transition-colors duration-200 group-hover:text-blue-500" style={{ color: 'var(--text-primary)' }}>
        {exam.title}
      </h3>
      {exam.description && (
        <p className="text-sm mb-3 line-clamp-2" style={{ color: 'var(--text-secondary)' }}>{exam.description}</p>
      )}

      <div className="mt-auto flex items-center gap-3 text-sm" style={{ color: 'var(--text-tertiary)' }}>
        <span>📋 {exam.total_questions} câu</span>
        <span>⏱ {exam.time_limit_minutes} phút</span>
      </div>
    </>
  );
}
