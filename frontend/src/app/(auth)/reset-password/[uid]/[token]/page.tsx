"use client";

import { useState, type FormEvent } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";

export default function ResetPasswordPage() {
  const params = useParams();
  const router = useRouter();
  const uid = params.uid as string;
  const token = params.token as string;

  const [pw1, setPw1] = useState("");
  const [pw2, setPw2] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (pw1 !== pw2) { setError("Mật khẩu xác nhận không khớp."); return; }
    if (pw1.length < 8) { setError("Mật khẩu phải có ít nhất 8 ký tự."); return; }
    setLoading(true);
    setError("");
    try {
      const r = await fetch("/api/v1/auth/reset-password/", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ uid, token, new_password1: pw1, new_password2: pw2 }),
      });
      if (r.ok) {
        setSuccess(true);
        setTimeout(() => router.push("/login"), 3000);
      } else {
        const d = await r.json();
        setError(d.error || "Link không hợp lệ hoặc đã hết hạn.");
      }
    } catch { setError("Lỗi kết nối."); }
    setLoading(false);
  };

  if (success) return (
    <div style={{ maxWidth: 480, margin: "0 auto", padding: "4rem 1rem", textAlign: "center" }}>
      <div className="text-5xl mb-4">✅</div>
      <h1 className="text-xl font-bold mb-3" style={{ color: "var(--text-primary)" }}>Đặt lại mật khẩu thành công!</h1>
      <p className="text-sm" style={{ color: "var(--text-secondary)" }}>Đang chuyển đến trang đăng nhập...</p>
    </div>
  );

  return (
    <div style={{ maxWidth: 480, margin: "0 auto", padding: "4rem 1rem" }}>
      <div className="text-center mb-8">
        <h1 className="text-2xl font-bold mb-2" style={{ color: "var(--text-primary)" }}>Đặt lại mật khẩu</h1>
        <p className="text-sm" style={{ color: "var(--text-secondary)" }}>Nhập mật khẩu mới cho tài khoản của bạn</p>
      </div>

      <div className="p-6 rounded-2xl" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
        {error && <div className="p-3 rounded-xl text-sm mb-4" style={{ background: "rgba(254,226,226,.7)", color: "#dc2626" }}>{error}</div>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-semibold mb-1" style={{ color: "var(--text-primary)" }}>Mật khẩu mới</label>
            <input type="password" value={pw1} onChange={(e) => setPw1(e.target.value)} required minLength={8} className="w-full p-3 rounded-xl text-sm border" style={{ background: "var(--bg-interactive)", borderColor: "var(--border-default)", color: "var(--text-primary)" }} />
          </div>
          <div>
            <label className="block text-sm font-semibold mb-1" style={{ color: "var(--text-primary)" }}>Xác nhận mật khẩu</label>
            <input type="password" value={pw2} onChange={(e) => setPw2(e.target.value)} required className="w-full p-3 rounded-xl text-sm border" style={{ background: "var(--bg-interactive)", borderColor: "var(--border-default)", color: "var(--text-primary)" }} />
          </div>
          <button type="submit" disabled={loading} className="w-full py-3 rounded-xl font-bold text-white" style={{ background: "#6366f1", opacity: loading ? 0.6 : 1, border: "none", cursor: "pointer" }}>
            {loading ? "Đang xử lý..." : "Đặt lại mật khẩu"}
          </button>
        </form>
        <div className="text-center mt-4">
          <Link href="/login" className="text-sm no-underline" style={{ color: "var(--text-tertiary)" }}>← Quay lại đăng nhập</Link>
        </div>
      </div>
    </div>
  );
}
