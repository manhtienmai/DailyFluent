"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function FeedbackCreatePage() {
  const router = useRouter();
  const [type, setType] = useState<"feature" | "bug">("feature");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !description.trim()) { setError("Vui lòng điền đầy đủ thông tin."); return; }
    setSubmitting(true);
    setError("");
    try {
      const r = await fetch("/api/v1/feedback/create", {
        method: "POST", credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type, title, description }),
      });
      if (r.ok) { router.push("/feedback"); }
      else { setError("Có lỗi xảy ra, vui lòng thử lại."); }
    } catch { setError("Lỗi kết nối."); }
    setSubmitting(false);
  };

  return (
    <div style={{ maxWidth: 600, margin: "0 auto", padding: "2rem 1rem" }}>
      <Link href="/feedback" className="text-sm no-underline mb-6 inline-flex items-center gap-1" style={{ color: "var(--text-tertiary)" }}>← Quay lại danh sách</Link>

      <div className="rounded-2xl overflow-hidden" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
        <div className="p-6" style={{ borderBottom: "1px solid var(--border-default)" }}>
          <h1 className="text-xl font-bold flex items-center gap-2" style={{ color: "var(--text-primary)" }}>➕ Tạo đề xuất mới</h1>
          <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>Chia sẻ ý tưởng tính năng mới hoặc báo lỗi</p>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {error && <div className="p-3 rounded-xl text-sm" style={{ background: "rgba(254,226,226,.7)", color: "#dc2626" }}>{error}</div>}

          {/* Type */}
          <div>
            <label className="block text-sm font-semibold mb-2" style={{ color: "var(--text-primary)" }}>Loại đề xuất *</label>
            <div className="grid grid-cols-2 gap-3">
              {(["feature", "bug"] as const).map((t) => (
                <button key={t} type="button" onClick={() => setType(t)} className="p-4 rounded-xl text-left transition-all" style={{
                  background: type === t ? (t === "feature" ? "rgba(99,102,241,.08)" : "rgba(239,68,68,.08)") : "var(--bg-interactive)",
                  border: `2px solid ${type === t ? (t === "feature" ? "#6366f1" : "#ef4444") : "var(--border-default)"}`,
                  cursor: "pointer",
                }}>
                  <div className="text-lg mb-1">{t === "feature" ? "⭐" : "🐛"}</div>
                  <div className="font-semibold text-sm" style={{ color: "var(--text-primary)" }}>{t === "feature" ? "Tính năng mới" : "Báo lỗi"}</div>
                  <div className="text-xs" style={{ color: "var(--text-tertiary)" }}>{t === "feature" ? "Đề xuất tính năng, cải tiến" : "Phản hồi lỗi, sự cố"}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Title */}
          <div>
            <label className="block text-sm font-semibold mb-1" style={{ color: "var(--text-primary)" }}>Tiêu đề *</label>
            <input value={title} onChange={(e) => setTitle(e.target.value)} maxLength={200} required placeholder="Nhập tiêu đề ngắn gọn, dễ hiểu..." className="w-full p-3 rounded-xl text-sm border" style={{ background: "var(--bg-interactive)", borderColor: "var(--border-default)", color: "var(--text-primary)" }} />
            <span className="text-xs" style={{ color: "var(--text-tertiary)" }}>Tối đa 200 ký tự</span>
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-semibold mb-1" style={{ color: "var(--text-primary)" }}>Mô tả chi tiết *</label>
            <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={8} required placeholder="Mô tả chi tiết..." className="w-full p-3 rounded-xl text-sm border resize-y" style={{ background: "var(--bg-interactive)", borderColor: "var(--border-default)", color: "var(--text-primary)" }} />
          </div>

          <div className="flex justify-end gap-3 pt-4" style={{ borderTop: "1px solid var(--border-default)" }}>
            <Link href="/feedback" className="px-5 py-2.5 rounded-xl text-sm font-semibold no-underline" style={{ color: "var(--text-secondary)" }}>Hủy</Link>
            <button type="submit" disabled={submitting} className="px-6 py-2.5 rounded-xl text-sm font-semibold text-white" style={{ background: "#6366f1", opacity: submitting ? 0.6 : 1, border: "none", cursor: "pointer" }}>
              {submitting ? "Đang gửi..." : "Gửi đề xuất"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
