"use client";

import Link from "next/link";

const GAMES = [
  { slug: "mcq", icon: "🎯", title: "Trắc nghiệm", desc: "Chọn đáp án đúng", color: "#6366f1", bg: "rgba(99,102,241,.08)" },
  { slug: "matching", icon: "🔗", title: "Nối từ", desc: "Nối từ với nghĩa", color: "#10b981", bg: "rgba(16,185,129,.08)" },
  { slug: "listening", icon: "🎧", title: "Nghe và chọn", desc: "Luyện nghe từ vựng", color: "#f59e0b", bg: "rgba(245,158,11,.08)" },
  { slug: "fill", icon: "✏️", title: "Điền từ", desc: "Điền từ còn thiếu", color: "#ec4899", bg: "rgba(236,72,153,.08)" },
  { slug: "dictation", icon: "📝", title: "Chính tả", desc: "Nghe và viết lại từ", color: "#14b8a6", bg: "rgba(20,184,166,.08)" },
];

export default function GamesHubPage() {
  return (
    <div style={{ padding: "24px", minHeight: "100vh" }}>
      <div className="max-w-3xl mx-auto">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-extrabold mb-2" style={{ color: "var(--text-primary)" }}>
            🎮 Luyện từ vựng
          </h1>
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
            Chọn trò chơi để ôn tập theo cách thú vị
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {GAMES.map((g) => (
            <Link
              key={g.slug}
              href={`/vocab/games/${g.slug}`}
              className="group flex items-center gap-4 p-5 rounded-2xl transition-all hover:translate-y-[-3px] hover:shadow-lg no-underline"
              style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}
            >
              <div className="w-14 h-14 rounded-2xl flex items-center justify-center text-2xl flex-shrink-0" style={{ background: g.bg }}>
                {g.icon}
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-base font-bold mb-0.5" style={{ color: "var(--text-primary)" }}>{g.title}</h3>
                <p className="text-xs" style={{ color: "var(--text-secondary)" }}>{g.desc}</p>
              </div>
              <svg className="w-5 h-5 transition-transform group-hover:translate-x-1" fill="none" stroke={g.color} strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
              </svg>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
