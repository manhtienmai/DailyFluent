"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function PlacementGoalsPage() {
  const router = useRouter();
  const [targetScore, setTargetScore] = useState(600);
  const [daysPerWeek, setDaysPerWeek] = useState(5);
  const [minutesPerDay, setMinutesPerDay] = useState(30);
  const [saving, setSaving] = useState(false);

  const handleSubmit = async () => {
    setSaving(true);
    try {
      await fetch("/placement/api/generate-path/", {
        method: "POST", credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target_score: targetScore, days_per_week: daysPerWeek, minutes_per_day: minutesPerDay }),
      });
      router.push("/placement/dashboard");
    } catch { /* ignore */ }
    setSaving(false);
  };

  return (
    <div style={{ maxWidth: 600, margin: "0 auto", padding: "2rem 1rem" }}>
      <div className="text-center mb-8">
        <h1 className="text-2xl font-bold mb-2" style={{ color: "var(--text-primary)" }}>🎯 Đặt mục tiêu</h1>
        <p className="text-sm" style={{ color: "var(--text-secondary)" }}>Tùy chỉnh lộ trình phù hợp với bạn</p>
      </div>

      <div className="space-y-6">
        {/* Target score */}
        <div className="p-6 rounded-2xl" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
          <label className="block text-sm font-semibold mb-3" style={{ color: "var(--text-primary)" }}>Điểm TOEIC mục tiêu</label>
          <div className="flex items-center gap-4">
            <input type="range" min={300} max={990} step={5} value={targetScore} onChange={(e) => setTargetScore(Number(e.target.value))} className="flex-1" style={{ accentColor: "#6366f1" }} />
            <span className="text-2xl font-bold w-16 text-right" style={{ color: "#6366f1" }}>{targetScore}</span>
          </div>
        </div>

        {/* Days per week */}
        <div className="p-6 rounded-2xl" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
          <label className="block text-sm font-semibold mb-3" style={{ color: "var(--text-primary)" }}>Số ngày học mỗi tuần</label>
          <div className="flex gap-2">
            {[3, 4, 5, 6, 7].map((d) => (
              <button key={d} onClick={() => setDaysPerWeek(d)} className="flex-1 py-3 rounded-xl text-sm font-bold transition-all" style={{
                background: daysPerWeek === d ? "#6366f1" : "var(--bg-interactive)",
                color: daysPerWeek === d ? "white" : "var(--text-primary)",
                border: `2px solid ${daysPerWeek === d ? "#6366f1" : "var(--border-default)"}`,
                cursor: "pointer",
              }}>{d} ngày</button>
            ))}
          </div>
        </div>

        {/* Minutes per day */}
        <div className="p-6 rounded-2xl" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
          <label className="block text-sm font-semibold mb-3" style={{ color: "var(--text-primary)" }}>Thời gian học mỗi ngày</label>
          <div className="flex gap-2">
            {[15, 30, 45, 60].map((m) => (
              <button key={m} onClick={() => setMinutesPerDay(m)} className="flex-1 py-3 rounded-xl text-sm font-bold transition-all" style={{
                background: minutesPerDay === m ? "#6366f1" : "var(--bg-interactive)",
                color: minutesPerDay === m ? "white" : "var(--text-primary)",
                border: `2px solid ${minutesPerDay === m ? "#6366f1" : "var(--border-default)"}`,
                cursor: "pointer",
              }}>{m} phút</button>
            ))}
          </div>
        </div>

        <button onClick={handleSubmit} disabled={saving} className="w-full py-4 rounded-xl font-bold text-white text-center" style={{ background: "#6366f1", opacity: saving ? 0.6 : 1, border: "none", cursor: "pointer" }}>
          {saving ? "Đang tạo lộ trình..." : "Tạo lộ trình học tập →"}
        </button>
      </div>
    </div>
  );
}
