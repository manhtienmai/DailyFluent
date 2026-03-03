"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";

interface PaymentStatus { status: string; plan_name: string; amount: string; qr_code_url?: string; bank_info?: { bank_name: string; account_number: string; account_name: string; }; }

export default function PaymentStatusPage() {
  const params = useParams();
  const paymentId = params.paymentId as string;
  const [data, setData] = useState<PaymentStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const poll = () => {
      fetch(`/api/v1/payment/${paymentId}/status`, { credentials: "include" })
        .then((r) => (r.ok ? r.json() : Promise.reject()))
        .then((d: PaymentStatus) => { setData(d); setLoading(false); })
        .catch(() => setLoading(false));
    };
    poll();
    const interval = setInterval(poll, 5000);
    return () => clearInterval(interval);
  }, [paymentId]);

  if (loading) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Đang tải...</div>;
  if (!data) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Không tìm thấy.</div>;

  const statusColors: Record<string, string> = { pending: "#f59e0b", completed: "#10b981", failed: "#ef4444" };
  const statusLabels: Record<string, string> = { pending: "Đang chờ thanh toán", completed: "Thành công", failed: "Thất bại" };

  return (
    <div style={{ maxWidth: 500, margin: "0 auto", padding: "2rem 1rem" }}>
      <div className="p-6 rounded-2xl text-center" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
        <div className="text-4xl mb-4">{data.status === "completed" ? "✅" : data.status === "failed" ? "❌" : "⏳"}</div>
        <h1 className="text-xl font-bold mb-2" style={{ color: "var(--text-primary)" }}>{statusLabels[data.status] || data.status}</h1>
        <p className="text-sm mb-4" style={{ color: "var(--text-secondary)" }}>{data.plan_name} — {data.amount}</p>
        <div className="inline-block px-4 py-1.5 rounded-full text-sm font-bold" style={{ background: `${statusColors[data.status]}20`, color: statusColors[data.status] }}>{statusLabels[data.status]}</div>

        {data.qr_code_url && data.status === "pending" && (
          <div className="mt-6">
            <img src={data.qr_code_url} alt="QR Code" className="mx-auto w-48 h-48 rounded-xl" />
          </div>
        )}

        {data.bank_info && data.status === "pending" && (
          <div className="mt-6 p-4 rounded-xl text-left text-sm" style={{ background: "var(--bg-interactive)" }}>
            <p className="font-semibold mb-2" style={{ color: "var(--text-primary)" }}>Thông tin chuyển khoản:</p>
            <p style={{ color: "var(--text-secondary)" }}>Ngân hàng: {data.bank_info.bank_name}</p>
            <p style={{ color: "var(--text-secondary)" }}>STK: {data.bank_info.account_number}</p>
            <p style={{ color: "var(--text-secondary)" }}>Chủ TK: {data.bank_info.account_name}</p>
          </div>
        )}

        <div className="mt-6">
          <Link href="/payment" className="text-sm font-semibold no-underline" style={{ color: "#6366f1" }}>← Quay lại gói dịch vụ</Link>
        </div>
      </div>
    </div>
  );
}
