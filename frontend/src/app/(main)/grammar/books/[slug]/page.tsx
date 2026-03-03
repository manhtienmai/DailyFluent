"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

interface GrammarPoint {
  slug: string;
  title: string;
  meaning: string;
  level: string;
}

interface BookDetail {
  slug: string;
  title: string;
  description: string;
  level: string;
  points: GrammarPoint[];
}

const badgeColors: Record<string, { bg: string; text: string; border: string }> = {
  n5: { bg: "#dcfce7", text: "#15803d", border: "#bbf7d0" },
  n4: { bg: "#ccfbf1", text: "#0f766e", border: "#99f6e4" },
  n3: { bg: "#dbeafe", text: "#1d4ed8", border: "#bfdbfe" },
  n2: { bg: "#ede9fe", text: "#6d28d9", border: "#ddd6fe" },
  n1: { bg: "#fef3c7", text: "#b45309", border: "#fde68a" },
};

export default function GrammarBookDetailPage() {
  const params = useParams();
  const slug = params.slug as string;

  const [book, setBook] = useState<BookDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/v1/grammar/books/${slug}`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d: BookDetail) => { setBook(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, [slug]);

  if (loading) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Đang tải...</div>;
  if (!book) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Không tìm thấy. API chưa sẵn sàng.</div>;

  const badge = badgeColors[book.level?.toLowerCase()] || badgeColors.n5;

  return (
    <div style={{ padding: "24px", minHeight: "100vh" }}>
      <div className="max-w-4xl mx-auto">
        <nav className="mb-5 flex items-center gap-2 text-sm" style={{ color: "var(--text-tertiary)" }}>
          <Link href="/grammar" className="hover:underline">Ngữ pháp</Link>
          <span>/</span>
          <Link href="/grammar/books" className="hover:underline">Theo sách</Link>
          <span>/</span>
          <span style={{ color: "var(--text-primary)" }}>{book.title}</span>
        </nav>

        <div className="mb-6">
          <div className="flex items-center gap-2 mb-2">
            {book.level && <span className="text-[10px] font-bold px-2 py-0.5 rounded-full" style={{ background: badge.bg, color: badge.text, border: `1px solid ${badge.border}` }}>{book.level}</span>}
            <span className="text-xs" style={{ color: "var(--text-tertiary)" }}>{book.points?.length || 0} điểm ngữ pháp</span>
          </div>
          <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>{book.title}</h1>
          {book.description && <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>{book.description}</p>}
        </div>

        {book.points?.length > 0 ? (
          <div className="space-y-2">
            {book.points.map((p, i) => (
              <Link
                key={p.slug}
                href={`/grammar/${p.slug}`}
                className="flex items-center gap-4 p-4 rounded-xl transition-all hover:translate-y-[-2px] no-underline"
                style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}
              >
                <span className="w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold flex-shrink-0" style={{ background: "var(--bg-interactive)", color: "var(--text-secondary)" }}>
                  {i + 1}
                </span>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-semibold truncate" style={{ fontFamily: "'Noto Sans JP', sans-serif", color: "var(--text-primary)" }}>{p.title}</div>
                  <div className="text-xs truncate" style={{ color: "var(--text-secondary)" }}>{p.meaning}</div>
                </div>
                {p.level && <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-full flex-shrink-0" style={{ background: badge.bg, color: badge.text, border: `1px solid ${badge.border}` }}>{p.level}</span>}
              </Link>
            ))}
          </div>
        ) : (
          <div className="text-center py-12" style={{ color: "var(--text-tertiary)" }}>Chưa có điểm ngữ pháp.</div>
        )}
      </div>
    </div>
  );
}
