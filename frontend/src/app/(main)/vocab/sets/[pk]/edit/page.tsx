"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";

interface SetData { pk: number; title: string; description: string; }

export default function VocabSetEditPage() {
  const params = useParams();
  const router = useRouter();
  const pk = params.pk as string;

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`/api/v1/vocab/sets/${pk}`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((d: SetData) => { setTitle(d.title); setDescription(d.description || ""); setLoading(false); })
      .catch(() => setLoading(false));
  }, [pk]);

  const save = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) { setError("Tên không được để trống."); return; }
    setSaving(true); setError("");
    try {
      const r = await fetch(`/api/v1/vocab/sets/${pk}/edit`, {
        method: "POST", credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, description }),
      });
      if (r.ok) router.push(`/vocab/sets/${pk}`);
      else setError("Lỗi khi lưu.");
    } catch { setError("Lỗi kết nối."); }
    setSaving(false);
  };

  if (loading) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Đang tải...</div>;

  return (
    <div style={{ maxWidth: 500, margin: "0 auto", padding: "2rem 1rem" }}>
      <Link href={`/vocab/sets/${pk}`} className="text-sm no-underline mb-6 inline-block" style={{ color: "var(--text-tertiary)" }}>← Quay lại</Link>
      <h1 className="text-2xl font-bold mb-6" style={{ color: "var(--text-primary)" }}>✏️ Chỉnh sửa bộ từ</h1>

      <div className="p-6 rounded-2xl" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
        {error && <div className="p-3 rounded-xl text-sm mb-4" style={{ background: "rgba(254,226,226,.7)", color: "#dc2626" }}>{error}</div>}
        <form onSubmit={save} className="space-y-4">
          <div>
            <label className="block text-sm font-semibold mb-1" style={{ color: "var(--text-primary)" }}>Tên bộ từ *</label>
            <input value={title} onChange={(e) => setTitle(e.target.value)} required className="w-full p-3 rounded-xl text-sm border" style={{ background: "var(--bg-interactive)", borderColor: "var(--border-default)", color: "var(--text-primary)" }} />
          </div>
          <div>
            <label className="block text-sm font-semibold mb-1" style={{ color: "var(--text-primary)" }}>Mô tả</label>
            <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={4} className="w-full p-3 rounded-xl text-sm border resize-y" style={{ background: "var(--bg-interactive)", borderColor: "var(--border-default)", color: "var(--text-primary)" }} />
          </div>
          <div className="flex justify-end gap-3">
            <Link href={`/vocab/sets/${pk}`} className="px-5 py-2.5 rounded-xl text-sm font-semibold no-underline" style={{ color: "var(--text-secondary)" }}>Hủy</Link>
            <button type="submit" disabled={saving} className="px-6 py-2.5 rounded-xl text-sm font-semibold text-white" style={{ background: "#6366f1", opacity: saving ? 0.6 : 1, border: "none", cursor: "pointer" }}>{saving ? "Đang lưu..." : "Lưu"}</button>
          </div>
        </form>
      </div>
    </div>
  );
}
