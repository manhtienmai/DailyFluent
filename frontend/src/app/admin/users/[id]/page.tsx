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
  if (pct >= 80) return "#52c41a";
  if (pct >= 60) return "#faad14";
  return "#ff4d4f";
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

// ── Bar chart (pure CSS) ──────────────────────

function MiniBarChart({ data }: { data: { date: string; minutes_studied: number }[] }) {
  if (!data.length) return <Empty description="Chưa có dữ liệu" />;

  const maxVal = Math.max(...data.map((d) => d.minutes_studied), 1);
  const last30 = data.slice(-30);

  return (
    <div style={{ padding: "8px 0" }}>
      <div
        style={{
          display: "flex",
          alignItems: "flex-end",
          gap: 2,
          height: 120,
          padding: "0 4px",
        }}
      >
        {last30.map((d, i) => {
          const h = Math.max((d.minutes_studied / maxVal) * 100, 2);
          return (
            <Tooltip
              key={i}
              title={`${new Date(d.date).toLocaleDateString("vi-VN")}: ${d.minutes_studied} phút`}
            >
              <div
                style={{
                  flex: 1,
                  height: `${h}%`,
                  background: d.minutes_studied > 0
                    ? "linear-gradient(180deg, #6366f1 0%, #818cf8 100%)"
                    : "#f0f0f0",
                  borderRadius: "3px 3px 0 0",
                  minWidth: 6,
                  transition: "height 0.3s ease",
                  cursor: "pointer",
                }}
              />
            </Tooltip>
          );
        })}
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 4 }}>
        <Text type="secondary" style={{ fontSize: 11 }}>
          {last30.length > 0 && new Date(last30[0].date).toLocaleDateString("vi-VN")}
        </Text>
        <Text type="secondary" style={{ fontSize: 11 }}>
          {last30.length > 0 && new Date(last30[last30.length - 1].date).toLocaleDateString("vi-VN")}
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
              {pct === 100 && <CheckCircleFilled style={{ color: "#52c41a", marginLeft: 6 }} />}
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
        {/* Header */}
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <Button
            icon={<ArrowLeftOutlined />}
            onClick={() => router.push("/admin/users")}
          />
          <div>
            <Title level={3} style={{ margin: 0 }}>
              📊 {user.username}
            </Title>
            <Space>
              <Text type="secondary">{user.email}</Text>
              <Text type="secondary">·</Text>
              <Text type="secondary">
                Tham gia {new Date(user.date_joined).toLocaleDateString("vi-VN")}
              </Text>
            </Space>
          </div>
        </div>

        {/* Overview Stats */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 16 }}>
          <Card size="small">
            <Statistic
              title="Tổng thời gian học"
              value={formatMinutes(overview.total_minutes)}
              prefix={<ClockCircleOutlined style={{ color: "#6366f1" }} />}
            />
          </Card>
          <Card size="small">
            <Statistic
              title="Số ngày hoạt động"
              value={overview.total_days_active}
              suffix="ngày"
              prefix={<CalendarOutlined style={{ color: "#10b981" }} />}
            />
          </Card>
          <Card size="small">
            <Statistic
              title="Streak hiện tại"
              value={overview.current_streak}
              suffix={`ngày (kỷ lục: ${overview.longest_streak})`}
              prefix={<FireOutlined style={{ color: "#f59e0b" }} />}
            />
          </Card>
          <Card size="small">
            <Statistic
              title="Từ vựng đã thuộc"
              value={overview.total_words_mastered}
              suffix="từ"
              prefix={<BookOutlined style={{ color: "#8b5cf6" }} />}
            />
          </Card>
          <Card size="small">
            <Statistic
              title="Bài thi đã làm"
              value={overview.total_exams_taken}
              suffix="bài"
              prefix={<TrophyOutlined style={{ color: "#ef4444" }} />}
            />
          </Card>
        </div>

        {/* Study Time Chart */}
        <Card title="⏱️ Thời gian học (30 ngày gần nhất)" size="small">
          <MiniBarChart data={data.daily_activity} />
        </Card>

        {/* EN10 Vocab Topics */}
        {data.en10_vocab_topics.length > 0 && (
          <Card title="📚 Từ vựng Tiếng Anh 10" size="small">
            <Table
              columns={vocabTopicCols}
              dataSource={data.en10_vocab_topics}
              rowKey="topic_id"
              size="small"
              pagination={false}
            />
          </Card>
        )}

        {/* EN10 Grammar Topics */}
        {data.en10_grammar_topics.length > 0 && (
          <Card title="📝 Ngữ pháp Tiếng Anh 10" size="small">
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

        {/* Exam History */}
        <Card title="📋 Lịch sử làm bài thi" size="small">
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

        {/* Vocab Set Progress */}
        {data.vocab_set_progress.length > 0 && (
          <Card title="📦 Tiến độ bộ từ vựng" size="small">
            <Table
              columns={vocabSetCols}
              dataSource={data.vocab_set_progress}
              rowKey={(_, i) => String(i)}
              size="small"
              pagination={{ pageSize: 10, showSizeChanger: false }}
            />
          </Card>
        )}
      </Space>
    </div>
  );
}
