"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";

interface Definition { part_of_speech: string; meaning: string; example?: string; example_trans?: string; }
interface WordData { word: string; ipa?: string; reading?: string; han_viet?: string; audio_url?: string; definitions: Definition[]; }

export default function VocabularyDetailPage() {
  const params = useParams();
  const word = decodeURIComponent(params.word as string);
  const [data, setData] = useState<WordData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/v1/vocab/english/${encodeURIComponent(word)}`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((d: WordData) => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, [word]);

  if (loading) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Đang tải...</div>;
  if (!data) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Không tìm thấy từ.</div>;

  return (
    <div style={{ maxWidth: 600, margin: "0 auto", padding: "2rem 1rem" }}>
      <Link href="/vocab/my-words" className="text-sm no-underline mb-6 inline-block" style={{ color: "var(--text-tertiary)" }}>← Quay lại</Link>

      <div className="p-6 rounded-2xl mb-6" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
        <div className="flex items-center gap-3 mb-4">
          {data.audio_url && <button onClick={() => new Audio(data.audio_url!).play()} className="w-10 h-10 rounded-full flex items-center justify-center text-lg" style={{ background: "rgba(99,102,241,.1)", color: "#6366f1", border: "none", cursor: "pointer" }}>🔊</button>}
          <div>
            <h1 className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>{data.word}</h1>
            <div className="flex gap-2 text-sm" style={{ color: "var(--text-tertiary)" }}>
              {data.ipa && <span>{data.ipa}</span>}
              {data.reading && <span>({data.reading})</span>}
              {data.han_viet && <span className="px-2 py-0.5 rounded text-xs font-medium" style={{ background: "rgba(99,102,241,.1)", color: "#6366f1" }}>{data.han_viet}</span>}
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        {data.definitions?.map((d, i) => (
          <div key={i} className="p-5 rounded-2xl" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
            <span className="inline-block px-2 py-0.5 rounded text-xs font-semibold mb-2" style={{ background: "rgba(99,102,241,.1)", color: "#6366f1" }}>{d.part_of_speech}</span>
            <p className="font-medium text-sm mb-2" style={{ color: "var(--text-primary)" }}>{d.meaning}</p>
            {d.example && <p className="text-sm italic" style={{ color: "var(--text-secondary)" }}>{d.example}</p>}
            {d.example_trans && <p className="text-xs mt-1" style={{ color: "var(--text-tertiary)" }}>{d.example_trans}</p>}
          </div>
        ))}
      </div>
    </div>
  );
}
