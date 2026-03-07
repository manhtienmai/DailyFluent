"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useLanguageMode } from "@/hooks/useLanguageMode";

interface ExamItem {
  slug: string;
  title: string;
  description: string;
  question_count: number;
  duration_minutes: number;
  category: string;
}

interface ExamCategory {
  slug: string;
  label: string;
  icon: string;
  description: string;
  color: string;
  href: string;
  lang: "en" | "jp";
}

const EXAM_CATEGORIES: ExamCategory[] = [
  { slug: "toeic", label: "TOEIC", icon: "📝", description: "Luyện đề TOEIC Reading & Listening", color: "#6366f1", href: "/exam/toeic", lang: "en" },
  { slug: "choukai", label: "聴解 Choukai", icon: "🎧", description: "Luyện nghe JLPT chọn đáp án", color: "#f59e0b", href: "/exam/choukai", lang: "jp" },
  { slug: "dokkai", label: "読解 Dokkai", icon: "📖", description: "Luyện đọc hiểu JLPT", color: "#10b981", href: "/exam/dokkai", lang: "jp" },
  { slug: "usage", label: "用法 Cách dùng từ", icon: "✍️", description: "Chọn câu dùng từ đúng", color: "#8b5cf6", href: "/exam/usage", lang: "jp" },
  { slug: "bunpou", label: "文法 Ngữ pháp", icon: "📝", description: "Điền chỗ trống ngữ pháp JLPT", color: "#ef4444", href: "/exam/bunpou", lang: "jp" },
  { slug: "books", label: "Sách đề", icon: "📚", description: "Bộ đề theo sách", color: "#ec4899", href: "/exam/books", lang: "jp" },
  { slug: "english", label: "🇬🇧 English Lớp 10", icon: "🇬🇧", description: "Luyện đề tiếng Anh thi vào lớp 10", color: "#3b82f6", href: "/exam/english", lang: "en" },
];

export default function ExamListPage() {
  const [exams, setExams] = useState<ExamItem[]>([]);
  const [loading, setLoading] = useState(true);
  const { mode } = useLanguageMode();

  const filteredCategories = EXAM_CATEGORIES.filter(cat => cat.lang === mode);

  useEffect(() => {
    fetch("/api/v1/exam/list", { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d) => { setExams(Array.isArray(d) ? d : []); setLoading(false); })
      .catch(() => { setExams([]); setLoading(false); });
  }, []);

  return (
    <div style={{ padding: "24px", minHeight: "100vh" }}>
      <div className="max-w-5xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-extrabold mb-2" style={{ color: "var(--text-primary)" }}>📝 Luyện thi</h1>
        </div>

        {/* Category cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
          {filteredCategories.map((cat) => (
            <Link
              key={cat.slug}
              href={cat.href}
              className="group flex items-center gap-4 p-5 rounded-2xl transition-all hover:translate-y-[-3px] hover:shadow-lg no-underline"
              style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}
            >
              <div className="w-14 h-14 rounded-2xl flex items-center justify-center text-2xl flex-shrink-0" style={{ background: `${cat.color}14` }}>
                {cat.icon}
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-base font-bold mb-0.5" style={{ color: "var(--text-primary)", fontFamily: cat.slug === "choukai" || cat.slug === "dokkai" ? "'Noto Sans JP', sans-serif" : "inherit" }}>
                  {cat.label}
                </h3>
                <p className="text-xs" style={{ color: "var(--text-secondary)" }}>{cat.description}</p>
              </div>
              <svg className="w-5 h-5 transition-transform group-hover:translate-x-1" fill="none" stroke={cat.color} strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
              </svg>
            </Link>
          ))}
        </div>

        {/* Recent exams */}
        {loading ? (
          <div className="text-center py-12" style={{ color: "var(--text-tertiary)" }}>Đang tải...</div>
        ) : exams.length > 0 && (
          <div>
            <h2 className="text-lg font-bold mb-4" style={{ color: "var(--text-primary)" }}>Đề thi gần đây</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {exams.map((e) => (
                <Link
                  key={e.slug}
                  href={`/exam/${e.slug}`}
                  className="block p-4 rounded-xl transition-all hover:translate-y-[-2px] no-underline"
                  style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}
                >
                  <h3 className="text-sm font-bold mb-1 truncate" style={{ color: "var(--text-primary)" }}>{e.title}</h3>
                  <p className="text-xs mb-2 line-clamp-2" style={{ color: "var(--text-secondary)" }}>{e.description || "Chưa có mô tả."}</p>
                  <div className="flex items-center gap-3 text-[10px]" style={{ color: "var(--text-tertiary)" }}>
                    <span>{e.question_count} câu</span>
                    {e.duration_minutes > 0 && <span>{e.duration_minutes} phút</span>}
                  </div>
                </Link>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
