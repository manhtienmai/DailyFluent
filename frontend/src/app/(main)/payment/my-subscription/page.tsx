"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

interface Subscription { plan_name: string; status: string; expires_at: string; features: string[]; }

export default function MySubscriptionPage() {
  const [sub, setSub] = useState<Subscription | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/v1/payment/my-subscription", { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((d: Subscription) => { setSub(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Đang tải...</div>;

  if (!sub) return (
    <div style={{ maxWidth: 500, margin: "0 auto", padding: "4rem 1rem", textAlign: "center" }}>
      <div className="text-5xl mb-4">🔒</div>
      <h1 className="text-xl font-bold mb-3" style={{ color: "var(--text-primary)" }}>Chưa có gói đăng ký</h1>
      <p className="mb-6" style={{ color: "var(--text-tertiary)" }}>Nâng cấp để truy cập tất cả tính năng.</p>
      <Link href="/payment" className="px-8 py-3 rounded-xl font-semibold text-white no-underline inline-block" style={{ background: "#6366f1" }}>Xem gói dịch vụ</Link>
    </div>
  );

  return (
    <div style={{ maxWidth: 500, margin: "0 auto", padding: "2rem 1rem" }}>
      <h1 className="text-2xl font-bold mb-6" style={{ color: "var(--text-primary)" }}>📋 Gói đăng ký</h1>
      <div className="p-6 rounded-2xl" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>{sub.plan_name}</h2>
          <span className="px-3 py-1 rounded-full text-xs font-bold" style={{ background: sub.status === "active" ? "rgba(16,185,129,.1)" : "rgba(245,158,11,.1)", color: sub.status === "active" ? "#10b981" : "#f59e0b" }}>
            {sub.status === "active" ? "Đang hoạt động" : sub.status}
          </span>
        </div>
        <p className="text-sm mb-4" style={{ color: "var(--text-tertiary)" }}>Hết hạn: {sub.expires_at}</p>
        <ul className="space-y-2">
          {sub.features?.map((f, i) => (
            <li key={i} className="flex items-start gap-2 text-sm" style={{ color: "var(--text-secondary)" }}>
              <span style={{ color: "#10b981" }}>✓</span> {f}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
