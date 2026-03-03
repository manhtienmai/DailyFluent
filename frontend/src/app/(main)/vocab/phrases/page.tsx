"use client";

import { useState, useEffect } from "react";

interface Phrase { id: number; phrase: string; meaning: string; example?: string; }

export default function PhraseListPage() {
  const [phrases, setPhrases] = useState<Phrase[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    fetch("/api/v1/vocab/phrases", { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((d: Phrase[]) => { setPhrases(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  const filtered = phrases.filter((p) => !search || p.phrase.toLowerCase().includes(search.toLowerCase()) || p.meaning.toLowerCase().includes(search.toLowerCase()));

  if (loading) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Đang tải...</div>;

  return (
    <div style={{ maxWidth: 700, margin: "0 auto", padding: "2rem 1rem" }}>
      <h1 className="text-2xl font-bold mb-2" style={{ color: "var(--text-primary)" }}>💬 Cụm từ</h1>
      <p className="text-sm mb-6" style={{ color: "var(--text-tertiary)" }}>{phrases.length} cụm từ</p>

      <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Tìm kiếm..." className="w-full p-3 rounded-xl text-sm border mb-6" style={{ background: "var(--bg-interactive)", borderColor: "var(--border-default)", color: "var(--text-primary)" }} />

      <div className="space-y-2">
        {filtered.map((p) => (
          <div key={p.id} className="p-4 rounded-xl" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
            <div className="flex items-start justify-between gap-3">
              <div>
                <span className="font-semibold text-sm" style={{ color: "var(--text-primary)" }}>{p.phrase}</span>
                <span className="text-sm ml-2" style={{ color: "var(--text-tertiary)" }}>— {p.meaning}</span>
              </div>
            </div>
            {p.example && <p className="text-xs mt-1 italic" style={{ color: "var(--text-tertiary)" }}>{p.example}</p>}
          </div>
        ))}
        {!filtered.length && <p className="text-center py-8" style={{ color: "var(--text-tertiary)" }}>Không tìm thấy.</p>}
      </div>
    </div>
  );
}
