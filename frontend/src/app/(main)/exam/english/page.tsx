"use client";
import { useEffect, useState } from "react";
import Link from "next/link";

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

export default function EnglishExamListPage() {
  const [items, setItems] = useState<ExamItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [isVip, setIsVip] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    fetch("/api/v1/exam/english/", { credentials: "include" })
      .then((r) => r.json())
      .then((d) => {
        setItems(d.items || []);
        setIsVip(d.is_vip || false);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
    setTimeout(() => setMounted(true), 50);
  }, []);

  return (
    <div className={`mx-auto max-w-4xl px-4 py-6 transition-all duration-500 ${mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"}`}>
      {/* Breadcrumb */}
      <nav className="mb-5 flex items-center gap-1.5 text-sm" style={{ color: 'var(--text-tertiary)' }}>
        <Link href="/exam/" className="no-underline hover:text-blue-500 transition-colors duration-200" style={{ color: 'var(--text-tertiary)' }}>Luyện thi</Link>
        <span style={{ color: 'var(--border-default)' }}>/</span>
        <span className="font-semibold" style={{ color: 'var(--text-primary)' }}>🇬🇧 English Lớp 10</span>
      </nav>

      {/* Header with animated underline */}
      <div className="mb-8">
        <h1 className="text-2xl font-extrabold tracking-tight mb-2 relative inline-block" style={{ color: 'var(--text-primary)' }}>
          🇬🇧 Luyện Đề Tiếng Anh — Thi vào Lớp 10
          <span className={`absolute bottom-0 left-0 h-[3px] bg-blue-500 rounded-full transition-all duration-700 ease-out ${mounted ? "w-full" : "w-0"}`} />
        </h1>
        <p className="text-sm leading-relaxed mt-2" style={{ color: 'var(--text-secondary)' }}>
          Mỗi đề gồm 40 câu trắc nghiệm, thời gian 60 phút. Có giải thích đáp án chi tiết cho mỗi câu.
        </p>
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
                  <div className="mt-3 flex flex-col gap-2">
                    <div className="rounded-lg px-3 py-2 text-center text-sm font-semibold flex items-center justify-center gap-1.5" style={{ background: 'var(--bg-interactive)', color: 'var(--text-disabled)' }}>
                      <span className="animate-pulse">🔒</span> Yêu cầu VIP
                    </div>
                    <a
                      href="https://zalo.me/0962715898"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="rounded-lg bg-blue-500 px-3 py-2 text-center text-sm font-semibold text-white hover:bg-blue-600 transition-all duration-200 no-underline hover:shadow-md hover:shadow-blue-500/25 active:scale-[0.97]"
                    >
                      💬 Liên hệ mở khóa
                    </a>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
        </>
      )}

      {/* VIP banner */}
      {!loading && items.length > 0 && !isVip && (
        <div
          className="mt-8 rounded-xl bg-gradient-to-r from-amber-50 to-orange-50 dark:from-amber-900/20 dark:to-orange-900/20 border border-amber-200/60 dark:border-amber-800/60 p-6 text-center"
          style={{ animation: "slideUp 0.5s ease-out 0.3s both" }}
        >
          <p className="text-lg font-bold text-amber-700 dark:text-amber-400 mb-1">
            <span className="inline-block animate-bounce">👑</span> Mở khóa tất cả đề thi
          </p>
          <p className="text-sm text-amber-600 dark:text-amber-500/80 mb-4">
            Liên hệ để nhận quyền truy cập toàn bộ kho đề thi + giải thích chi tiết + bài ôn tập
          </p>
          <a
            href="https://zalo.me/0962715898"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-block rounded-lg bg-amber-500 px-6 py-2.5 text-sm font-bold text-white hover:bg-amber-600 transition-all duration-200 no-underline hover:shadow-lg hover:shadow-amber-500/30 hover:-translate-y-0.5 active:scale-[0.97]"
          >
            💬 Liên hệ qua Zalo
          </a>
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
