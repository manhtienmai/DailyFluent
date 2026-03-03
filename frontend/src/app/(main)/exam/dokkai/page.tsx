"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

interface DokkaiPassage {
  slug: string;
  title: string;
  level: string;
  question_count: number;
  description: string;
  reading_format: string;
  book_title: string | null;
}

export default function DokkaiListPage() {
  const [passages, setPassages] = useState<DokkaiPassage[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/v1/exam/dokkai/", { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d) => { setPassages(Array.isArray(d) ? d : []); setLoading(false); })
      .catch(() => { setPassages([]); setLoading(false); });
  }, []);

  return (
    <div style={{ padding: "24px", minHeight: "100vh" }}>
      <div className="max-w-5xl mx-auto">
        <nav className="mb-5 flex items-center gap-2 text-sm" style={{ color: "var(--text-tertiary)" }}>
          <Link href="/exam" className="hover:underline">Luyện thi</Link>
          <span>/</span>
          <span style={{ color: "var(--text-primary)" }}>読解 Dokkai</span>
        </nav>

        <div className="mb-6">
          <h1 className="text-2xl font-bold mb-1" style={{ color: "var(--text-primary)", fontFamily: "'Noto Sans JP', sans-serif" }}>
            📖 読解 Dokkai
          </h1>
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>Luyện đọc hiểu JLPT</p>
        </div>

        {loading ? (
          <div className="text-center py-16" style={{ color: "var(--text-tertiary)" }}>Đang tải...</div>
        ) : passages.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {passages.map((p) => (
              <Link
                key={p.slug}
                href={`/exam/dokkai/${p.slug}`}
                className="block p-5 rounded-2xl transition-all hover:translate-y-[-3px] hover:shadow-lg no-underline"
                style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}
              >
                <div className="flex items-center gap-2 mb-3">
                  {p.level && (
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full" style={{ background: "rgba(16,185,129,.1)", color: "#059669", border: "1px solid rgba(16,185,129,.2)" }}>
                      {p.level}
                    </span>
                  )}
                  {p.reading_format && (
                    <span className="text-[10px] font-medium px-2 py-0.5 rounded-full" style={{ background: "rgba(99,102,241,.08)", color: "#6366f1" }}>
                      {p.reading_format}
                    </span>
                  )}
                  <span className="text-[10px]" style={{ color: "var(--text-tertiary)" }}>{p.question_count} câu</span>
                </div>
                <h3 className="text-sm font-bold mb-1" style={{ color: "var(--text-primary)", fontFamily: "'Noto Sans JP', sans-serif" }}>{p.title}</h3>
                <p className="text-xs line-clamp-2" style={{ color: "var(--text-secondary)" }}>{p.description || p.book_title || "Đề đọc hiểu."}</p>
              </Link>
            ))}
          </div>
        ) : (
          <div className="text-center py-16" style={{ color: "var(--text-secondary)" }}>
            <div className="text-5xl mb-4">📖</div>
            <p className="text-lg font-medium">Chưa có bài đọc</p>
            <p className="text-sm mt-1">Dữ liệu sẽ hiển thị khi API sẵn sàng.</p>
          </div>
        )}
      </div>
    </div>
  );
}
