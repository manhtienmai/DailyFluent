"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function SetCreatePage() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [language, setLanguage] = useState<"en" | "jp">("jp");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) { setError("Vui lòng nhập tên bộ từ."); return; }
    setSubmitting(true);
    setError("");
    try {
      const res = await fetch("/api/v1/vocab/sets", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ title, description, language }),
      });
      if (!res.ok) throw new Error("Failed");
      const d = await res.json();
      router.push(`/vocab/sets/${d.id}`);
    } catch {
      setError("Tạo bộ từ thất bại. Vui lòng thử lại.");
      setSubmitting(false);
    }
  };

  return (
    <div style={{ padding: "24px", minHeight: "100vh" }}>
      <div className="max-w-lg mx-auto">
        <nav className="mb-5 flex items-center gap-2 text-sm" style={{ color: "var(--text-tertiary)" }}>
          <Link href="/vocab/sets" className="hover:underline">Bộ từ</Link>
          <span>/</span>
          <span style={{ color: "var(--text-primary)" }}>Tạo mới</span>
        </nav>

        <h1 className="text-2xl font-bold mb-6" style={{ color: "var(--text-primary)" }}>✨ Tạo bộ từ mới</h1>

        <form onSubmit={handleSubmit} className="p-6 rounded-2xl space-y-5" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wide mb-1.5" style={{ color: "var(--text-secondary)" }}>Tên bộ từ *</label>
            <input type="text" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="VD: Từ vựng N2 Tuần 1" className="w-full p-3 rounded-xl text-sm border outline-none transition-all" style={{ background: "var(--bg-interactive)", borderColor: "var(--border-default)", color: "var(--text-primary)" }} />
          </div>
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wide mb-1.5" style={{ color: "var(--text-secondary)" }}>Mô tả</label>
            <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={3} placeholder="Mô tả ngắn về bộ từ..." className="w-full p-3 rounded-xl text-sm border outline-none transition-all resize-none" style={{ background: "var(--bg-interactive)", borderColor: "var(--border-default)", color: "var(--text-primary)" }} />
          </div>
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wide mb-1.5" style={{ color: "var(--text-secondary)" }}>Ngôn ngữ</label>
            <div className="flex gap-3">
              {(["jp", "en"] as const).map((l) => (
                <button key={l} type="button" onClick={() => setLanguage(l)} className="flex-1 py-2.5 rounded-xl text-sm font-semibold transition-all" style={{
                  background: language === l ? (l === "jp" ? "linear-gradient(135deg, #ef4444, #f87171)" : "linear-gradient(135deg, #3b82f6, #60a5fa)") : "var(--bg-interactive)",
                  color: language === l ? "#fff" : "var(--text-secondary)",
                  border: language === l ? "none" : "1px solid var(--border-default)",
                }}>
                  {l === "jp" ? "🇯🇵 Tiếng Nhật" : "🇺🇸 Tiếng Anh"}
                </button>
              ))}
            </div>
          </div>
          {error && <div className="p-3 rounded-xl text-sm" style={{ background: "rgba(254,226,226,.7)", color: "#dc2626", border: "1px solid rgba(252,165,165,.5)" }}>{error}</div>}
          <button type="submit" disabled={submitting} className="w-full py-3 rounded-xl text-sm font-semibold text-white transition-all" style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6)", opacity: submitting ? 0.6 : 1 }}>
            {submitting ? "Đang tạo..." : "Tạo bộ từ"}
          </button>
        </form>
      </div>
    </div>
  );
}
