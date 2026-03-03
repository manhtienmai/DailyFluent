"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

interface SetItem {
  item_id: number;
  word: string;
  language: string;
  part_of_speech: string;
  ipa: string;
  meaning: string;
  example: string;
  example_trans: string;
}

interface SetDetail {
  id: number;
  title: string;
  description: string;
  language: "en" | "jp";
  word_count: number;
  words: SetItem[];
}

export default function SetDetailPage() {
  const params = useParams();
  const pk = params.pk as string;

  const [data, setData] = useState<SetDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/v1/vocab/sets/${pk}`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d: SetDetail) => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, [pk]);

  if (loading) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Đang tải...</div>;
  if (!data) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Không tìm thấy bộ từ.</div>;

  return (
    <div style={{ padding: "24px", minHeight: "100vh" }}>
      <div className="max-w-4xl mx-auto">
        {/* Breadcrumb */}
        <nav className="mb-5 flex items-center gap-2 text-sm" style={{ color: "var(--text-tertiary)" }}>
          <Link href="/vocab/sets" className="hover:underline">Bộ từ</Link>
          <span>/</span>
          <span style={{ color: "var(--text-primary)" }}>{data.title}</span>
        </nav>

        {/* Header */}
        <div className="flex items-start justify-between gap-4 mb-6 flex-wrap">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full" style={{
                background: data.language === "jp" ? "rgba(239,68,68,.1)" : "rgba(59,130,246,.1)",
                color: data.language === "jp" ? "#dc2626" : "#2563eb",
                border: `1px solid ${data.language === "jp" ? "rgba(239,68,68,.25)" : "rgba(59,130,246,.25)"}`,
              }}>{data.language.toUpperCase()}</span>
              <span className="text-xs" style={{ color: "var(--text-tertiary)" }}>{data.word_count} từ</span>
            </div>
            <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>{data.title}</h1>
            {data.description && <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>{data.description}</p>}
          </div>
          <div className="flex gap-2">
            <Link href={`/vocab/sets/${pk}/study`} className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white" style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6)", textDecoration: "none" }}>
              📝 Học
            </Link>
          </div>
        </div>

        {/* Word list */}
        <div className="rounded-2xl overflow-hidden" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-[11px] uppercase tracking-wide" style={{ background: "var(--bg-app-subtle)", color: "var(--text-tertiary)" }}>
                <th className="px-4 py-3 text-left font-semibold">#</th>
                <th className="px-4 py-3 text-left font-semibold">Từ</th>
                {data.language === "jp" && <th className="px-4 py-3 text-left font-semibold">Cách đọc</th>}
                <th className="px-4 py-3 text-left font-semibold">Nghĩa</th>
              </tr>
            </thead>
            <tbody>
              {data.words?.map((item, i) => (
                <tr key={item.item_id} className="border-t" style={{ borderColor: "var(--border-subtle)" }}>
                  <td className="px-4 py-2.5 text-xs" style={{ color: "var(--text-tertiary)" }}>{i + 1}</td>
                  <td className="px-4 py-2.5 font-semibold" style={{ fontFamily: data.language === "jp" ? "'Noto Sans JP', sans-serif" : "inherit", color: "var(--text-primary)" }}>{item.word}</td>
                  {data.language === "jp" && (
                    <td className="px-4 py-2.5" style={{ fontFamily: "'Noto Sans JP', sans-serif", color: "var(--text-secondary)" }}>{item.ipa || "–"}</td>
                  )}
                  <td className="px-4 py-2.5" style={{ color: "var(--text-secondary)" }}>{item.meaning || "–"}</td>
                </tr>
              ))}
              {(!data.words || data.words.length === 0) && (
                <tr><td colSpan={4} className="px-4 py-8 text-center" style={{ color: "var(--text-tertiary)" }}>Chưa có từ nào.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
