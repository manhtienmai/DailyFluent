"use client";

import { useState, useEffect, useRef } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";

interface DictationData {
  title: string;
  description: string;
  audio_url: string;
  transcript: string;
  hints: string[];
}

export default function DictationDetailPage() {
  const params = useParams();
  const slug = params.slug as string;
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const [data, setData] = useState<DictationData | null>(null);
  const [loading, setLoading] = useState(true);
  const [userText, setUserText] = useState("");
  const [showResult, setShowResult] = useState(false);

  useEffect(() => {
    fetch(`/api/v1/dictation/${slug}`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((d: DictationData) => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, [slug]);

  if (loading) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Đang tải...</div>;
  if (!data) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Không tìm thấy.</div>;

  const checkResult = () => setShowResult(true);

  return (
    <div style={{ maxWidth: 768, margin: "0 auto", padding: "2rem 1rem" }}>
      <Link href="/dictation" className="text-sm no-underline mb-4 inline-block" style={{ color: "var(--text-tertiary)" }}>← Tất cả bài dictation</Link>

      <h1 className="text-2xl font-bold mb-2" style={{ color: "var(--text-primary)" }}>{data.title}</h1>
      <p className="text-sm mb-6" style={{ color: "var(--text-secondary)" }}>{data.description}</p>

      {/* Audio player */}
      <div className="p-5 rounded-2xl mb-6" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
        <div className="flex items-center gap-4">
          <button onClick={() => audioRef.current?.play()} className="w-12 h-12 rounded-full flex items-center justify-center text-xl" style={{ background: "rgba(99,102,241,.1)", color: "#6366f1", border: "none", cursor: "pointer" }}>▶</button>
          <div className="flex-1">
            <audio ref={audioRef} src={data.audio_url} controls className="w-full" style={{ height: 40 }} />
          </div>
        </div>
        {data.hints?.length > 0 && (
          <div className="mt-4 pt-4" style={{ borderTop: "1px solid var(--border-default)" }}>
            <p className="text-xs font-semibold mb-2" style={{ color: "var(--text-secondary)" }}>Gợi ý:</p>
            <div className="flex flex-wrap gap-2">
              {data.hints.map((h, i) => <span key={i} className="text-xs px-2 py-1 rounded-lg" style={{ background: "rgba(99,102,241,.08)", color: "#6366f1" }}>{h}</span>)}
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="mb-6">
        <textarea value={userText} onChange={(e) => setUserText(e.target.value)} placeholder="Nghe và viết lại nội dung..." rows={6} className="w-full p-4 rounded-2xl text-sm resize-y" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)", color: "var(--text-primary)" }} />
      </div>

      {!showResult ? (
        <button onClick={checkResult} disabled={!userText.trim()} className="w-full py-3 rounded-xl font-bold text-white" style={{ background: userText.trim() ? "#6366f1" : "var(--border-default)", cursor: userText.trim() ? "pointer" : "not-allowed", border: "none" }}>Kiểm tra</button>
      ) : (
        <div className="p-5 rounded-2xl" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
          <h3 className="font-bold text-sm mb-3" style={{ color: "var(--text-primary)" }}>Đáp án:</h3>
          <p className="text-sm whitespace-pre-wrap mb-4" style={{ color: "var(--text-secondary)" }}>{data.transcript}</p>
          <button onClick={() => { setShowResult(false); setUserText(""); }} className="px-5 py-2 rounded-xl text-sm font-semibold text-white" style={{ background: "#6366f1", border: "none", cursor: "pointer" }}>Thử lại</button>
        </div>
      )}
    </div>
  );
}
