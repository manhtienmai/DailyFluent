"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";

interface Comment { id: number; user_email: string; text: string; created_at: string; }
interface FeedbackDetail { id: number; title: string; description: string; type: string; status: string; status_display: string; vote_count: number; user_voted: boolean; user_email: string; created_at: string; comments: Comment[]; }

export default function FeedbackDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [fb, setFb] = useState<FeedbackDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [comment, setComment] = useState("");
  const [posting, setPosting] = useState(false);

  useEffect(() => {
    fetch(`/api/v1/feedback/${id}`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((d: FeedbackDetail) => { setFb(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, [id]);

  const vote = async () => {
    if (!fb) return;
    try {
      const r = await fetch(`/feedback/${fb.id}/vote/`, { method: "POST", credentials: "include", headers: { "Content-Type": "application/json" } });
      const d = await r.json();
      if (d.success) setFb({ ...fb, vote_count: d.total_votes, user_voted: d.voted });
    } catch { /* ignore */ }
  };

  const postComment = async () => {
    if (!comment.trim() || !fb) return;
    setPosting(true);
    try {
      const r = await fetch(`/api/v1/feedback/${fb.id}/comment`, { method: "POST", credentials: "include", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text: comment }) });
      const d = await r.json();
      if (d.success) {
        setFb({ ...fb, comments: [...fb.comments, d.comment] });
        setComment("");
      }
    } catch { /* ignore */ }
    setPosting(false);
  };

  if (loading) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Đang tải...</div>;
  if (!fb) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Không tìm thấy.</div>;

  return (
    <div style={{ maxWidth: 700, margin: "0 auto", padding: "2rem 1rem" }}>
      <Link href="/feedback" className="text-sm no-underline mb-6 inline-block" style={{ color: "var(--text-tertiary)" }}>← Quay lại</Link>

      <div className="flex gap-4 mb-6">
        <button onClick={vote} className="flex flex-col items-center gap-1 px-3 py-4 rounded-xl" style={{
          background: fb.user_voted ? "rgba(99,102,241,.12)" : "var(--bg-interactive)",
          border: fb.user_voted ? "1px solid rgba(99,102,241,.3)" : "1px solid var(--border-default)",
          cursor: "pointer", minWidth: 60,
        }}>
          <span className="font-bold text-xl" style={{ color: fb.user_voted ? "#6366f1" : "var(--text-primary)" }}>{fb.vote_count}</span>
          <svg viewBox="0 0 24 24" fill="none" stroke={fb.user_voted ? "#6366f1" : "var(--text-tertiary)"} strokeWidth="2.5" className="w-4 h-4"><polyline points="18 15 12 9 6 15" /></svg>
        </button>
        <div>
          <div className="flex items-center gap-2 flex-wrap mb-2">
            <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full" style={{ background: fb.type === "feature" ? "rgba(99,102,241,.1)" : "rgba(239,68,68,.1)", color: fb.type === "feature" ? "#6366f1" : "#ef4444" }}>{fb.type === "feature" ? "Tính năng" : "Báo lỗi"}</span>
            <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full" style={{ background: "rgba(16,185,129,.1)", color: "#10b981" }}>{fb.status_display}</span>
          </div>
          <h1 className="text-xl font-bold mb-2" style={{ color: "var(--text-primary)" }}>{fb.title}</h1>
          <div className="text-xs" style={{ color: "var(--text-tertiary)" }}>👤 {fb.user_email} • 📅 {fb.created_at}</div>
        </div>
      </div>

      <div className="p-5 rounded-2xl mb-6" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
        <p className="text-sm whitespace-pre-wrap" style={{ color: "var(--text-secondary)" }}>{fb.description}</p>
      </div>

      {/* Comments */}
      <div className="mb-6">
        <h3 className="font-bold text-sm mb-4" style={{ color: "var(--text-primary)" }}>💬 Bình luận ({fb.comments?.length || 0})</h3>
        <div className="space-y-3">
          {fb.comments?.map((c) => (
            <div key={c.id} className="p-4 rounded-xl" style={{ background: "var(--bg-interactive)" }}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold" style={{ color: "var(--text-primary)" }}>{c.user_email}</span>
                <span className="text-xs" style={{ color: "var(--text-tertiary)" }}>{c.created_at}</span>
              </div>
              <p className="text-sm" style={{ color: "var(--text-secondary)" }}>{c.text}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="flex gap-3">
        <input value={comment} onChange={(e) => setComment(e.target.value)} placeholder="Viết bình luận..." className="flex-1 p-3 rounded-xl text-sm border" style={{ background: "var(--bg-interactive)", borderColor: "var(--border-default)", color: "var(--text-primary)" }} onKeyDown={(e) => e.key === "Enter" && postComment()} />
        <button onClick={postComment} disabled={posting || !comment.trim()} className="px-5 py-3 rounded-xl text-sm font-semibold text-white" style={{ background: "#6366f1", opacity: posting || !comment.trim() ? 0.5 : 1, border: "none", cursor: "pointer" }}>Gửi</button>
      </div>
    </div>
  );
}
