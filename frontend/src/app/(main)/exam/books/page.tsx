"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

interface ExamBook {
  slug: string;
  title: string;
  description: string;
  exam_count: number;
  level: string;
}

export default function ExamBookListPage() {
  const [books, setBooks] = useState<ExamBook[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/v1/exam/books", { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d) => { setBooks(Array.isArray(d) ? d : []); setLoading(false); })
      .catch(() => { setBooks([]); setLoading(false); });
  }, []);

  return (
    <div style={{ padding: "24px", minHeight: "100vh" }}>
      <div className="max-w-5xl mx-auto">
        <nav className="mb-5 flex items-center gap-2 text-sm" style={{ color: "var(--text-tertiary)" }}>
          <Link href="/exam" className="hover:underline">Luyện thi</Link>
          <span>/</span>
          <span style={{ color: "var(--text-primary)" }}>Sách đề</span>
        </nav>

        <div className="mb-6">
          <h1 className="text-2xl font-bold mb-1" style={{ color: "var(--text-primary)" }}>📚 Sách đề thi</h1>
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>Luyện đề theo bộ sách</p>
        </div>

        {loading ? (
          <div className="text-center py-16" style={{ color: "var(--text-tertiary)" }}>Đang tải...</div>
        ) : books.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {books.map((b) => (
              <Link key={b.slug} href={`/exam/books/${b.slug}`} className="block p-5 rounded-2xl transition-all hover:translate-y-[-3px] hover:shadow-lg no-underline" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
                {b.level && <span className="text-[10px] font-bold px-2 py-0.5 rounded-full mb-2 inline-block" style={{ background: "rgba(236,72,153,.1)", color: "#be185d", border: "1px solid rgba(236,72,153,.2)" }}>{b.level}</span>}
                <h3 className="text-base font-bold mb-1" style={{ color: "var(--text-primary)" }}>{b.title}</h3>
                <p className="text-xs mb-2 line-clamp-2" style={{ color: "var(--text-secondary)" }}>{b.description || "Bộ đề thi."}</p>
                <div className="text-[10px]" style={{ color: "var(--text-tertiary)" }}>{b.exam_count} đề</div>
              </Link>
            ))}
          </div>
        ) : (
          <div className="text-center py-16" style={{ color: "var(--text-secondary)" }}>
            <div className="text-5xl mb-4">📚</div>
            <p>Chưa có sách đề.</p>
          </div>
        )}
      </div>
    </div>
  );
}
