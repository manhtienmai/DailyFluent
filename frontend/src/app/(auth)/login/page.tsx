"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { loginAPI } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError("Vui lòng nhập email và mật khẩu.");
      return;
    }
    setLoading(true);
    setError("");

    const result = await loginAPI(email, password);
    if (result.success) {
      router.push("/");
    } else {
      setError(result.message || "Đăng nhập thất bại.");
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-[400px]">
      {/* Logo */}
      <div className="text-center mb-8">
        <div className="text-4xl font-extrabold mb-1" style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
          DailyFluent
        </div>
        <p className="text-sm" style={{ color: "var(--text-secondary)" }}>Chào mừng trở lại 👋</p>
      </div>

      {/* Card */}
      <div className="p-6 rounded-2xl" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)", boxShadow: "0 4px 24px rgba(0,0,0,.06)" }}>
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-xs font-semibold uppercase tracking-wide mb-1.5" style={{ color: "var(--text-secondary)" }}>Email</label>
            <input
              type="email" value={email} onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com" autoComplete="email" autoFocus
              className="w-full p-3 rounded-xl text-sm border outline-none transition-all"
              style={{ background: "var(--bg-interactive)", borderColor: "var(--border-default)", color: "var(--text-primary)" }}
            />
          </div>

          <div className="mb-5">
            <label className="block text-xs font-semibold uppercase tracking-wide mb-1.5" style={{ color: "var(--text-secondary)" }}>Mật khẩu</label>
            <input
              type="password" value={password} onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••" autoComplete="current-password"
              className="w-full p-3 rounded-xl text-sm border outline-none transition-all"
              style={{ background: "var(--bg-interactive)", borderColor: "var(--border-default)", color: "var(--text-primary)" }}
            />
          </div>

          {error && (
            <div className="mb-4 p-3 rounded-xl text-sm" style={{ background: "rgba(254,226,226,.7)", color: "#dc2626", border: "1px solid rgba(252,165,165,.5)" }}>
              {error}
            </div>
          )}

          <button
            type="submit" disabled={loading}
            className="w-full py-3 rounded-xl text-sm font-semibold text-white transition-all"
            style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6)", opacity: loading ? 0.6 : 1 }}
          >
            {loading ? "Đang đăng nhập..." : "Đăng nhập"}
          </button>
        </form>

        {/* Divider */}
        <div className="flex items-center gap-3 my-5">
          <div className="flex-1 h-px" style={{ background: "var(--border-default)" }} />
          <span className="text-[10px] uppercase" style={{ color: "var(--text-tertiary)" }}>hoặc</span>
          <div className="flex-1 h-px" style={{ background: "var(--border-default)" }} />
        </div>

        {/* Google OAuth */}
        <a
          href="/accounts/google/login/?process=login"
          className="flex items-center justify-center gap-2 w-full py-3 rounded-xl text-sm font-semibold transition-all no-underline"
          style={{ background: "var(--bg-interactive)", color: "var(--text-primary)", border: "1px solid var(--border-default)" }}
        >
          <svg className="w-4 h-4" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" />
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
          </svg>
          Đăng nhập với Google
        </a>
      </div>

      {/* Footer */}
      <p className="text-center mt-5 text-sm" style={{ color: "var(--text-secondary)" }}>
        Chưa có tài khoản?{" "}
        <Link href="/signup" className="font-semibold" style={{ color: "var(--action-primary)" }}>Đăng ký</Link>
      </p>
    </div>
  );
}
