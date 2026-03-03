"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";

function VerifyEmailContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const key = searchParams.get("key");

  const [status, setStatus] = useState<"verifying" | "success" | "error">(key ? "verifying" : "error");

  useEffect(() => {
    if (!key) return;
    fetch("/api/v1/auth/verify-email/", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ key }),
    })
      .then((r) => { setStatus(r.ok ? "success" : "error"); if (r.ok) setTimeout(() => router.push("/login"), 3000); })
      .catch(() => setStatus("error"));
  }, [key, router]);

  return (
    <div style={{ maxWidth: 480, margin: "0 auto", padding: "4rem 1rem", textAlign: "center" }}>
      {status === "verifying" && (
        <>
          <div className="text-5xl mb-4">⏳</div>
          <h1 className="text-xl font-bold mb-3" style={{ color: "var(--text-primary)" }}>Đang xác thực...</h1>
        </>
      )}
      {status === "success" && (
        <>
          <div className="text-5xl mb-4">✅</div>
          <h1 className="text-xl font-bold mb-3" style={{ color: "var(--text-primary)" }}>Email đã xác thực!</h1>
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>Đang chuyển đến trang đăng nhập...</p>
        </>
      )}
      {status === "error" && (
        <>
          <div className="text-5xl mb-4">❌</div>
          <h1 className="text-xl font-bold mb-3" style={{ color: "var(--text-primary)" }}>Link không hợp lệ</h1>
          <p className="text-sm mb-4" style={{ color: "var(--text-secondary)" }}>Link xác thực đã hết hạn hoặc không hợp lệ.</p>
          <Link href="/login" className="text-sm font-semibold no-underline" style={{ color: "#6366f1" }}>← Quay lại đăng nhập</Link>
        </>
      )}
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={<div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Đang tải...</div>}>
      <VerifyEmailContent />
    </Suspense>
  );
}
