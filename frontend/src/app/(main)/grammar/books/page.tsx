"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

interface GrammarBook {
  slug: string;
  title: string;
  description: string;
  level: string;
  point_count: number;
}

const badgeColors: Record<string, { bg: string; text: string; border: string }> = {
  n5: { bg: "#dcfce7", text: "#15803d", border: "#bbf7d0" },
  n4: { bg: "#ccfbf1", text: "#0f766e", border: "#99f6e4" },
  n3: { bg: "#dbeafe", text: "#1d4ed8", border: "#bfdbfe" },
  n2: { bg: "#ede9fe", text: "#6d28d9", border: "#ddd6fe" },
  n1: { bg: "#fef3c7", text: "#b45309", border: "#fde68a" },
};

export default function GrammarBooksPage() {
  const [books, setBooks] = useState<GrammarBook[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/v1/grammar/books", { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d) => { setBooks(Array.isArray(d) ? d : []); setLoading(false); })
      .catch(() => { setBooks([]); setLoading(false); });
  }, []);

  return (
    <div style={{ padding: "24px", minHeight: "100vh" }}>
      <div className="max-w-5xl mx-auto">
        <nav className="mb-5 flex items-center gap-2 text-sm" style={{ color: "var(--text-tertiary)" }}>
          <Link href="/grammar" className="hover:underline">Ngữ pháp</Link>
          <span>/</span>
          <span style={{ color: "var(--text-primary)" }}>Theo sách</span>
        </nav>

        <div className="mb-6">
          <h1 className="text-2xl font-bold mb-1" style={{ color: "var(--text-primary)" }}>📖 Ngữ pháp theo sách</h1>
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>Học ngữ pháp theo giáo trình</p>
        </div>

        {loading ? (
          <div className="text-center py-16" style={{ color: "var(--text-tertiary)" }}>Đang tải...</div>
        ) : books.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {books.map((b) => {
              const badge = badgeColors[b.level?.toLowerCase()] || badgeColors.n5;
              return (
                <Link
                  key={b.slug}
                  href={`/grammar/books/${b.slug}`}
                  className="block p-5 rounded-2xl transition-all hover:translate-y-[-3px] hover:shadow-lg no-underline"
                  style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}
                >
                  <div className="flex items-center gap-2 mb-3">
                    {b.level && (
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full" style={{ background: badge.bg, color: badge.text, border: `1px solid ${badge.border}` }}>
                        {b.level}
                      </span>
                    )}
                    <span className="text-[10px]" style={{ color: "var(--text-tertiary)" }}>{b.point_count} điểm ngữ pháp</span>
                  </div>
                  <h3 className="text-base font-bold mb-1" style={{ color: "var(--text-primary)" }}>{b.title}</h3>
                  <p className="text-xs line-clamp-2" style={{ color: "var(--text-secondary)" }}>{b.description || "Sách ngữ pháp."}</p>
                </Link>
              );
            })}
          </div>
        ) : (
          <div className="text-center py-16" style={{ color: "var(--text-secondary)" }}>
            <div className="text-5xl mb-4">📖</div>
            <p className="text-lg font-medium">Chưa có sách</p>
            <p className="text-sm mt-1">Dữ liệu sẽ hiển thị khi API sẵn sàng.</p>
          </div>
        )}
      </div>
    </div>
  );
}
