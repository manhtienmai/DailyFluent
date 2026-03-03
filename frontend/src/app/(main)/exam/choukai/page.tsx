"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

interface ChoukaiBook {
  slug: string;
  title: string;
  description: string;
  question_count: number;
  level: string;
  cover_url: string;
}

export default function ChoukaiBookListPage() {
  const [books, setBooks] = useState<ChoukaiBook[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/v1/exam/choukai/books", { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d) => { setBooks(Array.isArray(d) ? d : []); setLoading(false); })
      .catch(() => { setBooks([]); setLoading(false); });
  }, []);

  return (
    <div style={{ padding: "24px", minHeight: "100vh" }}>
      <div className="max-w-5xl mx-auto">
        {/* Breadcrumb */}
        <nav className="mb-5 flex items-center gap-2 text-sm" style={{ color: "var(--text-tertiary)" }}>
          <Link href="/exam" className="hover:underline">Luyện thi</Link>
          <span>/</span>
          <span style={{ color: "var(--text-primary)" }}>聴解 Choukai</span>
        </nav>

        <div className="mb-6">
          <h1 className="text-2xl font-bold mb-1" style={{ color: "var(--text-primary)", fontFamily: "'Noto Sans JP', sans-serif" }}>
            🎧 聴解 Choukai
          </h1>
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>Luyện nghe JLPT — chọn sách để bắt đầu</p>
        </div>

        {loading ? (
          <div className="text-center py-16" style={{ color: "var(--text-tertiary)" }}>Đang tải...</div>
        ) : books.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {books.map((book) => (
              <Link
                key={book.slug}
                href={`/exam/choukai/${book.slug}`}
                className="block rounded-2xl overflow-hidden transition-all hover:translate-y-[-3px] hover:shadow-lg no-underline"
                style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}
              >
                {book.cover_url ? (
                  <div className="h-32 overflow-hidden">
                    <img src={book.cover_url} alt={book.title} className="w-full h-full object-cover" />
                  </div>
                ) : (
                  <div className="h-32 bg-gradient-to-br from-amber-100 to-amber-50 flex items-center justify-center">
                    <span className="text-4xl">🎧</span>
                  </div>
                )}
                <div className="p-4">
                  {book.level && (
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full mb-2 inline-block" style={{ background: "rgba(245,158,11,.1)", color: "#b45309", border: "1px solid rgba(245,158,11,.2)" }}>
                      {book.level}
                    </span>
                  )}
                  <h3 className="text-sm font-bold mb-1" style={{ color: "var(--text-primary)" }}>{book.title}</h3>
                  <p className="text-xs mb-2 line-clamp-2" style={{ color: "var(--text-secondary)" }}>{book.description || "Chưa có mô tả."}</p>
                  <div className="text-[10px]" style={{ color: "var(--text-tertiary)" }}>{book.question_count} câu hỏi</div>
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <div className="text-center py-16" style={{ color: "var(--text-secondary)" }}>
            <div className="text-5xl mb-4">🎧</div>
            <p className="text-lg font-medium">Chưa có sách</p>
            <p className="text-sm mt-1">Dữ liệu sẽ hiển thị khi API sẵn sàng.</p>
          </div>
        )}
      </div>
    </div>
  );
}
