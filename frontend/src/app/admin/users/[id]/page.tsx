"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  Card,
  Table,
  Tag,
  Typography,
  Space,
  Spin,
  Statistic,
  Progress,
  Empty,
  Button,
  Tooltip,
} from "antd";
import {
  ArrowLeftOutlined,
  ClockCircleOutlined,
  FireOutlined,
  BookOutlined,
  TrophyOutlined,
  CalendarOutlined,
  CheckCircleFilled,
} from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import { adminGet } from "@/lib/admin-api";

const { Title, Text } = Typography;

// ── Types ─────────────────────────────────────
interface LearningHistory {
  user: {
    id: number;
    username: string;
    email: string;
    first_name: string;
    last_name: string;
    date_joined: string;
  };
  overview: {
    total_minutes: number;
    total_days_active: number;
    current_streak: number;
    longest_streak: number;
    total_words_mastered: number;
    total_exams_taken: number;
  };
  en10_vocab_topics: {
    topic_id: string;
    title: string;
    title_vi: string;
    emoji: string;
    total_words: number;
    words_mastered: number;
  }[];
  en10_grammar_topics: {
    topic_id: string;
    title: string;
    title_vi: string;
    emoji: string;
    total_exercises: number;
  }[];
  exam_attempts: {
    id: number;
    template_title: string;
    book_title: string;
    level: string;
    correct_count: number;
    total_questions: number;
    score_percent: number;
    started_at: string;
    submitted_at: string | null;
    duration_minutes: number | null;
  }[];
  vocab_set_progress: {
    set_title: string;
    collection_name: string;
    status: string;
    words_learned: number;
    words_total: number;
    quiz_best_score: number;
  }[];
  daily_activity: {
    date: string;
    minutes_studied: number;
    lessons_completed: number;
    points_earned: number;
  }[];
}

// ── Helpers ───────────────────────────────────

function formatMinutes(mins: number): string {
  if (mins < 60) return `${mins} phút`;
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  return m > 0 ? `${h}h ${m}m` : `${h} giờ`;
}

function scoreColor(pct: number): string {
  if (pct >= 80) return "#22c55e";
  if (pct >= 60) return "#f59e0b";
  return "#ef4444";
}

function statusTag(status: string) {
  const map: Record<string, { color: string; label: string }> = {
    completed: { color: "green", label: "Hoàn thành" },
    in_progress: { color: "blue", label: "Đang học" },
    not_started: { color: "default", label: "Chưa bắt đầu" },
  };
  const s = map[status] || { color: "default", label: status };
  return <Tag color={s.color}>{s.label}</Tag>;
}

// ── Stat Card ─────────────────────────────────

function StatCard({
  icon,
  color,
  bg,
  title,
  value,
  suffix,
}: {
  icon: React.ReactNode;
  color: string;
  bg: string;
  title: string;
  value: string | number;
  suffix?: string;
}) {
  return (
    <div style={{
      background: "#fff",
      borderRadius: 16,
      padding: "20px 18px",
      border: "1px solid #f0f0f0",
      transition: "all 0.3s",
      cursor: "default",
    }}
    className="admin-stat-card"
    >
      <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
        <div style={{
          width: 44, height: 44, borderRadius: 12,
          background: bg,
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: 20, color,
          flexShrink: 0,
        }}>
          {icon}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 12, color: "#94a3b8", fontWeight: 600, marginBottom: 2 }}>{title}</div>
          <div style={{ fontSize: 22, fontWeight: 900, color: "#1e293b", lineHeight: 1.2 }}>
            {value}
            {suffix && <span style={{ fontSize: 13, fontWeight: 600, color: "#94a3b8", marginLeft: 4 }}>{suffix}</span>}
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Bar chart (premium CSS) ──────────────────

function StudyChart({ data }: { data: { date: string; minutes_studied: number }[] }) {
  const [period, setPeriod] = useState<"today" | "7d" | "30d">("30d");

  if (!data.length) return <Empty description="Chưa có dữ liệu" />;

  const today = new Date().toISOString().split("T")[0];
  const filtered = period === "today"
    ? data.filter(d => d.date === today)
    : period === "7d"
      ? data.slice(-7)
      : data.slice(-30);

  const maxVal = Math.max(...filtered.map((d) => d.minutes_studied), 1);

  const periodLabel = period === "today" ? "Hôm nay" : period === "7d" ? "7 ngày" : "30 ngày";

  return (
    <div style={{ padding: "12px 0" }}>
      <div style={{ display: "flex", gap: 6, marginBottom: 12 }}>
        {(["today", "7d", "30d"] as const).map(p => (
          <button
            key={p}
            onClick={() => setPeriod(p)}
            style={{
              padding: "4px 14px", borderRadius: 8, border: "1px solid",
              borderColor: period === p ? "#6366f1" : "#e2e8f0",
              background: period === p ? "rgba(99,102,241,0.08)" : "transparent",
              color: period === p ? "#6366f1" : "#64748b",
              fontSize: 12, fontWeight: 700, cursor: "pointer",
              transition: "all 0.2s",
            }}
          >
            {p === "today" ? "Hôm nay" : p === "7d" ? "7 ngày" : "30 ngày"}
          </button>
        ))}
      </div>
      <div style={{
        display: "flex",
        alignItems: "flex-end",
        gap: 3,
        height: 140,
        padding: "0 4px",
        position: "relative",
      }}>
        {/* Grid lines */}
        {[0.25, 0.5, 0.75, 1].map(pct => (
          <div key={pct} style={{
            position: "absolute", left: 0, right: 0,
            bottom: `${pct * 100}%`,
            borderBottom: "1px dashed rgba(0,0,0,0.06)",
            pointerEvents: "none",
          }} />
        ))}
        {filtered.map((d, i) => {
          const h = Math.max((d.minutes_studied / maxVal) * 100, 3);
          const isActive = d.minutes_studied > 0;
          return (
            <Tooltip
              key={i}
              title={`${new Date(d.date).toLocaleDateString("vi-VN")}: ${d.minutes_studied} phút`}
            >
              <div
                style={{
                  flex: 1,
                  height: `${h}%`,
                  background: isActive
                    ? "linear-gradient(180deg, #6366f1 0%, #a5b4fc 100%)"
                    : "rgba(0,0,0,0.04)",
                  borderRadius: "4px 4px 0 0",
                  minWidth: 8,
                  transition: "all 0.3s cubic-bezier(0.4,0,0.2,1)",
                  cursor: "pointer",
                  position: "relative",
                }}
                onMouseEnter={(e) => {
                  if (isActive) (e.currentTarget.style.transform = "scaleY(1.08)");
                  (e.currentTarget.style.opacity = "0.85");
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget.style.transform = "scaleY(1)");
                  (e.currentTarget.style.opacity = "1");
                }}
              />
            </Tooltip>
          );
        })}
      </div>
      <div style={{
        display: "flex", justifyContent: "space-between",
        marginTop: 8, padding: "0 4px",
      }}>
        <Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>
          {filtered.length > 0 && new Date(filtered[0].date).toLocaleDateString("vi-VN")}
        </Text>
        <Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>
          {filtered.length > 0 && new Date(filtered[filtered.length - 1].date).toLocaleDateString("vi-VN")}
        </Text>
      </div>
    </div>
  );
}

// ── Page ──────────────────────────────────────

export default function UserDetailPage() {
  const params = useParams();
  const router = useRouter();
  const userId = params?.id;

  const [data, setData] = useState<LearningHistory | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!userId) return;
    setLoading(true);
    adminGet<LearningHistory>(`/users/${userId}/learning-history/`)
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [userId]);

  if (loading) {
    return (
      <div style={{ textAlign: "center", padding: 80 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!data) {
    return (
      <div style={{ textAlign: "center", padding: 80 }}>
        <Empty description="Không tìm thấy user" />
        <Button onClick={() => router.push("/admin/users")} style={{ marginTop: 16 }}>
          ← Quay lại
        </Button>
      </div>
    );
  }

  const { user, overview } = data;
  const totalStudyMinutes = data.daily_activity.reduce((s, d) => s + d.minutes_studied, 0);

  // ── Exam columns ────────────────────────────
  const examCols: ColumnsType<LearningHistory["exam_attempts"][0]> = [
    {
      title: "Đề thi",
      key: "title",
      render: (_, r) => (
        <div>
          <Text strong>{r.template_title}</Text>
          {r.book_title && (
            <div>
              <Text type="secondary" style={{ fontSize: 12 }}>{r.book_title}</Text>
            </div>
          )}
        </div>
      ),
    },
    {
      title: "Level",
      dataIndex: "level",
      width: 90,
      render: (v) => <Tag>{v}</Tag>,
    },
    {
      title: "Kết quả",
      key: "result",
      width: 140,
      render: (_, r) => (
        <Space orientation="vertical" size={0}>
          <Text strong style={{ color: scoreColor(r.score_percent) }}>
            {r.correct_count}/{r.total_questions} ({r.score_percent}%)
          </Text>
          <Progress
            percent={r.score_percent}
            size="small"
            showInfo={false}
            strokeColor={scoreColor(r.score_percent)}
          />
        </Space>
      ),
    },
    {
      title: "Thời gian",
      dataIndex: "duration_minutes",
      width: 100,
      render: (v) => v != null ? `${v} phút` : "—",
    },
    {
      title: "Ngày làm",
      dataIndex: "started_at",
      width: 120,
      render: (v) => new Date(v).toLocaleDateString("vi-VN"),
    },
  ];

  // ── Vocab topics columns ────────────────────
  const vocabTopicCols: ColumnsType<LearningHistory["en10_vocab_topics"][0]> = [
    {
      title: "Chủ đề",
      key: "topic",
      render: (_, r) => (
        <Space>
          <span style={{ fontSize: 18 }}>{r.emoji}</span>
          <div>
            <Text strong>{r.title}</Text>
            <div><Text type="secondary" style={{ fontSize: 12 }}>{r.title_vi}</Text></div>
          </div>
        </Space>
      ),
    },
    {
      title: "Tiến độ",
      key: "progress",
      width: 200,
      render: (_, r) => {
        const pct = r.total_words > 0 ? Math.round((r.words_mastered / r.total_words) * 100) : 0;
        return (
          <Space orientation="vertical" size={0} style={{ width: "100%" }}>
            <Text style={{ fontSize: 12 }}>
              {r.words_mastered}/{r.total_words} từ
              {pct === 100 && <CheckCircleFilled style={{ color: "#22c55e", marginLeft: 6 }} />}
            </Text>
            <Progress percent={pct} size="small" showInfo={false} strokeColor="#6366f1" />
          </Space>
        );
      },
    },
  ];

  // ── Vocab set columns ──────────────────────
  const vocabSetCols: ColumnsType<LearningHistory["vocab_set_progress"][0]> = [
    {
      title: "Bộ từ",
      key: "set",
      render: (_, r) => (
        <div>
          <Text strong>{r.set_title}</Text>
          {r.collection_name && (
            <div><Text type="secondary" style={{ fontSize: 12 }}>{r.collection_name}</Text></div>
          )}
        </div>
      ),
    },
    {
      title: "Trạng thái",
      dataIndex: "status",
      width: 130,
      render: (v) => statusTag(v),
    },
    {
      title: "Từ đã học",
      key: "words",
      width: 140,
      render: (_, r) => {
        const pct = r.words_total > 0 ? Math.round((r.words_learned / r.words_total) * 100) : 0;
        return (
          <Space orientation="vertical" size={0}>
            <Text style={{ fontSize: 12 }}>{r.words_learned}/{r.words_total}</Text>
            <Progress percent={pct} size="small" showInfo={false} strokeColor="#10b981" />
          </Space>
        );
      },
    },
    {
      title: "Quiz cao nhất",
      dataIndex: "quiz_best_score",
      width: 120,
      align: "center" as const,
      render: (v: number) => (
        <Text strong style={{ color: scoreColor(v) }}>
          {v}%
        </Text>
      ),
    },
  ];

  return (
    <div>
      <Space orientation="vertical" size="large" style={{ width: "100%" }}>
        {/* ── Header ── */}
        <div style={{
          display: "flex", alignItems: "center", gap: 16,
          padding: "16px 20px", borderRadius: 16,
          background: "linear-gradient(135deg, #f8fafc, #f1f5f9)",
          border: "1px solid #e2e8f0",
        }}>
          <Button
            icon={<ArrowLeftOutlined />}
            onClick={() => router.push("/admin/users")}
            style={{ borderRadius: 10 }}
          />
          <div>
            <Title level={3} style={{ margin: 0 }}>
              📊 {user.username}
            </Title>
            <Space>
              <Text type="secondary" style={{ fontSize: 13 }}>{user.email}</Text>
              <Text type="secondary">·</Text>
              <Text type="secondary" style={{ fontSize: 13 }}>
                Tham gia {new Date(user.date_joined).toLocaleDateString("vi-VN")}
              </Text>
            </Space>
          </div>
        </div>

        {/* ── Overview Stats ── */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 12 }}>
          <StatCard
            icon={<ClockCircleOutlined />}
            color="#6366f1" bg="rgba(99,102,241,0.1)"
            title="Tổng thời gian học"
            value={formatMinutes(overview.total_minutes || totalStudyMinutes)}
          />
          <StatCard
            icon={<CalendarOutlined />}
            color="#10b981" bg="rgba(16,185,129,0.1)"
            title="Số ngày hoạt động"
            value={overview.total_days_active} suffix="ngày"
          />
          <StatCard
            icon={<FireOutlined />}
            color="#f59e0b" bg="rgba(245,158,11,0.1)"
            title="Streak hiện tại"
            value={overview.current_streak}
            suffix={`ngày (kỷ lục: ${overview.longest_streak})`}
          />
          <StatCard
            icon={<BookOutlined />}
            color="#8b5cf6" bg="rgba(139,92,246,0.1)"
            title="Từ vựng đã thuộc"
            value={overview.total_words_mastered} suffix="từ"
          />
          <StatCard
            icon={<TrophyOutlined />}
            color="#ef4444" bg="rgba(239,68,68,0.1)"
            title="Bài thi đã làm"
            value={overview.total_exams_taken} suffix="bài"
          />
        </div>

        {/* ── Study Time Chart ── */}
        <Card
          title={<span style={{ fontWeight: 800 }}>⏱️ Thời gian học (30 ngày gần nhất)</span>}
          size="small"
          style={{ borderRadius: 16, border: "1px solid #e2e8f0" }}
        >
          <StudyChart data={data.daily_activity} />
        </Card>

        {/* ── EN10 Vocab Topics ── */}
        {data.en10_vocab_topics.filter(t => t.words_mastered > 0).length > 0 && (
          <Card
            title={<span style={{ fontWeight: 800 }}>📚 Tiếng Anh 9 lên 10</span>}
            size="small"
            style={{ borderRadius: 16, border: "1px solid #e2e8f0" }}
          >
            <Table
              columns={vocabTopicCols}
              dataSource={data.en10_vocab_topics.filter(t => t.words_mastered > 0)}
              rowKey="topic_id"
              size="small"
              pagination={false}
            />
          </Card>
        )}

        {/* ── EN10 Grammar Topics ── */}
        {data.en10_grammar_topics.length > 0 && (
          <Card
            title={<span style={{ fontWeight: 800 }}>📝 Ngữ pháp Tiếng Anh 10</span>}
            size="small"
            style={{ borderRadius: 16, border: "1px solid #e2e8f0" }}
          >
            <Table
              columns={[
                {
                  title: "Chủ đề",
                  key: "topic",
                  render: (_: unknown, r: LearningHistory["en10_grammar_topics"][0]) => (
                    <Space>
                      <span style={{ fontSize: 18 }}>{r.emoji}</span>
                      <div>
                        <Text strong>{r.title}</Text>
                        <div><Text type="secondary" style={{ fontSize: 12 }}>{r.title_vi}</Text></div>
                      </div>
                    </Space>
                  ),
                },
                {
                  title: "Số bài tập",
                  dataIndex: "total_exercises",
                  width: 120,
                  align: "center" as const,
                },
              ]}
              dataSource={data.en10_grammar_topics}
              rowKey="topic_id"
              size="small"
              pagination={false}
            />
          </Card>
        )}

        {/* ── Exam History ── */}
        <Card
          title={<span style={{ fontWeight: 800 }}>📋 Lịch sử làm bài thi</span>}
          size="small"
          style={{ borderRadius: 16, border: "1px solid #e2e8f0" }}
        >
          {data.exam_attempts.length > 0 ? (
            <Table
              columns={examCols}
              dataSource={data.exam_attempts}
              rowKey="id"
              size="small"
              pagination={{ pageSize: 10, showSizeChanger: false }}
            />
          ) : (
            <Empty description="Chưa làm bài thi nào" />
          )}
        </Card>

        {/* ── Vocab Set Progress ── */}
        {data.vocab_set_progress.length > 0 && (
          <Card
            title={<span style={{ fontWeight: 800 }}>📦 Tiến độ bộ từ vựng</span>}
            size="small"
            style={{ borderRadius: 16, border: "1px solid #e2e8f0" }}
          >
            <Table
              columns={vocabSetCols}
              dataSource={data.vocab_set_progress}
              rowKey={(r) => `${r.set_title}-${r.collection_name}`}
              size="small"
              pagination={{ pageSize: 10, showSizeChanger: false }}
            />
          </Card>
        )}
      </Space>

      <style jsx global>{`
        .admin-stat-card:hover {
          border-color: #e2e8f0 !important;
          box-shadow: 0 4px 16px rgba(0,0,0,0.06) !important;
          transform: translateY(-2px);
        }
      `}</style>
    </div>
  );
}
