"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Row, Col, Card, Statistic, Typography, Table, Tag, Space, Spin, Alert, Button, Select, Progress,
} from "antd";
import {
  ReloadOutlined, TeamOutlined, TrophyOutlined, BarChartOutlined,
  RiseOutlined, CheckCircleOutlined, FireOutlined, BookOutlined,
} from "@ant-design/icons";
import { adminGet } from "@/lib/admin-api";

const { Title, Text } = Typography;

// ── Types ──────────────────────────────────────────────────

interface ScoreDistribution {
  excellent: number;
  good: number;
  average: number;
  weak: number;
  fail: number;
}

interface QuizTypeStat {
  type: string;
  label: string;
  attempts: number;
  avg_score: number;
}

interface StudentRanking {
  id: number;
  username: string;
  email: string;
  total_attempts: number;
  avg_score: number;
  last_active: string | null;
}

interface RecentResult {
  id: number;
  username: string;
  quiz_type: string;
  quiz_id: string;
  score: number;
  correct: number;
  total: number;
  completed_at: string;
}

interface DailyTrend {
  date: string;
  attempts: number;
  avg_score: number;
}

interface AssignmentStat {
  id: number;
  title: string;
  quiz_type: string;
  quiz_id: string;
  teacher_name: string;
  assigned_count: number;
  completed_count: number;
  created_at: string;
}

interface DashboardData {
  total_students: number;
  total_attempts: number;
  avg_score: number;
  completion_rate: number;
  attempts_today: number;
  attempts_week: number;
  score_distribution: ScoreDistribution;
  by_quiz_type: QuizTypeStat[];
  daily_trend: DailyTrend[];
  student_rankings: StudentRanking[];
  recent_results: RecentResult[];
  assignment_stats: AssignmentStat[];
}

// ── Score colors ──────────────────────────────────────────

const SCORE_COLORS = {
  excellent: { color: "#10b981", label: "Xuất sắc (9-10)" },
  good: { color: "#3b82f6", label: "Tốt (7-8.9)" },
  average: { color: "#f59e0b", label: "Trung bình (5-6.9)" },
  weak: { color: "#f97316", label: "Yếu (3-4.9)" },
  fail: { color: "#ef4444", label: "Kém (0-2.9)" },
};

const QUIZ_TYPE_COLORS: Record<string, string> = {
  grammar: "#6366f1",
  bunpou: "#ec4899",
  vocab: "#10b981",
  "phrasal-verbs": "#f59e0b",
  usage: "#3b82f6",
  collocations: "#8b5cf6",
  exam: "#06b6d4",
  kanji: "#ef4444",
  dictation: "#14b8a6",
};

function scoreTag(score: number) {
  if (score >= 9) return <Tag color="success">{score}</Tag>;
  if (score >= 7) return <Tag color="processing">{score}</Tag>;
  if (score >= 5) return <Tag color="warning">{score}</Tag>;
  return <Tag color="error">{score}</Tag>;
}

function timeAgo(dateStr: string | null): string {
  if (!dateStr) return "—";
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m trước`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h trước`;
  const days = Math.floor(hours / 24);
  return `${days}d trước`;
}

// ── Component ─────────────────────────────────────────────

export default function TeacherDashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [typeFilter, setTypeFilter] = useState<string>("");

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const stats = await adminGet<DashboardData>("/teacher-dashboard/stats");
      setData(stats);
      setError(null);
    } catch {
      setError("Không thể tải dữ liệu dashboard. Hãy đảm bảo bạn có quyền staff.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (loading && !data) {
    return (
      <div style={{ display: "flex", justifyContent: "center", padding: 100 }}>
        <Spin size="large" tip="Đang tải dữ liệu..." />
      </div>
    );
  }

  if (!data) {
    return <Alert message={error || "Không có dữ liệu"} type="error" showIcon />;
  }

  const filteredResults = typeFilter
    ? data.recent_results.filter((r) => r.quiz_type === typeFilter)
    : data.recent_results;

  // Score distribution total for donut
  const distTotal =
    data.score_distribution.excellent +
    data.score_distribution.good +
    data.score_distribution.average +
    data.score_distribution.weak +
    data.score_distribution.fail || 1;

  // Bar chart max
  const maxAttempts = Math.max(...data.by_quiz_type.map((t) => t.attempts), 1);

  return (
    <div>
      {/* Header */}
      <Row justify="space-between" align="middle" style={{ marginBottom: 24 }}>
        <Col>
          <Title level={3} style={{ margin: 0 }}>
            📊 Teacher Dashboard
          </Title>
          <Text type="secondary" style={{ fontSize: 13 }}>
            Tổng quan kết quả học tập của học sinh
          </Text>
        </Col>
        <Col>
          <Button type="primary" icon={<ReloadOutlined />} onClick={fetchData} loading={loading}>
            Làm mới
          </Button>
        </Col>
      </Row>

      {error && <Alert message={error} type="warning" showIcon closable style={{ marginBottom: 20 }} />}

      {/* ── KPI Cards ── */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {[
          { title: "Tổng học sinh", value: data.total_students, icon: <TeamOutlined />, color: "#6366f1", extra: `📅 Hôm nay: ${data.attempts_today} lần làm bài` },
          { title: "Tổng lần làm bài", value: data.total_attempts, icon: <BarChartOutlined />, color: "#10b981", extra: `📆 7 ngày: ${data.attempts_week}` },
          { title: "Điểm trung bình", value: data.avg_score, icon: <TrophyOutlined />, color: "#f59e0b", suffix: "/10" },
          { title: "Hoàn thành bài tập", value: data.completion_rate, icon: <CheckCircleOutlined />, color: "#3b82f6", suffix: "%" },
        ].map((kpi, i) => (
          <Col xs={24} sm={12} lg={6} key={i}>
            <Card
              style={{ background: `linear-gradient(135deg, ${kpi.color}18, ${kpi.color}08)`, border: `1px solid ${kpi.color}25` }}
              styles={{ body: { padding: 20 } }}
            >
              <Statistic
                title={<Text style={{ fontSize: 12, fontWeight: 600 }}>{kpi.title}</Text>}
                value={kpi.value}
                prefix={<span style={{ color: kpi.color }}>{kpi.icon}</span>}
                suffix={kpi.suffix}
                valueStyle={{ color: kpi.color, fontWeight: 800 }}
              />
              {kpi.extra && <Text type="secondary" style={{ fontSize: 12 }}>{kpi.extra}</Text>}
            </Card>
          </Col>
        ))}
      </Row>

      {/* ── Charts Row ── */}
      <Row gutter={[20, 20]} style={{ marginBottom: 24 }}>
        {/* Score Distribution Donut */}
        <Col xs={24} lg={8}>
          <Card title={<><FireOutlined style={{ color: "#f59e0b" }} /> Phân bố điểm số</>}>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
              <svg width={180} height={180} viewBox="0 0 180 180">
                {(() => {
                  const r = 70, cx = 90, cy = 90, strokeW = 16;
                  const circumference = 2 * Math.PI * r;
                  const entries = Object.entries(data.score_distribution) as [keyof ScoreDistribution, number][];
                  let offset = 0;
                  return entries.map(([key, val]) => {
                    const len = (val / distTotal) * circumference;
                    const el = (
                      <circle
                        key={key}
                        cx={cx} cy={cy} r={r}
                        fill="none"
                        stroke={SCORE_COLORS[key].color}
                        strokeWidth={strokeW}
                        strokeDasharray={`${len} ${circumference - len}`}
                        strokeDashoffset={-offset}
                        strokeLinecap="round"
                        transform={`rotate(-90 ${cx} ${cy})`}
                        style={{ transition: "stroke-dasharray 0.6s ease" }}
                      />
                    );
                    offset += len;
                    return el;
                  });
                })()}
                <text x={90} y={85} textAnchor="middle" style={{ fontSize: 24, fontWeight: 800, fill: "currentColor" }}>
                  {distTotal}
                </text>
                <text x={90} y={102} textAnchor="middle" style={{ fontSize: 10, fontWeight: 600, fill: "#94a3b8" }}>
                  lần làm bài
                </text>
              </svg>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "6px 16px", justifyContent: "center", marginTop: 12 }}>
                {Object.entries(SCORE_COLORS).map(([key, { color, label }]) => (
                  <div key={key} style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11 }}>
                    <div style={{ width: 10, height: 10, borderRadius: 3, background: color }} />
                    <Text type="secondary" style={{ fontSize: 11 }}>
                      {label}: <strong>{data.score_distribution[key as keyof ScoreDistribution]}</strong>
                    </Text>
                  </div>
                ))}
              </div>
            </div>
          </Card>
        </Col>

        {/* Performance by Quiz Type */}
        <Col xs={24} lg={16}>
          <Card title={<><BookOutlined style={{ color: "#6366f1" }} /> Hiệu suất theo loại bài</>}>
            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              {data.by_quiz_type.map((qt) => {
                const color = QUIZ_TYPE_COLORS[qt.type] || "#64748b";
                const barWidth = (qt.attempts / maxAttempts) * 100;
                return (
                  <div key={qt.type}>
                    <Row justify="space-between" align="middle" style={{ marginBottom: 4 }}>
                      <Space>
                        <div style={{ width: 10, height: 10, borderRadius: 3, background: color }} />
                        <Text strong style={{ fontSize: 13 }}>{qt.label}</Text>
                        <Tag style={{ borderRadius: 4 }}>{qt.attempts} lần</Tag>
                      </Space>
                      <Space>
                        <Text strong style={{ color, fontSize: 14 }}>
                          {qt.avg_score}/10
                        </Text>
                      </Space>
                    </Row>
                    <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                      <div style={{ flex: 1, height: 10, borderRadius: 5, overflow: "hidden", background: "rgba(148,163,184,0.08)" }}>
                        <div
                          style={{
                            width: `${barWidth}%`,
                            height: "100%",
                            background: `linear-gradient(90deg, ${color}cc, ${color})`,
                            borderRadius: 5,
                            transition: "width 0.6s ease",
                            minWidth: 4,
                          }}
                        />
                      </div>
                      <Progress
                        type="circle"
                        percent={Math.round(qt.avg_score * 10)}
                        size={32}
                        strokeColor={color}
                        format={() => <span style={{ fontSize: 9, fontWeight: 700 }}>{qt.avg_score}</span>}
                      />
                    </div>
                  </div>
                );
              })}
              {data.by_quiz_type.length === 0 && (
                <Text type="secondary" style={{ textAlign: "center", padding: 20 }}>Chưa có dữ liệu</Text>
              )}
            </div>
          </Card>
        </Col>
      </Row>

      {/* ── Daily Trend ── */}
      <Card title={<><RiseOutlined style={{ color: "#10b981" }} /> Xu hướng 14 ngày</>} style={{ marginBottom: 24 }}>
        <div style={{ display: "flex", alignItems: "flex-end", gap: 4, height: 80, padding: "0 4px" }}>
          {data.daily_trend.map((d, i) => {
            const maxAtt = Math.max(...data.daily_trend.map((x) => x.attempts), 1);
            const h = (d.attempts / maxAtt) * 60 + 4;
            const color = d.avg_score >= 7 ? "#10b981" : d.avg_score >= 5 ? "#f59e0b" : "#ef4444";
            return (
              <div
                key={i}
                title={`${d.date}: ${d.attempts} lần, TB: ${d.avg_score}`}
                style={{
                  flex: 1,
                  height: h,
                  background: `linear-gradient(180deg, ${color}, ${color}88)`,
                  borderRadius: "4px 4px 0 0",
                  transition: "height 0.4s ease",
                  cursor: "pointer",
                  position: "relative",
                }}
              >
                <span
                  style={{
                    position: "absolute",
                    bottom: "100%",
                    left: "50%",
                    transform: "translateX(-50%)",
                    fontSize: 9,
                    fontWeight: 700,
                    color,
                    whiteSpace: "nowrap",
                    display: i % 2 === 0 ? "block" : "none",
                  }}
                >
                  {d.attempts}
                </span>
              </div>
            );
          })}
        </div>
        <div style={{ display: "flex", gap: 4, padding: "4px 4px 0" }}>
          {data.daily_trend.map((d, i) => (
            <div key={i} style={{ flex: 1, textAlign: "center", fontSize: 9, color: "#94a3b8" }}>
              {i % 2 === 0 ? new Date(d.date).toLocaleDateString("vi-VN", { day: "2-digit", month: "2-digit" }) : ""}
            </div>
          ))}
        </div>
      </Card>

      {/* ── Tables Row ── */}
      <Row gutter={[20, 20]} style={{ marginBottom: 24 }}>
        {/* Student Rankings */}
        <Col xs={24} lg={12}>
          <Card
            title={<Space><span>🏆 Bảng xếp hạng học sinh</span><Tag color="processing">{data.student_rankings.length} học sinh</Tag></Space>}
            styles={{ body: { padding: 0 } }}
          >
            <Table
              dataSource={data.student_rankings}
              rowKey="id"
              pagination={{ pageSize: 10, size: "small" }}
              size="small"
              locale={{ emptyText: "Chưa có dữ liệu" }}
              columns={[
                {
                  title: "#",
                  key: "rank",
                  width: 50,
                  render: (_, __, i) => {
                    const medals = ["🥇", "🥈", "🥉"];
                    return i < 3 ? <span style={{ fontSize: 16 }}>{medals[i]}</span> : <Text type="secondary">{i + 1}</Text>;
                  },
                },
                {
                  title: "Học sinh",
                  key: "student",
                  render: (_, r: StudentRanking) => (
                    <div>
                      <Text strong style={{ fontSize: 13 }}>{r.username}</Text>
                      <br />
                      <Text type="secondary" style={{ fontSize: 11 }}>{r.email}</Text>
                    </div>
                  ),
                },
                {
                  title: "Lần làm",
                  dataIndex: "total_attempts",
                  key: "attempts",
                  sorter: (a: StudentRanking, b: StudentRanking) => a.total_attempts - b.total_attempts,
                  render: (v: number) => <Text strong>{v}</Text>,
                },
                {
                  title: "TB",
                  dataIndex: "avg_score",
                  key: "score",
                  sorter: (a: StudentRanking, b: StudentRanking) => a.avg_score - b.avg_score,
                  defaultSortOrder: "descend" as const,
                  render: (v: number) => scoreTag(v),
                },
                {
                  title: "Hoạt động",
                  key: "active",
                  render: (_, r: StudentRanking) => (
                    <Text type="secondary" style={{ fontSize: 11 }}>{timeAgo(r.last_active)}</Text>
                  ),
                },
              ]}
            />
          </Card>
        </Col>

        {/* Recent Results */}
        <Col xs={24} lg={12}>
          <Card
            title={
              <Row justify="space-between" align="middle" style={{ width: "100%" }}>
                <Space><span>📝 Kết quả gần đây</span></Space>
                <Select
                  placeholder="Lọc loại bài"
                  allowClear
                  size="small"
                  style={{ width: 150 }}
                  value={typeFilter || undefined}
                  onChange={(v) => setTypeFilter(v || "")}
                  options={data.by_quiz_type.map((t) => ({ value: t.type, label: t.label }))}
                />
              </Row>
            }
            styles={{ body: { padding: 0 } }}
          >
            <Table
              dataSource={filteredResults}
              rowKey="id"
              pagination={{ pageSize: 10, size: "small" }}
              size="small"
              locale={{ emptyText: "Chưa có kết quả" }}
              columns={[
                {
                  title: "Học sinh",
                  dataIndex: "username",
                  key: "user",
                  render: (v: string) => <Text strong style={{ fontSize: 12 }}>{v}</Text>,
                },
                {
                  title: "Loại",
                  dataIndex: "quiz_type",
                  key: "type",
                  render: (v: string) => (
                    <Tag color={QUIZ_TYPE_COLORS[v] ? undefined : "default"} style={{ borderRadius: 4, color: QUIZ_TYPE_COLORS[v] }}>
                      {v}
                    </Tag>
                  ),
                },
                {
                  title: "Bài",
                  dataIndex: "quiz_id",
                  key: "quiz",
                  ellipsis: true,
                  render: (v: string) => <Text style={{ fontSize: 11 }}>{v}</Text>,
                },
                {
                  title: "Kết quả",
                  key: "result",
                  render: (_, r: RecentResult) => (
                    <Space size={4}>
                      {scoreTag(r.score)}
                      <Text type="secondary" style={{ fontSize: 11 }}>({r.correct}/{r.total})</Text>
                    </Space>
                  ),
                },
                {
                  title: "Thời gian",
                  key: "time",
                  render: (_, r: RecentResult) => (
                    <Text type="secondary" style={{ fontSize: 11 }}>{timeAgo(r.completed_at)}</Text>
                  ),
                },
              ]}
            />
          </Card>
        </Col>
      </Row>

      {/* ── Assignments ── */}
      {data.assignment_stats.length > 0 && (
        <Card
          title={<Space><span>📋 Theo dõi bài tập đã giao</span><Tag color="processing">{data.assignment_stats.length} bài tập</Tag></Space>}
          style={{ marginBottom: 24 }}
          styles={{ body: { padding: 0 } }}
        >
          <Table
            dataSource={data.assignment_stats}
            rowKey="id"
            pagination={false}
            size="small"
            columns={[
              {
                title: "Bài tập",
                key: "title",
                render: (_, a: AssignmentStat) => (
                  <div>
                    <Text strong style={{ fontSize: 13 }}>{a.title}</Text>
                    <br />
                    <Text type="secondary" style={{ fontSize: 11 }}>{a.quiz_type} / {a.quiz_id}</Text>
                  </div>
                ),
              },
              {
                title: "Giáo viên",
                dataIndex: "teacher_name",
                key: "teacher",
                render: (v: string) => <Text style={{ fontSize: 12 }}>{v}</Text>,
              },
              {
                title: "Đã giao",
                dataIndex: "assigned_count",
                key: "assigned",
                render: (v: number) => <Text strong>{v}</Text>,
              },
              {
                title: "Hoàn thành",
                key: "progress",
                render: (_, a: AssignmentStat) => {
                  const pct = a.assigned_count > 0 ? Math.round((a.completed_count / a.assigned_count) * 100) : 0;
                  return (
                    <Space>
                      <Progress
                        type="circle"
                        percent={pct}
                        size={36}
                        strokeColor={pct >= 80 ? "#10b981" : pct >= 50 ? "#f59e0b" : "#ef4444"}
                        format={() => <span style={{ fontSize: 10, fontWeight: 700 }}>{pct}%</span>}
                      />
                      <Text type="secondary" style={{ fontSize: 11 }}>{a.completed_count}/{a.assigned_count}</Text>
                    </Space>
                  );
                },
              },
              {
                title: "Ngày tạo",
                key: "date",
                render: (_, a: AssignmentStat) => (
                  <Text type="secondary" style={{ fontSize: 11 }}>
                    {new Date(a.created_at).toLocaleDateString("vi-VN")}
                  </Text>
                ),
              },
            ]}
          />
        </Card>
      )}
    </div>
  );
}
