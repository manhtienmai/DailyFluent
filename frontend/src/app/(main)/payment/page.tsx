"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

interface Plan { slug: string; name: string; price: number; price_label: string; duration_label: string; features: string[]; is_popular?: boolean; }

export default function PaymentPlansPage() {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/v1/payment/plans", { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((d: Plan[]) => { setPlans(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Đang tải...</div>;

  return (
    <div style={{ maxWidth: 900, margin: "0 auto", padding: "2rem 1rem" }}>
      <div className="text-center mb-8">
        <h1 className="text-2xl font-bold mb-2" style={{ color: "var(--text-primary)" }}>⭐ Nâng cấp tài khoản</h1>
        <p className="text-sm" style={{ color: "var(--text-secondary)" }}>Truy cập không giới hạn tất cả tính năng</p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "1.5rem" }}>
        {plans.map((p) => (
          <div key={p.slug} className="p-6 rounded-2xl text-center relative" style={{
            background: p.is_popular ? "linear-gradient(135deg, rgba(99,102,241,.06), rgba(139,92,246,.06))" : "var(--bg-surface)",
            border: p.is_popular ? "2px solid #6366f1" : "1px solid var(--border-default)",
          }}>
            {p.is_popular && <span className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full text-xs font-bold text-white" style={{ background: "#6366f1" }}>Phổ biến</span>}
            <h3 className="text-lg font-bold mb-1" style={{ color: "var(--text-primary)" }}>{p.name}</h3>
            <p className="text-sm mb-4" style={{ color: "var(--text-tertiary)" }}>{p.duration_label}</p>
            <div className="text-3xl font-extrabold mb-4" style={{ color: "#6366f1" }}>{p.price_label}</div>
            <ul className="space-y-2 mb-6 text-left">
              {p.features?.map((f, i) => (
                <li key={i} className="flex items-start gap-2 text-sm" style={{ color: "var(--text-secondary)" }}>
                  <span style={{ color: "#10b981" }}>✓</span> {f}
                </li>
              ))}
            </ul>
            <Link href={`/payment/checkout/${p.slug}`} className="block w-full py-3 rounded-xl font-bold text-center no-underline text-white" style={{ background: p.is_popular ? "#6366f1" : "var(--text-secondary)" }}>Chọn gói</Link>
          </div>
        ))}
        {!plans.length && <p className="col-span-full text-center py-8" style={{ color: "var(--text-tertiary)" }}>Chưa có gói nào.</p>}
      </div>
    </div>
  );
}
