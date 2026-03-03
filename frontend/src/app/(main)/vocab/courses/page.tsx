"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

interface Course {
  id: number;
  slug: string;
  title: string;
  description: string;
  language: string;
  level: string;
  cover_image: string | null;
  set_count: number;
  total_words: number;
}

/* SVG icon helpers */
const BookIcon = () => (
  <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2">
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
  </svg>
);

const LangIcon = () => (
  <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2">
    <path strokeLinecap="round" strokeLinejoin="round" d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
  </svg>
);

const ChevronIcon = () => (
  <svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2.5">
    <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
  </svg>
);

/* Gradient palette for variety */
const GRADIENTS = [
  "linear-gradient(135deg, #ef4444, #dc2626)",
  "linear-gradient(135deg, #f97316, #ea580c)",
  "linear-gradient(135deg, #6366f1, #4f46e5)",
  "linear-gradient(135deg, #10b981, #059669)",
  "linear-gradient(135deg, #ec4899, #db2777)",
  "linear-gradient(135deg, #8b5cf6, #7c3aed)",
];

export default function CoursesHomePage() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/v1/vocab/courses", { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d) => { setCourses(Array.isArray(d) ? d : []); setLoading(false); })
      .catch(() => { setCourses([]); setLoading(false); });
  }, []);

  return (
    <div style={{ padding: "24px", minHeight: "100vh" }}>
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div style={{ marginBottom: 24 }}>
          <h1 style={{ fontSize: 22, fontWeight: 800, color: "var(--text-primary)", margin: 0 }}>📚 Khóa học từ vựng</h1>
          <p style={{ fontSize: 13, color: "var(--text-secondary)", marginTop: 4 }}>Học theo lộ trình có sẵn</p>
        </div>

        {loading ? (
          <div style={{ textAlign: "center", padding: "64px 0", color: "var(--text-tertiary)" }}>Đang tải...</div>
        ) : courses.length > 0 ? (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: 20 }}>
            {courses.map((c, idx) => (
              <Link
                key={c.slug}
                href={`/vocab/courses/${c.slug}`}
                style={{ textDecoration: "none", display: "block" }}
              >
                <article style={{
                  borderRadius: 16,
                  overflow: "hidden",
                  background: "var(--bg-surface)",
                  border: "1px solid var(--border-default)",
                  boxShadow: "0 2px 16px rgba(0,0,0,.06)",
                  transition: "transform .2s, box-shadow .2s",
                  cursor: "pointer",
                }}>
                  {/* Image section */}
                  <div style={{
                    height: 160,
                    background: c.cover_image
                      ? `url(${c.cover_image}) center/cover no-repeat`
                      : GRADIENTS[idx % GRADIENTS.length],
                    position: "relative",
                  }}>
                    {/* Badge */}
                    <div style={{
                      position: "absolute", top: 10, left: 10,
                      padding: "4px 10px", borderRadius: 8,
                      fontSize: 11, fontWeight: 700,
                      background: "rgba(255,255,255,.9)",
                      color: "#64748b",
                      backdropFilter: "blur(4px)",
                    }}>
                      Chưa bắt đầu
                    </div>
                  </div>

                  {/* Info section */}
                  <div style={{ padding: "14px 16px 16px" }}>
                    {/* Title */}
                    <h2 style={{
                      fontSize: 15, fontWeight: 700,
                      color: "var(--text-primary)",
                      margin: "0 0 10px",
                      lineHeight: 1.3,
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                    }}>
                      {c.title}
                    </h2>

                    {/* Stats row */}
                    <div style={{
                      display: "flex", alignItems: "center", gap: 0,
                      fontSize: 12, color: "var(--text-secondary)",
                      marginBottom: 12,
                    }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
                        <BookIcon />
                        <span><strong style={{ color: "var(--text-primary)" }}>{c.set_count}</strong> bộ</span>
                      </div>
                      <div style={{
                        width: 1, height: 14, background: "var(--border-default)",
                        margin: "0 12px", flexShrink: 0,
                      }} />
                      <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
                        <LangIcon />
                        <span><strong style={{ color: "var(--text-primary)" }}>{c.total_words}</strong> từ</span>
                      </div>
                    </div>

                    {/* Progress row */}
                    <div style={{
                      display: "flex", alignItems: "center", justifyContent: "space-between",
                    }}>
                      <div style={{ fontSize: 12, color: "var(--text-secondary)" }}>
                        <strong style={{ color: "var(--text-primary)" }}>0</strong>/{c.total_words} từ đã học • 0%
                      </div>
                      <div style={{
                        width: 28, height: 28, borderRadius: 8,
                        display: "flex", alignItems: "center", justifyContent: "center",
                        background: "var(--bg-app-subtle)",
                        color: "var(--text-secondary)",
                        flexShrink: 0,
                      }}>
                        <ChevronIcon />
                      </div>
                    </div>
                  </div>
                </article>
              </Link>
            ))}
          </div>
        ) : (
          <div style={{ textAlign: "center", padding: "64px 0", color: "var(--text-secondary)" }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>📚</div>
            <p style={{ fontSize: 16, fontWeight: 600 }}>Chưa có khóa học</p>
            <p style={{ fontSize: 13, marginTop: 4 }}>Dữ liệu sẽ hiển thị khi API sẵn sàng.</p>
          </div>
        )}
      </div>
    </div>
  );
}
