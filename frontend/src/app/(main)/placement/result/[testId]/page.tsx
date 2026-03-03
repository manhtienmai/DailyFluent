"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";

interface SkillScore { skill: string; label: string; score: number; }
interface ResultData {
  estimated_score: number;
  confidence_interval: number;
  estimated_listening: number;
  estimated_reading: number;
  questions_answered: number;
  accuracy: number;
  skill_scores: SkillScore[];
}

const SKILL_LABELS: Record<string, string> = {
  L1: "Nghe - Mô tả hình ảnh", L2: "Nghe - Hỏi đáp", L3: "Nghe - Hội thoại", L4: "Nghe - Bài nói ngắn",
  R5: "Đọc - Điền câu", R6: "Đọc - Hoàn thành đoạn văn", R7: "Đọc - Đọc hiểu", VOC: "Từ vựng", GRM: "Ngữ pháp",
};

export default function PlacementResultPage() {
  const params = useParams();
  const testId = params.testId as string;
  const [result, setResult] = useState<ResultData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/placement/api/test/${testId}/`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((d: ResultData) => { setResult(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, [testId]);

  if (loading) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Đang tải...</div>;
  if (!result) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Không tìm thấy kết quả.</div>;

  return (
    <div style={{ maxWidth: 768, margin: "0 auto", padding: "2rem 1rem" }}>
      <div className="text-center mb-8">
        <div className="inline-block p-4 rounded-full mb-4" style={{ background: "linear-gradient(135deg, #34d399, #059669)" }}>
          <svg className="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
        </div>
        <h1 className="text-3xl font-bold mb-2" style={{ color: "var(--text-primary)" }}>Hoàn thành!</h1>
        <p style={{ color: "var(--text-secondary)" }}>Đây là kết quả đánh giá của bạn</p>
      </div>

      {/* Score card */}
      <div className="rounded-2xl p-8 text-white text-center mb-8" style={{ background: "linear-gradient(135deg, #6366f1, #7c3aed)", boxShadow: "0 8px 32px rgba(99,102,241,.3)" }}>
        <p className="text-sm" style={{ color: "rgba(255,255,255,.7)" }}>Điểm TOEIC ước tính</p>
        <div className="flex items-center justify-center gap-2">
          <span className="text-6xl font-bold">{result.estimated_score}</span>
          <span className="text-xl" style={{ color: "rgba(255,255,255,.6)" }}>±{result.confidence_interval}</span>
        </div>
        <div className="grid grid-cols-2 gap-8 mt-8 pt-6" style={{ borderTop: "1px solid rgba(255,255,255,.2)" }}>
          <div className="text-center"><p className="text-sm" style={{ color: "rgba(255,255,255,.7)" }}>Nghe</p><p className="text-3xl font-bold">{result.estimated_listening}</p></div>
          <div className="text-center"><p className="text-sm" style={{ color: "rgba(255,255,255,.7)" }}>Đọc</p><p className="text-3xl font-bold">{result.estimated_reading}</p></div>
        </div>
      </div>

      {/* Skill breakdown */}
      <div className="rounded-2xl p-6 mb-8" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
        <h2 className="text-lg font-bold mb-4" style={{ color: "var(--text-primary)" }}>📊 Chi tiết kỹ năng</h2>
        <div className="space-y-4">
          {result.skill_scores?.map((s) => {
            const pct = Math.min(Math.max(((s.score + 3) / 6) * 100, 5), 100);
            const color = s.score >= 1 ? "#10b981" : s.score >= 0 ? "#f59e0b" : s.score >= -1 ? "#f97316" : "#ef4444";
            const label = s.score >= 1 ? "Tốt" : s.score >= 0 ? "Trung bình" : s.score >= -1 ? "Cần cải thiện" : "Yếu";
            return (
              <div key={s.skill}>
                <div className="flex justify-between mb-1">
                  <span className="text-sm font-medium" style={{ color: "var(--text-secondary)" }}>{SKILL_LABELS[s.skill] || s.skill}</span>
                  <span className="text-sm font-medium" style={{ color }}>{label}</span>
                </div>
                <div className="h-2 rounded-full overflow-hidden" style={{ background: "var(--border-default)" }}>
                  <div className="h-full rounded-full" style={{ background: color, width: `${pct}%` }} />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 mb-8">
        <div className="text-center p-4 rounded-xl" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
          <p className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>{result.questions_answered}</p>
          <p className="text-sm" style={{ color: "var(--text-tertiary)" }}>Câu đã trả lời</p>
        </div>
        <div className="text-center p-4 rounded-xl" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
          <p className="text-2xl font-bold" style={{ color: "var(--text-primary)" }}>{result.accuracy}%</p>
          <p className="text-sm" style={{ color: "var(--text-tertiary)" }}>Độ chính xác</p>
        </div>
      </div>

      {/* CTA */}
      <div className="space-y-4">
        <Link href="/placement/goals" className="block w-full py-4 rounded-xl text-center font-bold text-white no-underline" style={{ background: "#6366f1" }}>
          Đặt mục tiêu & Tạo lộ trình học tập →
        </Link>
        <Link href="/" className="block w-full text-center py-3 no-underline" style={{ color: "var(--text-tertiary)" }}>Quay về trang chủ</Link>
      </div>
    </div>
  );
}
