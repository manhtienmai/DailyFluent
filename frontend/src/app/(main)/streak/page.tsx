"use client";

import { useState, useEffect } from "react";

interface LeaderboardUser {
  rank: number;
  username: string;
  current_streak: number;
  longest_streak: number;
}

export default function StreakLeaderboardPage() {
  const [leaderboard, setLeaderboard] = useState<LeaderboardUser[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/v1/streak/leaderboard", { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d) => { setLeaderboard(Array.isArray(d) ? d : []); setLoading(false); })
      .catch(() => { setLeaderboard([]); setLoading(false); });
  }, []);

  // No is_me flag from API; skip "my stats" card

  const rankColors: Record<number, string> = { 1: "#EAB308", 2: "#94A3B8", 3: "#B45309" };

  return (
    <div style={{ padding: "24px", minHeight: "100vh" }}>
      <div className="max-w-[800px] mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-2xl font-extrabold mb-2" style={{ color: "var(--text-primary)" }}>🏆 Bảng Xếp Hạng Tuần Này</h1>
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
            Tính từ thứ 2 đến hôm nay
          </p>
        </div>



        {/* Leaderboard table */}
        {loading ? (
          <div className="text-center py-16" style={{ color: "var(--text-tertiary)" }}>Đang tải...</div>
        ) : leaderboard.length > 0 ? (
          <div className="rounded-2xl overflow-hidden" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", boxShadow: "0 1px 3px rgba(0,0,0,.04)" }}>
            {/* Header row */}
            <div className="flex items-center px-6 py-3" style={{ background: "var(--bg-app-subtle)", borderBottom: "1px solid var(--border-default)" }}>
              <div className="w-10 text-center text-xs font-semibold uppercase" style={{ color: "var(--text-secondary)" }}>#</div>
              <div className="flex-1 ml-4 text-xs font-semibold uppercase" style={{ color: "var(--text-secondary)" }}>Thành viên</div>
              <div className="w-24 text-right text-xs font-semibold uppercase" style={{ color: "var(--text-secondary)" }}>Streak</div>
              <div className="w-24 text-right text-xs font-semibold uppercase" style={{ color: "var(--text-secondary)" }}>Kỷ lục</div>
            </div>

            {leaderboard.map((u, i) => (
              <div key={u.rank} className="flex items-center px-6 py-3 transition-colors relative" style={{
                borderBottom: i < leaderboard.length - 1 ? "1px solid var(--border-subtle)" : "none",
                background: "transparent",
              }}>
                <div className="w-10 text-center text-lg font-bold" style={{ color: rankColors[i + 1] || "var(--text-tertiary)" }}>
                  {i + 1}
                </div>
                <div className="flex-1 ml-4 flex items-center gap-3 min-w-0">
                  <div className="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0" style={{ background: "#E2E8F0", color: "#64748B", border: "1px solid var(--border-default)" }}>
                    {u.username.charAt(0).toUpperCase()}
                  </div>
                  <div className="min-w-0 overflow-hidden">
                    <div className="font-semibold truncate" style={{ color: "var(--text-primary)" }}>
                      {u.username}
                    </div>
                    {u.current_streak > 0 && <div className="text-xs" style={{ color: "var(--text-tertiary)" }}>🔥 {u.current_streak} ngày streak</div>}
                  </div>
                </div>
                <div className="w-24 text-right">
                  <div className="font-bold" style={{ color: "var(--action-primary)" }}>🔥 {u.current_streak}</div>
                  <div className="text-xs" style={{ color: "var(--text-tertiary)" }}>ngày</div>
                </div>
                <div className="w-24 text-right">
                  <div className="font-bold" style={{ color: "var(--text-primary)" }}>{u.longest_streak}</div>
                  <div className="text-xs" style={{ color: "var(--text-tertiary)" }}>ngày</div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-16" style={{ color: "var(--text-secondary)" }}>
            <div className="text-5xl mb-4">🏆</div>
            <p>Chưa có dữ liệu xếp hạng tuần này. Hãy bắt đầu học ngay!</p>
          </div>
        )}
      </div>
    </div>
  );
}
