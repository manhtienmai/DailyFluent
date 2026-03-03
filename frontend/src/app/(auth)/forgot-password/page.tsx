"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const r = await fetch("/api/v1/auth/forgot-password/", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      if (r.ok) setSent(true);
      else setError("Có lỗi xảy ra, vui lòng thử lại.");
    } catch { setError("Lỗi kết nối."); }
    setLoading(false);
  };

  if (sent) return (
    <div style={{ maxWidth: 480, margin: "0 auto", padding: "4rem 1rem", textAlign: "center" }}>
      <div className="text-5xl mb-4">📧</div>
      <h1 className="text-xl font-bold mb-3" style={{ color: "var(--text-primary)" }}>Kiểm tra email của bạn</h1>
      <p className="text-sm mb-6" style={{ color: "var(--text-secondary)" }}>Chúng tôi đã gửi hướng dẫn đặt lại mật khẩu đến <b>{email}</b>.</p>
      <Link href="/login" className="text-sm font-semibold no-underline" style={{ color: "#6366f1" }}>← Quay lại đăng nhập</Link>
    </div>
  );

  return (
    <div style={{ maxWidth: 480, margin: "0 auto", padding: "4rem 1rem" }}>
      <div className="text-center mb-8">
        <h1 className="text-2xl font-bold mb-2" style={{ color: "var(--text-primary)" }}>Quên mật khẩu?</h1>
        <p className="text-sm" style={{ color: "var(--text-secondary)" }}>Nhập email để nhận link đặt lại mật khẩu</p>
      </div>

      <div className="p-6 rounded-2xl" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
        {error && <div className="p-3 rounded-xl text-sm mb-4" style={{ background: "rgba(254,226,226,.7)", color: "#dc2626" }}>{error}</div>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-semibold mb-1" style={{ color: "var(--text-primary)" }}>Email</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required placeholder="email@example.com" className="w-full p-3 rounded-xl text-sm border" style={{ background: "var(--bg-interactive)", borderColor: "var(--border-default)", color: "var(--text-primary)" }} />
          </div>
          <button type="submit" disabled={loading} className="w-full py-3 rounded-xl font-bold text-white" style={{ background: "#6366f1", opacity: loading ? 0.6 : 1, border: "none", cursor: "pointer" }}>
            {loading ? "Đang gửi..." : "Gửi link đặt lại"}
          </button>
        </form>
        <div className="text-center mt-4">
          <Link href="/login" className="text-sm no-underline" style={{ color: "var(--text-tertiary)" }}>← Quay lại đăng nhập</Link>
        </div>
      </div>
    </div>
  );
}
