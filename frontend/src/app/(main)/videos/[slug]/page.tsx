"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";

interface TranscriptLine { start_time: number; text: string; }
interface VideoData { title: string; youtube_id: string; level: string; category?: string; description?: string; view_count: number; created_at: string; transcript_lines: TranscriptLine[]; }

export default function VideoDetailPage() {
  const params = useParams();
  const slug = params.slug as string;
  const [video, setVideo] = useState<VideoData | null>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<"video" | "transcript">("video");

  useEffect(() => {
    fetch(`/api/v1/videos/${slug}`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((d: VideoData) => { setVideo(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, [slug]);

  if (loading) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Đang tải...</div>;
  if (!video) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Không tìm thấy video.</div>;

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto", padding: "2rem 1rem" }}>
      <Link href="/videos" className="text-sm no-underline mb-4 inline-block" style={{ color: "var(--text-tertiary)" }}>← Tất cả video</Link>

      {/* Tabs */}
      <div className="flex gap-1 p-1 rounded-full mb-4 w-fit" style={{ background: "var(--bg-interactive)" }}>
        {(["video", "transcript"] as const).map((t) => (
          <button key={t} onClick={() => setTab(t)} className="px-4 py-1.5 rounded-full text-xs font-semibold transition-all" style={{
            background: tab === t ? "#10b981" : "transparent",
            color: tab === t ? "white" : "var(--text-secondary)",
            border: "none", cursor: "pointer",
          }}>{t === "video" ? "🎬 Video" : "📝 Chép chính tả"}</button>
        ))}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: tab === "transcript" ? "1fr" : "2fr 1fr", gap: "1.5rem" }}>
        {/* Video */}
        <div>
          <div className="rounded-2xl overflow-hidden mb-4" style={{ background: "#000" }}>
            <div style={{ position: "relative", paddingBottom: "56.25%", height: 0 }}>
              <iframe src={`https://www.youtube.com/embed/${video.youtube_id}?rel=0&modestbranding=1`} allowFullScreen style={{ position: "absolute", top: 0, left: 0, width: "100%", height: "100%", border: "none" }} />
            </div>
          </div>
          <h1 className="text-xl font-bold mb-2" style={{ color: "var(--text-primary)" }}>{video.title}</h1>
          <div className="flex flex-wrap gap-2 mb-2">
            <span className="px-2 py-0.5 rounded-full text-xs font-medium" style={{ background: "rgba(16,185,129,.1)", color: "#10b981" }}>{video.level}</span>
            {video.category && <span className="px-2 py-0.5 rounded-full text-xs" style={{ background: "var(--bg-interactive)", color: "var(--text-secondary)" }}>{video.category}</span>}
          </div>
          <div className="text-xs mb-4" style={{ color: "var(--text-tertiary)" }}>{video.view_count} views • {video.created_at}</div>
          {video.description && <div className="p-4 rounded-2xl text-sm" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)", color: "var(--text-secondary)" }}>{video.description}</div>}
        </div>

        {/* Transcript sidebar */}
        <aside className="p-4 rounded-2xl" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)", maxHeight: 520, overflowY: "auto" }}>
          <h2 className="text-sm font-semibold mb-3" style={{ color: "var(--text-primary)" }}>Phụ đề</h2>
          <div className="space-y-2">
            {video.transcript_lines?.map((l, i) => (
              <div key={i} className="flex gap-3 px-2 py-1 rounded-xl text-sm cursor-pointer transition-all hover:bg-[rgba(16,185,129,.06)]">
                <span className="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 text-xs" style={{ background: "var(--bg-interactive)", color: "var(--text-tertiary)" }}>▶</span>
                <p style={{ color: "var(--text-secondary)" }}>{l.text}</p>
              </div>
            ))}
            {(!video.transcript_lines || !video.transcript_lines.length) && <p className="text-xs" style={{ color: "var(--text-tertiary)" }}>Chưa có phụ đề.</p>}
          </div>
        </aside>
      </div>
    </div>
  );
}
