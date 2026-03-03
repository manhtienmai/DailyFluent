"use client";

import { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";

interface FeedbackItem { id: number; title: string; description: string; type: string; status: string; status_display: string; vote_count: number; user_voted: boolean; user_email: string; created_at: string; comment_count: number; }
interface FeedbackList { items: FeedbackItem[]; page: number; total_pages: number; }

function FeedbackListContent() {
  const searchParams = useSearchParams();
  const [data, setData] = useState<FeedbackList>({ items: [], page: 1, total_pages: 1 });
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState(searchParams.get("status") || "all");
  const [sort, setSort] = useState(searchParams.get("sort") || "popular");
  const [type, setType] = useState(searchParams.get("type") || "all");

  const load = (s = status, so = sort, t = type) => {
    setLoading(true);
    fetch(`/api/v1/feedback?status=${s}&sort=${so}&type=${t}`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((d: FeedbackList) => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const vote = async (id: number) => {
    try {
      const r = await fetch(`/feedback/${id}/vote/`, { method: "POST", credentials: "include", headers: { "Content-Type": "application/json" } });
      const d = await r.json();
      if (d.success) {
        setData((prev) => ({ ...prev, items: prev.items.map((f) => f.id === id ? { ...f, vote_count: d.total_votes, user_voted: d.voted } : f) }));
      }
    } catch { /* ignore */ }
  };

  const apply = (key: string, val: string) => {
    const s2 = key === "status" ? val : status;
    const so2 = key === "sort" ? val : sort;
    const t2 = key === "type" ? val : type;
    if (key === "status") setStatus(val); if (key === "sort") setSort(val); if (key === "type") setType(val);
    load(s2, so2, t2);
  };

  return (
    <div style={{ maxWidth: 900, margin: "0 auto", padding: "2rem 1rem" }}>
      <div className="flex items-center justify-between flex-wrap gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2" style={{ color: "var(--text-primary)" }}>💬 Góc Cải Tiến</h1>
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>Đề xuất tính năng mới, báo lỗi và bình chọn cho ý tưởng hay</p>
        </div>
        <Link href="/feedback/create" className="px-5 py-2.5 rounded-xl text-sm font-semibold text-white no-underline" style={{ background: "#6366f1" }}>+ Tạo đề xuất mới</Link>
      </div>

      {/* Filters */}
      <div className="flex items-center justify-between flex-wrap gap-3 mb-6">
        <div className="flex gap-1 p-1 rounded-xl" style={{ background: "var(--bg-interactive)" }}>
          {[["all", "Tất cả"], ["in_progress", "Đang thực hiện"], ["done", "Đã hoàn thành"]].map(([v, l]) => (
            <button key={v} onClick={() => apply("status", v)} className="px-4 py-2 rounded-lg text-sm font-medium transition-all" style={{
              background: status === v ? "var(--bg-surface)" : "transparent",
              color: status === v ? "var(--text-primary)" : "var(--text-secondary)",
              cursor: "pointer", border: "none", boxShadow: status === v ? "0 1px 3px rgba(0,0,0,.1)" : "none",
            }}>{l}</button>
          ))}
        </div>
        <div className="flex gap-3 items-center">
          <select value={sort} onChange={(e) => apply("sort", e.target.value)} className="px-3 py-2 rounded-lg text-sm" style={{ background: "var(--bg-interactive)", color: "var(--text-primary)", border: "1px solid var(--border-default)" }}>
            <option value="popular">Phổ biến nhất</option>
            <option value="latest">Mới nhất</option>
          </select>
          <select value={type} onChange={(e) => apply("type", e.target.value)} className="px-3 py-2 rounded-lg text-sm" style={{ background: "var(--bg-interactive)", color: "var(--text-primary)", border: "1px solid var(--border-default)" }}>
            <option value="all">Tất cả</option>
            <option value="feature">Tính năng</option>
            <option value="bug">Báo lỗi</option>
          </select>
        </div>
      </div>

      {loading ? <div className="text-center py-12" style={{ color: "var(--text-tertiary)" }}>Đang tải...</div> : (
        <div className="space-y-3">
          {data.items.map((f) => (
            <Link key={f.id} href={`/feedback/${f.id}`} className="flex items-stretch gap-4 p-4 rounded-2xl no-underline transition-all hover:translate-y-[-1px]" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
              <button onClick={(e) => { e.preventDefault(); vote(f.id); }} className="flex flex-col items-center justify-center gap-1 px-3 py-2 rounded-xl min-w-[60px] transition-all" style={{
                background: f.user_voted ? "rgba(99,102,241,.12)" : "var(--bg-interactive)",
                border: f.user_voted ? "1px solid rgba(99,102,241,.3)" : "1px solid var(--border-default)",
                cursor: "pointer",
              }}>
                <span className="font-bold text-lg" style={{ color: f.user_voted ? "#6366f1" : "var(--text-primary)" }}>{f.vote_count}</span>
                <svg viewBox="0 0 24 24" fill="none" stroke={f.user_voted ? "#6366f1" : "var(--text-tertiary)"} strokeWidth="2.5" className="w-4 h-4"><polyline points="18 15 12 9 6 15" /></svg>
              </button>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap mb-1">
                  <h2 className="font-semibold text-sm truncate" style={{ color: "var(--text-primary)" }}>{f.title}</h2>
                  <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full" style={{ background: f.type === "feature" ? "rgba(99,102,241,.1)" : "rgba(239,68,68,.1)", color: f.type === "feature" ? "#6366f1" : "#ef4444" }}>{f.type === "feature" ? "Tính năng" : "Báo lỗi"}</span>
                  <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full" style={{ background: "rgba(16,185,129,.1)", color: "#10b981" }}>{f.status_display}</span>
                </div>
                <p className="text-xs line-clamp-1 mb-2" style={{ color: "var(--text-tertiary)" }}>{f.description}</p>
                <div className="flex items-center gap-4 text-xs" style={{ color: "var(--text-tertiary)" }}>
                  <span>👤 {f.user_email}</span>
                  <span>📅 {f.created_at}</span>
                  <span>💬 {f.comment_count} bình luận</span>
                </div>
              </div>
            </Link>
          ))}
          {!data.items.length && (
            <div className="text-center py-12">
              <div className="text-5xl mb-4">💬</div>
              <h3 className="font-bold mb-2" style={{ color: "var(--text-primary)" }}>Chưa có đề xuất nào</h3>
              <p className="mb-4" style={{ color: "var(--text-tertiary)" }}>Hãy là người đầu tiên!</p>
              <Link href="/feedback/create" className="px-6 py-3 rounded-xl text-sm font-semibold text-white no-underline inline-block" style={{ background: "#6366f1" }}>Tạo đề xuất đầu tiên</Link>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function FeedbackListPage() {
  return (
    <Suspense fallback={<div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Đang tải...</div>}>
      <FeedbackListContent />
    </Suspense>
  );
}
