"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

interface Video { slug: string; title: string; thumbnail_url?: string; view_count: number; duration_label: string; category?: string; created_at: string; }
interface Category { slug: string; name: string; }

export default function VideoListPage() {
  const [videos, setVideos] = useState<Video[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [active, setActive] = useState("");
  const [loading, setLoading] = useState(true);

  const load = (cat = "") => {
    setLoading(true);
    const q = cat ? `?category=${cat}` : "";
    fetch(`/api/v1/videos${q}`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((d: { videos: Video[]; categories: Category[] }) => { setVideos(d.videos || []); setCategories(d.categories || []); setLoading(false); })
      .catch(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const pick = (slug: string) => { setActive(slug); load(slug); };

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto", padding: "2rem 1rem" }}>
      <h1 className="text-2xl font-bold mb-6" style={{ color: "var(--text-primary)" }}>🎬 Japanese Videos</h1>

      {/* Chips */}
      <div className="flex flex-wrap gap-2 mb-6">
        <button onClick={() => pick("")} className="px-3 py-1.5 rounded-full text-xs font-semibold transition-all" style={{
          background: !active ? "#10b981" : "var(--bg-surface)",
          color: !active ? "white" : "var(--text-secondary)",
          border: !active ? "none" : "1px solid var(--border-default)",
          cursor: "pointer",
        }}>全部</button>
        {categories.map((c) => (
          <button key={c.slug} onClick={() => pick(c.slug)} className="px-3 py-1.5 rounded-full text-xs font-semibold transition-all" style={{
            background: active === c.slug ? "#10b981" : "var(--bg-surface)",
            color: active === c.slug ? "white" : "var(--text-secondary)",
            border: active === c.slug ? "none" : "1px solid var(--border-default)",
            cursor: "pointer",
          }}>{c.name}</button>
        ))}
      </div>

      {loading ? <div className="text-center py-12" style={{ color: "var(--text-tertiary)" }}>Đang tải...</div> : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: "1.5rem" }}>
          {videos.map((v) => (
            <Link key={v.slug} href={`/videos/${v.slug}`} className="rounded-2xl overflow-hidden no-underline transition-all hover:translate-y-[-4px] hover:shadow-lg" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
              <div className="relative h-48" style={{ background: "var(--bg-interactive)" }}>
                {v.thumbnail_url ? <img src={v.thumbnail_url} alt={v.title} className="w-full h-full object-cover" /> : <div className="w-full h-full flex items-center justify-center" style={{ color: "var(--text-tertiary)" }}>No thumbnail</div>}
                <span className="absolute bottom-3 left-3 px-2.5 py-1 rounded-full text-xs font-semibold text-white" style={{ background: "rgba(0,0,0,.7)" }}>🎧 {v.view_count}</span>
                <span className="absolute bottom-3 right-3 px-2.5 py-1 rounded-full text-xs font-semibold text-white" style={{ background: "rgba(0,0,0,.7)" }}>⏱ {v.duration_label}</span>
              </div>
              <div className="p-4">
                <h2 className="font-semibold text-sm line-clamp-2 mb-2" style={{ color: "var(--text-primary)" }}>{v.title}</h2>
                <div className="flex items-center justify-between text-xs" style={{ color: "var(--text-tertiary)" }}>
                  <span className="px-3 py-1 rounded-xl font-semibold text-white" style={{ background: "#6366f1" }}>Podcast</span>
                  <span>{v.created_at}</span>
                </div>
              </div>
            </Link>
          ))}
          {!videos.length && <p className="col-span-full text-center py-8" style={{ color: "var(--text-tertiary)" }}>Chưa có video nào.</p>}
        </div>
      )}
    </div>
  );
}
