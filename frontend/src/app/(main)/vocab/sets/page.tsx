"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import "./sets.css";

interface VocabSet {
  id: number;
  title: string;
  description: string;
  language: "en" | "jp";
  word_count: number;
  toeic_level: string;
  set_number: number | null;
  course_title: string | null;
  status: string;
}

/* SVG Icons */
const PlusIcon = () => (
  <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
    <path d="M12 5v14M5 12h14" />
  </svg>
);

const WordsIcon = () => (
  <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25H12" />
  </svg>
);

const ArrowIcon = () => (
  <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12h15m0 0l-6.75-6.75M19.5 12l-6.75 6.75" />
  </svg>
);

const FolderIcon = () => (
  <svg width="44" height="44" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24" style={{ opacity: 0.35 }}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z" />
  </svg>
);

/* Decorative accent gradients per language */
const ACCENT: Record<string, { gradient: string; bg: string; border: string; text: string }> = {
  jp: { gradient: "linear-gradient(135deg, #ef4444 0%, #f97316 100%)", bg: "rgba(239,68,68,.08)", border: "rgba(239,68,68,.18)", text: "#dc2626" },
  en: { gradient: "linear-gradient(135deg, #3b82f6 0%, #6366f1 100%)", bg: "rgba(59,130,246,.08)", border: "rgba(59,130,246,.18)", text: "#2563eb" },
};

const LANG_FILTER = [
  { key: "all", label: "Tất cả", emoji: "🌐" },
  { key: "en", label: "English", emoji: "🇺🇸" },
  { key: "jp", label: "日本語", emoji: "🇯🇵" },
] as const;

export default function VocabSetListPage() {
  const [sets, setSets] = useState<VocabSet[]>([]);
  const [loading, setLoading] = useState(true);
  const [lang, setLang] = useState<"all" | "en" | "jp">("all");
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    setLoading(true);
    const params = new URLSearchParams();
    if (lang !== "all") params.set("language", lang);
    fetch(`/api/v1/vocab/sets?${params}`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d) => { setSets(Array.isArray(d) ? d : []); setLoading(false); })
      .catch(() => { setSets([]); setLoading(false); });
  }, [lang]);

  const filtered = searchQuery
    ? sets.filter((s) => s.title.toLowerCase().includes(searchQuery.toLowerCase()))
    : sets;

  return (
    <div className="vs-page">
      {/* ── Hero Header ── */}
      <header className="vs-hero">
        <div className="vs-hero-content">
          <div className="vs-hero-text">
            <h1 className="vs-hero-title">Bộ từ vựng</h1>
            <p className="vs-hero-sub">Quản lý và ôn tập các bộ từ vựng của bạn</p>
          </div>
          <Link href="/vocab/sets/create" className="vs-create-btn">
            <PlusIcon />
            <span>Tạo bộ mới</span>
          </Link>
        </div>

        {/* Search */}
        <div className="vs-search-wrap">
          <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24" className="vs-search-icon">
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
          </svg>
          <input
            type="text"
            placeholder="Tìm kiếm bộ từ..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="vs-search-input"
          />
        </div>
      </header>

      {/* ── Language Filter Pills ── */}
      <div className="vs-filter-bar">
        {LANG_FILTER.map((f) => (
          <button
            key={f.key}
            onClick={() => setLang(f.key)}
            className={`vs-filter-pill ${lang === f.key ? "vs-filter-pill--active" : ""}`}
          >
            <span className="vs-filter-emoji">{f.emoji}</span>
            {f.label}
            {lang === f.key && (
              <span className="vs-filter-count">
                {f.key === "all" ? sets.length : sets.filter((s) => s.language === f.key).length}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* ── Content ── */}
      {loading ? (
        <div className="vs-loading">
          <div className="vs-spinner" />
          <span>Đang tải...</span>
        </div>
      ) : filtered.length > 0 ? (
        <div className="vs-grid">
          {filtered.map((set, idx) => {
            const accent = ACCENT[set.language] || ACCENT.en;
            return (
              <Link key={set.id} href={`/vocab/sets/${set.id}`} className="vs-card" style={{ animationDelay: `${idx * 40}ms` }}>
                {/* Accent strip */}
                <div className="vs-card-accent" style={{ background: accent.gradient }} />

                <div className="vs-card-body">
                  {/* Top row: badges */}
                  <div className="vs-card-badges">
                    <span className="vs-lang-badge" style={{ background: accent.bg, color: accent.text, borderColor: accent.border }}>
                      {set.language.toUpperCase()}
                    </span>
                    {set.toeic_level && (
                      <span className="vs-level-badge">TOEIC {set.toeic_level}</span>
                    )}
                    {set.course_title && (
                      <span className="vs-course-badge">{set.course_title}</span>
                    )}
                  </div>

                  {/* Title */}
                  <h3 className="vs-card-title">{set.title}</h3>

                  {/* Description */}
                  <p className="vs-card-desc">{set.description || "Chưa có mô tả"}</p>

                  {/* Footer */}
                  <div className="vs-card-footer">
                    <div className="vs-word-count">
                      <WordsIcon />
                      <span><strong>{set.word_count}</strong> từ vựng</span>
                    </div>
                    <div className="vs-card-arrow">
                      <ArrowIcon />
                    </div>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      ) : (
        <div className="vs-empty">
          <div className="vs-empty-icon">
            <FolderIcon />
          </div>
          <h3 className="vs-empty-title">Chưa có bộ từ nào</h3>
          <p className="vs-empty-desc">
            {searchQuery ? "Không tìm thấy kết quả. Thử từ khóa khác." : "Tạo bộ từ đầu tiên để bắt đầu học."}
          </p>
          {!searchQuery && (
            <Link href="/vocab/sets/create" className="vs-empty-cta">
              <PlusIcon />
              Tạo bộ mới
            </Link>
          )}
        </div>
      )}

      
    </div>
  );
}
