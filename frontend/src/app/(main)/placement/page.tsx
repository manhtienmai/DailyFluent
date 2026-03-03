"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

interface TestInfo { id: number; questions_answered: number; }
interface ProfileInfo { estimated_score: number; }

export default function PlacementWelcomePage() {
  const [inProgress, setInProgress] = useState<TestInfo | null>(null);
  const [profile, setProfile] = useState<ProfileInfo | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/v1/placement/status", { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((d) => {
        if (d.in_progress_test) setInProgress(d.in_progress_test);
        if (d.profile) setProfile(d.profile);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  return (
    <div style={{ maxWidth: 672, margin: "0 auto", padding: "2rem 1rem" }}>
      {/* Hero */}
      <div className="rounded-2xl p-8 text-white text-center mb-8" style={{ background: "linear-gradient(135deg, #6366f1, #7c3aed)", boxShadow: "0 8px 32px rgba(99,102,241,.3)" }}>
        <div className="w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6" style={{ background: "rgba(255,255,255,.2)" }}>
          <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
          </svg>
        </div>
        <h1 className="text-3xl font-bold mb-3">Chào mừng đến DailyFluent!</h1>
        <p className="text-white/90 text-lg mb-6">Hãy làm bài kiểm tra 5-10 phút để chúng tôi hiểu trình độ của bạn.</p>
        <div className="grid grid-cols-3 gap-4 mt-6">
          {[{ icon: "📊", text: "20-40 câu hỏi adaptive" }, { icon: "🎯", text: "Điều chỉnh độ khó theo năng lực" }, { icon: "📈", text: "Kết quả ước tính điểm TOEIC" }].map((f) => (
            <div key={f.icon} className="p-4 rounded-xl text-center" style={{ background: "rgba(255,255,255,.1)" }}>
              <span className="text-2xl block mb-2">{f.icon}</span>
              <p className="text-sm">{f.text}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Actions */}
      <div className="space-y-4">
        {inProgress ? (
          <Link href="/placement/test" className="block w-full py-4 px-6 rounded-xl text-center font-bold text-white no-underline transition-all" style={{ background: "#f59e0b" }}>
            ▶ Tiếp tục bài test ({inProgress.questions_answered} câu đã trả lời)
          </Link>
        ) : (
          <Link href="/placement/test" className="block w-full py-4 px-6 rounded-xl text-center font-bold text-white no-underline transition-all" style={{ background: "#6366f1" }}>
            ⚡ Bắt đầu ngay
          </Link>
        )}

        {profile && (
          <div className="p-6 rounded-xl" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
            <h3 className="font-semibold mb-3" style={{ color: "var(--text-primary)" }}>Kết quả lần test gần nhất</h3>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-3xl font-bold" style={{ color: "#6366f1" }}>{profile.estimated_score}</p>
                <p className="text-sm" style={{ color: "var(--text-tertiary)" }}>điểm TOEIC</p>
              </div>
              <Link href="/placement/dashboard" className="font-medium text-sm flex items-center gap-1 no-underline" style={{ color: "#6366f1" }}>Xem Dashboard →</Link>
            </div>
          </div>
        )}

        <Link href="/" className="block w-full text-center py-3 no-underline" style={{ color: "var(--text-tertiary)" }}>Bỏ qua, quay về trang chủ</Link>
      </div>

      <div className="mt-12 text-center text-sm" style={{ color: "var(--text-tertiary)" }}>
        <p>Bài test sẽ tự động điều chỉnh độ khó dựa trên câu trả lời của bạn.</p>
        <p className="mt-1">Kết quả sẽ được sử dụng để tạo lộ trình học tập cá nhân hóa.</p>
      </div>
    </div>
  );
}
