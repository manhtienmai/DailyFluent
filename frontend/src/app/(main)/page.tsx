"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useLanguageMode, type StudyLanguage } from "@/hooks/useLanguageMode";
import "./home.css";

/* ── Types ─────────────────────────────────────────────── */
interface StreakData {
  current_streak: number;
  goal_completed: boolean;
  minutes_today: number;
  seconds_today: number;
  goal_minutes: number;
  cards_today: number;
  new_cards_today: number;
  reviews_today: number;
}
interface ProgressData {
  total_words: number;
  mastered: number;
  learned: number;
  review_due: number;
}
interface ProfileData {
  first_name?: string;
  username?: string;
}

/* ── Day helpers ───────────────────────────────────────── */
const DAY_LABELS = ["CN", "T2", "T3", "T4", "T5", "T6", "T7"];
function getLast7Days() {
  const today = new Date();
  const dow = today.getDay(); // 0=CN
  const days: { label: string; isToday: boolean }[] = [];
  for (let i = 6; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(today.getDate() - i);
    days.push({ label: DAY_LABELS[d.getDay()], isToday: i === 0 });
  }
  return days;
}

/* ── Quick actions ─────────────────────────────────────── */
interface QuickAction {
  href: string;
  icon: string;
  label: string;
  desc: string;
  color: string;
  bg: string;
  lang: StudyLanguage | "both";
}
const QUICK_ACTIONS: QuickAction[] = [
  { href: "/exam/english", icon: "🇬🇧", label: "Tiếng Anh 10", desc: "Luyện thi vào 10", color: "#2563eb", bg: "rgba(37,99,235,.08)", lang: "en" },
  { href: "/vocab/flashcards", icon: "🃏", label: "Flashcard", desc: "Ôn từ vựng", color: "#6366f1", bg: "rgba(99,102,241,.08)", lang: "both" },
  { href: "/exam/bunpou/flashcard", icon: "文", label: "Flashcard NP", desc: "Ôn ngữ pháp", color: "#ef4444", bg: "rgba(239,68,68,.08)", lang: "jp" },
  { href: "/kanji", icon: "漢", label: "Kanji", desc: "Luyện Hán tự", color: "#f59e0b", bg: "rgba(245,158,11,.08)", lang: "jp" },
  { href: "/grammar", icon: "文", label: "Ngữ pháp", desc: "Học văn phạm", color: "#f59e0b", bg: "rgba(245,158,11,.08)", lang: "jp" },
  { href: "/exam", icon: "📝", label: "Luyện thi", desc: "TOEIC · JLPT", color: "#10b981", bg: "rgba(16,185,129,.08)", lang: "both" },
  { href: "/vocab/games", icon: "🎮", label: "Games", desc: "Ôn vui vẻ", color: "#ec4899", bg: "rgba(236,72,153,.08)", lang: "both" },
];

/* ── Quiz stats from localStorage ──────────────────────── */
function getTodayQuizStats() {
  const quizTypes = ["usage", "bunpou", "sentence_order", "dokkai", "mojigoi"];
  let totalAnswered = 0;
  let totalCorrect = 0;
  let totalRevealed = 0;
  const details: { type: string; answered: number; correct: number }[] = [];

  for (const qt of quizTypes) {
    // Scan all localStorage keys for this quiz type
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (!key || !key.startsWith(`quiz_${qt}_`)) continue;
      try {
        const data = JSON.parse(localStorage.getItem(key) || "{}");
        const answers = data.answers || {};
        const revealed = data.revealed || [];
        const count = Object.keys(answers).length;
        if (count > 0) {
          totalAnswered += count;
          totalRevealed += revealed.length;
          // We don't have correct/wrong in localStorage easily, just count revealed as done
          details.push({ type: qt, answered: count, correct: revealed.length });
        }
      } catch { /* ignore */ }
    }
  }
  return { totalAnswered, totalRevealed, details };
}

/* ── Component ─────────────────────────────────────────── */
export default function HomePage() {
  const [streak, setStreak] = useState<StreakData | null>(null);
  const [progress, setProgress] = useState<ProgressData | null>(null);
  const [name, setName] = useState("");
  const [quizStats, setQuizStats] = useState({ totalAnswered: 0, totalRevealed: 0, details: [] as { type: string; answered: number; correct: number }[] });
  const { mode } = useLanguageMode();
  const days = getLast7Days();

  useEffect(() => {
    fetch("/api/v1/streak/status", { credentials: "include" })
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => d && setStreak(d))
      .catch(() => {});
    fetch("/api/v1/vocab/progress", { credentials: "include" })
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => d && setProgress(d))
      .catch(() => {});
    fetch("/api/v1/profile/me", { credentials: "include" })
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => d && setName(d.first_name || d.username || ""))
      .catch(() => {});
    // Read quiz stats from localStorage  
    try { setQuizStats(getTodayQuizStats()); } catch {}
  }, []);

  const streakNum = streak?.current_streak ?? 0;
  const totalWords = progress?.total_words ?? 0;
  const mastered = progress?.mastered ?? 0;
  const learning = totalWords - mastered;
  const pct = totalWords > 0 ? Math.round((mastered / totalWords) * 100) : 0;
  const minutesToday = streak?.minutes_today ?? 0;
  const secondsToday = streak?.seconds_today ?? 0;
  const goalMinutes = streak?.goal_minutes ?? 10;
  const timePct = Math.min(100, Math.round(((minutesToday * 60 + secondsToday) / (goalMinutes * 60)) * 100));
  const cardsDone = streak?.cards_today ?? 0;

  return (
    <div className="home-wrap">
      <div className="max-w-5xl mx-auto">

        {/* ─── Glass Header ─────────────────────────────── */}
        <header className="home-header">
          {/* Gradient border accent at top */}
          <div style={{
            position: "absolute", top: 0, left: 0, right: 0, height: 3,
            background: "linear-gradient(90deg, #a78bfa, #818cf8, #60a5fa, #34d399, #fbbf24, #f97316, #ef4444)",
          }} />

          {/* Top row: greeting + streak */}
          <div className="home-header-top">
            {/* Greeting */}
            <div className="home-greeting" style={{ display: "flex", alignItems: "center", gap: 14 }}>
              <div style={{
                width: 48, height: 48, borderRadius: 14,
                background: "linear-gradient(135deg, #8b5cf6, #6366f1)",
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: 24, flexShrink: 0,
                boxShadow: "0 4px 12px rgba(99,102,241,.3)",
              }}>
                👋
              </div>
              <div>
                <h1 style={{ margin: 0, fontSize: 20, fontWeight: 800, color: "var(--text-primary)", lineHeight: 1.3 }}>
                  Xin chào{name ? `, ${name}` : ""}!
                </h1>
                <div style={{ fontSize: 13, color: "var(--text-secondary)", marginTop: 2 }}>
                  Tiếp tục học tập hôm nay
                </div>
              </div>
            </div>

            {/* Streak badge + day dots */}
            <div style={{ display: "flex", alignItems: "center", gap: 12 }} className="home-streak-wrap">
              {/* Streak number */}
              <div className="home-streak-badge" style={{
                display: "flex", alignItems: "center", gap: 6,
                background: "linear-gradient(135deg, #fb923c, #f97316)",
                padding: "6px 14px", borderRadius: 20,
                boxShadow: "0 2px 8px rgba(249,115,22,.3)",
              }}>
                <span style={{ fontSize: 16 }}>🔥</span>
                <span style={{ fontSize: 18, fontWeight: 800, color: "#fff", lineHeight: 1 }}>{streakNum}</span>
                <span style={{ fontSize: 11, color: "rgba(255,255,255,.85)", fontWeight: 600 }}>ngày</span>
              </div>

              {/* Day dots */}
              <div className="home-day-dots" style={{ display: "flex", gap: 5 }}>
                {days.map((d, i) => {
                  const active = streakNum > (6 - i);
                  return (
                    <div key={i} className="home-day-dot" style={{
                      width: 32, height: 32, borderRadius: "50%",
                      display: "flex", alignItems: "center", justifyContent: "center",
                      fontSize: 10, fontWeight: 700, lineHeight: 1,
                      background: d.isToday
                        ? "linear-gradient(135deg, #f97316, #fb923c)"
                        : active
                          ? "linear-gradient(135deg, #fb923c, #fdba74)"
                          : "var(--bg-app-subtle)",
                      color: d.isToday || active ? "#fff" : "var(--text-tertiary)",
                      boxShadow: d.isToday ? "0 2px 8px rgba(249,115,22,.35)" : active ? "0 1px 4px rgba(249,115,22,.2)" : "none",
                      border: !active && !d.isToday ? "1px solid var(--border-subtle)" : "none",
                    }}>
                      {d.label}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Divider */}
          <div style={{ height: 1, background: "var(--border-default)", margin: "18px 0" }} />

          {/* Stats row */}
          <div className="home-header-stats">
            <Link href="/vocab/my-words?filter=mastered" style={{ textDecoration: "none" }}>
              <div style={{ fontSize: 28, fontWeight: 800, color: "#22c55e", lineHeight: 1.2 }}>{mastered}</div>
              <div style={{ fontSize: 11, fontWeight: 700, color: "var(--text-tertiary)", marginTop: 4, letterSpacing: "0.05em", textTransform: "uppercase" as const }}>Đã thuộc</div>
            </Link>
            <Link href="/vocab/my-words?filter=learning" style={{ textDecoration: "none" }}>
              <div style={{ fontSize: 28, fontWeight: 800, color: "#f59e0b", lineHeight: 1.2 }}>{learning}</div>
              <div style={{ fontSize: 11, fontWeight: 700, color: "var(--text-tertiary)", marginTop: 4, letterSpacing: "0.05em", textTransform: "uppercase" as const }}>Đang học</div>
            </Link>
            <Link href="/vocab/my-words?filter=all" style={{ textDecoration: "none" }}>
              <div style={{ fontSize: 28, fontWeight: 800, color: "#6366f1", lineHeight: 1.2 }}>{totalWords}</div>
              <div style={{ fontSize: 11, fontWeight: 700, color: "var(--text-tertiary)", marginTop: 4, letterSpacing: "0.05em", textTransform: "uppercase" as const }}>Tổng từ</div>
            </Link>
            <div>
              <div style={{ fontSize: 28, fontWeight: 800, color: "#f43f5e", lineHeight: 1.2 }}>{pct}%</div>
              <div style={{ fontSize: 11, fontWeight: 700, color: "var(--text-tertiary)", marginTop: 4, letterSpacing: "0.05em", textTransform: "uppercase" as const }}>Tiến độ</div>
            </div>
          </div>
        </header>

        {/* ─── Daily Progress Dashboard ───────────────────── */}
        <div className="home-progress-grid">
          {/* Study Time */}
          <div className="stat-card" style={{ "--accent": "#6366f1", "--accent-bg": "rgba(99,102,241,.08)" } as React.CSSProperties}>
            <div className="stat-ring-wrap">
              <svg width="64" height="64" viewBox="0 0 64 64">
                <circle cx="32" cy="32" r="27" fill="none" stroke="var(--border-subtle)" strokeWidth="5" opacity=".4" />
                <circle cx="32" cy="32" r="27" fill="none"
                  stroke={timePct >= 100 ? "#10b981" : "url(#timeGrad)"}
                  strokeWidth="5" strokeLinecap="round"
                  strokeDasharray={`${(Math.min(timePct, 100) / 100) * 169.6} 169.6`}
                  transform="rotate(-90 32 32)"
                  style={{ transition: "stroke-dasharray .8s cubic-bezier(.4,0,.2,1)" }}
                />
                <defs>
                  <linearGradient id="timeGrad" x1="0" y1="0" x2="1" y2="1">
                    <stop offset="0%" stopColor="#818cf8" />
                    <stop offset="100%" stopColor="#6366f1" />
                  </linearGradient>
                </defs>
              </svg>
              <span className="stat-ring-value" style={{ color: timePct >= 100 ? "#10b981" : "#6366f1" }}>
                {minutesToday > 0 ? `${minutesToday}p` : secondsToday > 0 ? `${secondsToday}s` : "0p"}
              </span>
            </div>
            <div className="stat-label">Thời gian học</div>
            <div className="stat-sub">
              {timePct >= 100 ? (
                <span style={{ color: "#10b981", fontWeight: 700 }}>✓ Đạt mục tiêu!</span>
              ) : (
                <>Mục tiêu: {goalMinutes}p</>
              )}
            </div>
          </div>

          {/* Quiz Answered */}
          <div className="stat-card" style={{ "--accent": "#8b5cf6", "--accent-bg": "rgba(139,92,246,.08)" } as React.CSSProperties}>
            <div className="stat-icon-box" style={{ background: "linear-gradient(135deg, rgba(139,92,246,.12), rgba(99,102,241,.08))" }}>
              <span style={{ fontSize: 28, fontWeight: 800, color: "#8b5cf6", lineHeight: 1 }}>{quizStats.totalAnswered}</span>
            </div>
            <div className="stat-label">Câu đã làm</div>
            <div className="stat-sub">{quizStats.totalRevealed} đã xem đáp án</div>
          </div>

          {/* Flashcard */}
          <div className="stat-card" style={{ "--accent": "#10b981", "--accent-bg": "rgba(16,185,129,.08)" } as React.CSSProperties}>
            <div className="stat-icon-box" style={{ background: "linear-gradient(135deg, rgba(16,185,129,.12), rgba(52,211,153,.08))" }}>
              <span style={{ fontSize: 28, fontWeight: 800, color: "#10b981", lineHeight: 1 }}>{cardsDone}</span>
            </div>
            <div className="stat-label">Flashcard</div>
            <div className="stat-sub">
              {(streak?.new_cards_today ?? 0)} mới · {(streak?.reviews_today ?? 0)} ôn
            </div>
          </div>

          {/* Vocab Progress */}
          <div className="stat-card" style={{ "--accent": "#f59e0b", "--accent-bg": "rgba(245,158,11,.08)" } as React.CSSProperties}>
            <div className="stat-icon-box" style={{ background: "linear-gradient(135deg, rgba(245,158,11,.12), rgba(251,191,36,.08))" }}>
              <span style={{ fontSize: 28, fontWeight: 800, color: "#f59e0b", lineHeight: 1 }}>{pct}%</span>
            </div>
            <div className="stat-label">Tiến độ từ</div>
            <div className="stat-sub">{mastered}/{totalWords} từ</div>
          </div>
        </div>

        

        {/* Quiz Type Breakdown (only if quizStats has entries) */}
        {quizStats.details.length > 0 && (
          <div style={{
            display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 20,
          }}>
            {quizStats.details.map((d, i) => (
              <span key={i} style={{
                fontSize: 10, fontWeight: 600, padding: "3px 8px", borderRadius: 8,
                background: "var(--bg-surface)", border: "1px solid var(--border-default)",
                color: "var(--text-secondary)",
              }}>
                {d.type === "usage" ? "用法" : d.type === "bunpou" ? "文法" : d.type === "sentence_order" ? "語順" : d.type === "dokkai" ? "読解" : d.type}
                : {d.answered} câu
              </span>
            ))}
          </div>
        )}

        {/* ─── CTA Buttons (compact) ────────────────────── */}
        <div className="home-cta-grid">
          <Link href="/vocab/flashcards" style={{
            display: "flex", alignItems: "center", gap: 10,
            padding: "14px 14px", borderRadius: 14,
            background: "linear-gradient(135deg, #4F46E5, #7C3AED)",
            textDecoration: "none", color: "#fff",
            boxShadow: "0 4px 12px rgba(79,70,229,.25)",
            transition: "transform .15s, box-shadow .15s",
          }}>
            <span style={{ fontSize: 20 }}>🃏</span>
            <div>
              <div style={{ fontSize: 13, fontWeight: 700 }}>Ôn từ vựng</div>
              <div style={{ fontSize: 10, opacity: 0.8 }}>Flashcard SRS</div>
            </div>
          </Link>
          {mode === "jp" && (
            <Link href="/exam/bunpou/flashcard" style={{
              display: "flex", alignItems: "center", gap: 10,
              padding: "14px 14px", borderRadius: 14,
              background: "linear-gradient(135deg, #dc2626, #ef4444)",
              textDecoration: "none", color: "#fff",
              boxShadow: "0 4px 12px rgba(220,38,38,.25)",
              transition: "transform .15s, box-shadow .15s",
            }}>
              <span style={{ fontSize: 20 }}>🃏</span>
              <div>
                <div style={{ fontSize: 13, fontWeight: 700 }}>Ôn ngữ pháp</div>
                <div style={{ fontSize: 10, opacity: 0.8 }}>Flashcard 文法</div>
              </div>
            </Link>
          )}
          {mode === "en" && (
            <Link href="/exam/english" style={{
              display: "flex", alignItems: "center", gap: 10,
              padding: "14px 14px", borderRadius: 14,
              background: "linear-gradient(135deg, #2563eb, #3b82f6)",
              textDecoration: "none", color: "#fff",
              boxShadow: "0 4px 12px rgba(37,99,235,.25)",
              transition: "transform .15s, box-shadow .15s",
            }}>
              <span style={{ fontSize: 20 }}>🇬🇧</span>
              <div>
                <div style={{ fontSize: 13, fontWeight: 700 }}>Tiếng Anh 10</div>
                <div style={{ fontSize: 10, opacity: 0.8 }}>Luyện thi vào 10</div>
              </div>
            </Link>
          )}
          <Link href="/streak" style={{
            display: "flex", alignItems: "center", gap: 10,
            padding: "14px 14px", borderRadius: 14,
            background: "linear-gradient(135deg, #f59e0b, #d97706)",
            textDecoration: "none", color: "#fff",
            boxShadow: "0 4px 12px rgba(245,158,11,.25)",
            transition: "transform .15s, box-shadow .15s",
          }}>
            <span style={{ fontSize: 20 }}>🔥</span>
            <div>
              <div style={{ fontSize: 13, fontWeight: 700 }}>Streak</div>
              <div style={{ fontSize: 10, opacity: 0.8 }}>Chuỗi ngày học</div>
            </div>
          </Link>
        </div>

        {/* ─── Quick Actions Grid ───────────────────────── */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-8">
          {QUICK_ACTIONS.filter(a => a.lang === "both" || a.lang === mode).map((a) => (
            <Link
              key={a.href}
              href={a.href}
              className="group flex flex-col items-center gap-2 p-4 rounded-2xl transition-all hover:translate-y-[-3px] hover:shadow-md no-underline"
              style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}
            >
              <div className="w-12 h-12 rounded-2xl flex items-center justify-center text-xl transition-transform group-hover:scale-110" style={{ background: a.bg, fontFamily: a.label === "Kanji" || a.label === "Ngữ pháp" ? "'Noto Sans JP', sans-serif" : "inherit" }}>
                {a.icon}
              </div>
              <div className="text-center">
                <div className="text-sm font-bold" style={{ color: "var(--text-primary)" }}>{a.label}</div>
                <div className="text-[10px]" style={{ color: "var(--text-tertiary)" }}>{a.desc}</div>
              </div>
            </Link>
          ))}
        </div>

        {/* ─── Module Links ─────────────────────────────── */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {[
            { href: "/vocab/sets", icon: "📦", title: "Bộ từ vựng", desc: "Quản lý và khám phá bộ từ", lang: "both" as const },
            { href: "/vocab/courses", icon: "📚", title: "Khóa học", desc: "Học theo lộ trình", lang: "both" as const },
            { href: "/vocab/my-words", icon: "📝", title: "Từ của tôi", desc: "Xem tiến độ từ vựng", lang: "both" as const },
            { href: "/exam/choukai", icon: "🎧", title: "聴解 Choukai", desc: "Luyện nghe JLPT", lang: "jp" as const },
            { href: "/exam/dokkai", icon: "📖", title: "読解 Dokkai", desc: "Luyện đọc hiểu", lang: "jp" as const },
            { href: "/exam/usage", icon: "✍️", title: "用法 Cách dùng từ", desc: "Quiz cách dùng từ", lang: "jp" as const },
            { href: "/grammar/books", icon: "📕", title: "Sách ngữ pháp", desc: "Học theo giáo trình", lang: "jp" as const },
            { href: "/exam/english", icon: "🇬🇧", title: "Tiếng Anh 10", desc: "Từ vựng + Ngữ pháp", lang: "en" as const },
            { href: "/exam/english/vocabulary", icon: "📚", title: "Từ vựng EN10", desc: "Học theo chủ đề", lang: "en" as const },
            { href: "/exam/english/grammar", icon: "✍️", title: "Ngữ pháp EN10", desc: "Học ngữ pháp Anh", lang: "en" as const },
          ].filter(item => item.lang === "both" || item.lang === mode).map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="flex items-center gap-3 p-4 rounded-xl transition-all hover:translate-y-[-2px] no-underline"
              style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}
            >
              <span className="text-xl">{item.icon}</span>
              <div className="min-w-0">
                <div className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>{item.title}</div>
                <div className="text-[10px]" style={{ color: "var(--text-tertiary)" }}>{item.desc}</div>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
