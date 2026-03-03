"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";

export default function VocabSetDeletePage() {
  const params = useParams();
  const router = useRouter();
  const pk = params.pk as string;
  const [title, setTitle] = useState("");
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    fetch(`/api/v1/vocab/sets/${pk}`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((d: { title: string }) => { setTitle(d.title); setLoading(false); })
      .catch(() => setLoading(false));
  }, [pk]);

  const confirmDelete = async () => {
    setDeleting(true);
    try {
      const r = await fetch(`/api/v1/vocab/sets/${pk}/delete`, { method: "POST", credentials: "include" });
      if (r.ok) router.push("/vocab/sets");
    } catch { /* ignore */ }
    setDeleting(false);
  };

  if (loading) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Đang tải...</div>;

  return (
    <div style={{ maxWidth: 500, margin: "0 auto", padding: "4rem 1rem", textAlign: "center" }}>
      <div className="p-8 rounded-2xl" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
        <div className="text-5xl mb-4">⚠️</div>
        <h1 className="text-xl font-bold mb-3" style={{ color: "var(--text-primary)" }}>Xóa bộ từ?</h1>
        <p className="text-sm mb-6" style={{ color: "var(--text-secondary)" }}>Bạn có chắc chắn muốn xóa <b>&ldquo;{title}&rdquo;</b>? Hành động này không thể hoàn tác.</p>
        <div className="flex gap-3 justify-center">
          <Link href={`/vocab/sets/${pk}`} className="px-6 py-2.5 rounded-xl text-sm font-semibold no-underline" style={{ background: "var(--bg-interactive)", color: "var(--text-primary)", border: "1px solid var(--border-default)" }}>Hủy</Link>
          <button onClick={confirmDelete} disabled={deleting} className="px-6 py-2.5 rounded-xl text-sm font-semibold text-white" style={{ background: "#ef4444", opacity: deleting ? 0.6 : 1, border: "none", cursor: "pointer" }}>{deleting ? "Đang xóa..." : "Xóa bộ từ"}</button>
        </div>
      </div>
    </div>
  );
}
