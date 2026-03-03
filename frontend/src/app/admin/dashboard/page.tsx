"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Row, Col, Card, Statistic, Typography, Button, Alert, Table, Tabs, Tag, Space, Spin, Badge, Avatar,
} from "antd";
import {
  ReloadOutlined, TeamOutlined, EyeOutlined, UserAddOutlined, TrophyOutlined,
  LoginOutlined, ScheduleOutlined, RiseOutlined, GlobalOutlined, BarChartOutlined,
  ThunderboltOutlined, RobotOutlined, BookOutlined, FormOutlined, CommentOutlined,
  AppstoreOutlined,
} from "@ant-design/icons";
import Link from "next/link";
import { adminGet, type AdminStats } from "@/lib/admin-api";

const { Title, Text } = Typography;

/* ── Fallback data ──────────────────────────────────────── */

const FALLBACK_STATS: AdminStats = {
  today_visitors: 0, today_views: 0, users_today: 0, total_users: 0,
  active_now: 0, peak_hour: "", user_growth: 0, users_month: 0,
  users_week: 0, users_yesterday: 0, today_users: 0, total_views: 0,
  total_views_week: 0, total_views_month: 0,
  hourly_labels: [], hourly_data: [], user_labels: [], user_data: [],
  views_labels: [], views_data: [], recent_users: [],
  top_pages_today: [], top_pages_week: [],
  gemini_tokens_today: 0, gemini_tokens_month: 0,
  gemini_calls_today: 0, gemini_calls_month: 0,
  gemini_input_today: 0, gemini_input_month: 0,
  gemini_output_today: 0, gemini_output_month: 0,
  gemini_by_model: [],
};

/* ── Quick Links ───────────────────────────────────────── */

const QUICK_LINKS = [
  { label: "Thêm từ vựng", href: "/admin/vocab/bulk-add", icon: <ThunderboltOutlined />, color: "#6366F1" },
  { label: "Import JP", href: "/admin/vocab/import-jp", icon: "🇯🇵", color: "#EC4899" },
  { label: "Quiz Generator", href: "/admin/vocab/quiz-generate", icon: "🎯", color: "#10B981" },
  { label: "Import TOEIC", href: "/admin/exam/import-toeic", icon: "📤", color: "#F59E0B" },
  { label: "Choukai Tool", href: "/admin/vocab/choukai-tool", icon: "🎧", color: "#06B6D4" },
  { label: "Kanji Import", href: "/admin/kanji", icon: "漢", color: "#E11D48" },
];

/* ── Component ─────────────────────────────────────────── */

export default function DashboardPage() {
  const [stats, setStats] = useState<AdminStats>(FALLBACK_STATS);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"today" | "week">("today");

  const fetchStats = useCallback(async () => {
    setLoading(true);
    try {
      const data = await adminGet<AdminStats>("/dashboard/stats/");
      setStats(data);
      setError(null);
    } catch {
      setError("Chưa có API dashboard. Đang hiển thị giao diện mẫu.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchStats(); }, [fetchStats]);

  const now = new Date();
  const dateStr = now.toLocaleString("vi-VN", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });

  return (
    <div>
      {/* ── Header ── */}
      <Row justify="space-between" align="middle" style={{ marginBottom: 24 }}>
        <Col>
          <Title level={3} style={{ margin: 0 }}>📊 Dashboard</Title>
          <Space size="small" style={{ marginTop: 4 }}>
            <Text type="secondary" style={{ fontSize: 13 }}>Cập nhật: <strong>{dateStr}</strong></Text>
            {stats.active_now > 0 && <Tag color="success" style={{ borderRadius: 20 }}>🟢 {stats.active_now} online</Tag>}
          </Space>
        </Col>
        <Col>
          <Button type="primary" icon={<ReloadOutlined />} onClick={fetchStats} loading={loading}>
            Làm mới
          </Button>
        </Col>
      </Row>

      {error && <Alert message={error} type="warning" showIcon closable style={{ marginBottom: 20 }} />}

      {/* ── KPI Cards ── */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {[
          { title: "Khách truy cập hôm nay", value: stats.today_visitors, icon: <TeamOutlined />, color: "#6366F1", extra: stats.active_now > 0 ? `🟢 ${stats.active_now} đang online` : undefined },
          { title: "Lượt xem hôm nay", value: stats.today_views, icon: <EyeOutlined />, color: "#10B981", extra: `📅 7 ngày: ${stats.total_views_week.toLocaleString()}` },
          { title: "Đăng ký hôm nay", value: stats.users_today, icon: <UserAddOutlined />, color: "#F59E0B", extra: stats.user_growth > 0 ? `↑ +${stats.user_growth} vs hôm qua` : stats.user_growth < 0 ? `↓ ${stats.user_growth}` : "= so với hôm qua" },
          { title: "Tổng người dùng", value: stats.total_users, icon: <TrophyOutlined />, color: "#EC4899", extra: `📆 30 ngày: +${stats.users_month.toLocaleString()}` },
        ].map((kpi, i) => (
          <Col xs={24} sm={12} lg={6} key={i}>
            <Card
              style={{ background: `linear-gradient(135deg, ${kpi.color}18, ${kpi.color}08)`, border: `1px solid ${kpi.color}25` }}
              styles={{ body: { padding: "20px" } }}
            >
              <Statistic
                title={<Text style={{ fontSize: 12, fontWeight: 600 }}>{kpi.title}</Text>}
                value={loading ? "—" : kpi.value}
                prefix={<span style={{ color: kpi.color }}>{kpi.icon}</span>}
                valueStyle={{ color: kpi.color, fontWeight: 800 }}
              />
              {kpi.extra && <Text type="secondary" style={{ fontSize: 12 }}>{kpi.extra}</Text>}
            </Card>
          </Col>
        ))}
      </Row>

      {/* ── Mini Stats ── */}
      <Row gutter={[12, 12]} style={{ marginBottom: 28 }}>
        {[
          { icon: <LoginOutlined />, value: stats.today_users, label: "User đăng nhập", color: "#6366F1" },
          { icon: <ScheduleOutlined />, value: stats.users_yesterday, label: "Đăng ký hôm qua", color: "#10B981" },
          { icon: <RiseOutlined />, value: stats.users_week, label: "User mới 7 ngày", color: "#F59E0B" },
          { icon: <GlobalOutlined />, value: stats.total_views_week, label: "Lượt xem 7 ngày", color: "#06B6D4" },
          { icon: <BarChartOutlined />, value: stats.total_views_month, label: "Lượt xem 30 ngày", color: "#8B5CF6" },
          { icon: <EyeOutlined />, value: stats.total_views, label: "Tổng lượt xem", color: "#EC4899" },
        ].map((item, i) => (
          <Col xs={12} sm={8} lg={4} key={i}>
            <Card size="small" styles={{ body: { padding: 16 } }}>
              <div style={{ color: item.color, fontSize: 20, marginBottom: 8 }}>{item.icon}</div>
              <Statistic value={loading ? "—" : item.value} valueStyle={{ fontSize: 22, fontWeight: 800 }} />
              <Text type="secondary" style={{ fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: 0.5 }}>
                {item.label}
              </Text>
            </Card>
          </Col>
        ))}
      </Row>

      {/* ── Quick Links ── */}
      <div style={{ marginBottom: 28 }}>
        <Title level={5} style={{ marginBottom: 12 }}>⚡ Truy cập nhanh</Title>
        <Row gutter={[12, 12]}>
          {QUICK_LINKS.map((link) => (
            <Col xs={12} sm={8} lg={4} key={link.href}>
              <Link href={link.href} style={{ textDecoration: "none" }}>
                <Card
                  hoverable
                  size="small"
                  styles={{ body: { padding: 16, display: "flex", alignItems: "center", gap: 12 } }}
                >
                  <span style={{ fontSize: 22, width: 40, height: 40, borderRadius: 10, background: `${link.color}15`, display: "flex", alignItems: "center", justifyContent: "center" }}>
                    {link.icon}
                  </span>
                  <Text strong style={{ fontSize: 13 }}>{link.label}</Text>
                </Card>
              </Link>
            </Col>
          ))}
        </Row>
      </div>

      {/* ── Gemini AI Usage ── */}
      <div style={{ marginBottom: 28 }}>
        <Title level={5} style={{ marginBottom: 14 }}>🤖 Gemini AI Token Usage</Title>

        <Card style={{ marginBottom: 16 }}>
          <Row gutter={[24, 16]}>
            {/* Donut chart */}
            <Col xs={24} md={8}>
              {(() => {
                const totalMonth = stats.gemini_tokens_month;
                const inputMonth = stats.gemini_input_month;
                const outputMonth = stats.gemini_output_month;
                const thinkingMonth = Math.max(0, totalMonth - inputMonth - outputMonth);
                const total3 = inputMonth + outputMonth + thinkingMonth || 1;
                const r = 68, cx = 88, cy = 88, stroke = 14;
                const circumference = 2 * Math.PI * r;
                const gap = 4;
                const inputLen = (circumference - gap * 3) * (inputMonth / total3);
                const outputLen = (circumference - gap * 3) * (outputMonth / total3);
                const thinkingLen = (circumference - gap * 3) * (thinkingMonth / total3);

                return (
                  <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                    <svg width={176} height={176} viewBox="0 0 176 176">
                      <defs>
                        <linearGradient id="inputGrad" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stopColor="#06b6d4" /><stop offset="100%" stopColor="#0891b2" /></linearGradient>
                        <linearGradient id="outputGrad" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stopColor="#14b8a6" /><stop offset="100%" stopColor="#10b981" /></linearGradient>
                        <linearGradient id="thinkGrad" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stopColor="#f59e0b" /><stop offset="100%" stopColor="#f97316" /></linearGradient>
                      </defs>
                      <circle cx={cx} cy={cy} r={r} fill="none" stroke="rgba(148,163,184,0.1)" strokeWidth={stroke} />
                      <circle cx={cx} cy={cy} r={r} fill="none" stroke="url(#inputGrad)" strokeWidth={stroke}
                        strokeDasharray={`${inputLen} ${circumference - inputLen}`}
                        strokeLinecap="round" transform={`rotate(-90 ${cx} ${cy})`}
                        style={{ transition: "stroke-dasharray 0.6s ease" }} />
                      <circle cx={cx} cy={cy} r={r} fill="none" stroke="url(#outputGrad)" strokeWidth={stroke}
                        strokeDasharray={`${outputLen} ${circumference - outputLen}`}
                        strokeDashoffset={-(inputLen + gap)}
                        strokeLinecap="round" transform={`rotate(-90 ${cx} ${cy})`}
                        style={{ transition: "stroke-dasharray 0.6s ease" }} />
                      {thinkingMonth > 0 && (
                        <circle cx={cx} cy={cy} r={r} fill="none" stroke="url(#thinkGrad)" strokeWidth={stroke}
                          strokeDasharray={`${thinkingLen} ${circumference - thinkingLen}`}
                          strokeDashoffset={-(inputLen + outputLen + gap * 2)}
                          strokeLinecap="round" transform={`rotate(-90 ${cx} ${cy})`}
                          style={{ transition: "stroke-dasharray 0.6s ease" }} />
                      )}
                      <text x={cx} y={cy - 6} textAnchor="middle" style={{ fontSize: 22, fontWeight: 800, fill: "currentColor" }}>
                        {loading ? "—" : (totalMonth >= 1000 ? `${(totalMonth / 1000).toFixed(1)}K` : totalMonth.toLocaleString())}
                      </text>
                      <text x={cx} y={cy + 12} textAnchor="middle" style={{ fontSize: 9, fontWeight: 700, fill: "#94a3b8", textTransform: "uppercase" as const, letterSpacing: 1.2 }}>
                        Total 30 ngày
                      </text>
                    </svg>
                    <Space style={{ marginTop: 6 }}>
                      <Badge color="#06b6d4" text={<Text type="secondary" style={{ fontSize: 11 }}>Input</Text>} />
                      <Badge color="#14b8a6" text={<Text type="secondary" style={{ fontSize: 11 }}>Output</Text>} />
                      {thinkingMonth > 0 && <Badge color="#f59e0b" text={<Text type="secondary" style={{ fontSize: 11 }}>Thinking</Text>} />}
                    </Space>
                  </div>
                );
              })()}
            </Col>

            {/* Stats grid */}
            <Col xs={24} md={16}>
              <Row gutter={[8, 8]}>
                {[
                  { label: "Input hôm nay", value: stats.gemini_input_today, color: "#06b6d4" },
                  { label: "Output hôm nay", value: stats.gemini_output_today, color: "#14b8a6" },
                  { label: "Input 30 ngày", value: stats.gemini_input_month, color: "#0891b2" },
                  { label: "Output 30 ngày", value: stats.gemini_output_month, color: "#10b981" },
                  { label: "Calls hôm nay", value: stats.gemini_calls_today, color: "#0ea5e9" },
                  { label: "Calls 30 ngày", value: stats.gemini_calls_month, color: "#f59e0b" },
                ].map((item, i) => (
                  <Col span={8} key={i}>
                    <Card size="small" style={{ background: `${item.color}08`, border: `1px solid ${item.color}22` }} styles={{ body: { padding: "10px 12px" } }}>
                      <Text type="secondary" style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: 0.6 }}>{item.label}</Text>
                      <div style={{ fontSize: 20, fontWeight: 800, color: item.color, lineHeight: 1.3 }}>
                        {loading ? "—" : item.value.toLocaleString()}
                      </div>
                    </Card>
                  </Col>
                ))}
              </Row>
            </Col>
          </Row>
        </Card>

        {/* Per-model breakdown */}
        {stats.gemini_by_model.length > 0 && (
          <Card size="small" title={<Text type="secondary" style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: 0.8 }}>Token theo Model</Text>}>
            {(() => {
              const MODEL_COLORS: Record<string, [string, string]> = {
                "gemini-2.5-pro": ["#0891b2", "#06b6d4"],
                "gemini-2.5-flash": ["#10b981", "#14b8a6"],
                "gemini-2.0-flash": ["#f59e0b", "#fbbf24"],
                "gemini-1.5-pro": ["#0ea5e9", "#38bdf8"],
                "gemini-1.5-flash": ["#06b6d4", "#67e8f9"],
              };
              const maxTotal = Math.max(...stats.gemini_by_model.map(m => m.total), 1);
              return stats.gemini_by_model.map((m, i) => {
                const [c1, c2] = MODEL_COLORS[m.model] || ["#64748b", "#94a3b8"];
                const barWidth = (m.total / maxTotal) * 100;
                const inputPct = m.total > 0 ? (m.input / m.total) * 100 : 0;
                const outputPct = m.total > 0 ? (m.output / m.total) * 100 : 0;
                const thinkPct = Math.max(0, 100 - inputPct - outputPct);
                return (
                  <div key={i} style={{ marginBottom: i < stats.gemini_by_model.length - 1 ? 16 : 0 }}>
                    <Row justify="space-between" align="middle" style={{ marginBottom: 6 }}>
                      <Space>
                        <div style={{ width: 10, height: 10, borderRadius: 3, background: `linear-gradient(135deg, ${c1}, ${c2})` }} />
                        <Text strong style={{ fontSize: 13 }}>{m.model}</Text>
                        <Tag color="processing" style={{ borderRadius: 4 }}>{m.calls} calls</Tag>
                      </Space>
                      <Text strong style={{ fontSize: 14, color: c1 }}>{m.total.toLocaleString()}</Text>
                    </Row>
                    <div style={{ height: 10, borderRadius: 5, overflow: "hidden", background: "rgba(148,163,184,0.08)", display: "flex", width: `${barWidth}%`, minWidth: 24 }}>
                      <div style={{ width: `${inputPct}%`, background: `linear-gradient(90deg, #06b6d4, #0891b2)`, transition: "width 0.6s ease" }} />
                      <div style={{ width: `${outputPct}%`, background: `linear-gradient(90deg, #14b8a6, #10b981)`, transition: "width 0.6s ease" }} />
                      {thinkPct > 0 && <div style={{ width: `${thinkPct}%`, background: `linear-gradient(90deg, #f59e0b, #f97316)`, transition: "width 0.6s ease" }} />}
                    </div>
                    <Space style={{ marginTop: 5 }}>
                      <Text style={{ fontSize: 10, color: "#06b6d4", fontWeight: 600 }}>⬇ In: {m.input.toLocaleString()}</Text>
                      <Text style={{ fontSize: 10, color: "#14b8a6", fontWeight: 600 }}>⬆ Out: {m.output.toLocaleString()}</Text>
                      {m.total - m.input - m.output > 0 && <Text style={{ fontSize: 10, color: "#f59e0b", fontWeight: 600 }}>💭 Think: {(m.total - m.input - m.output).toLocaleString()}</Text>}
                    </Space>
                  </div>
                );
              });
            })()}
          </Card>
        )}
      </div>

      {/* ── Users + Pages ── */}
      <Row gutter={[20, 20]} style={{ marginBottom: 24 }}>
        {/* Recent Users */}
        <Col xs={24} lg={12}>
          <Card
            title={<Space><span>🆕 Người dùng mới nhất</span><Tag color="processing">{stats.recent_users.length} gần nhất</Tag></Space>}
            styles={{ body: { padding: 0 } }}
          >
            <Table
              dataSource={stats.recent_users}
              rowKey={(_, i) => String(i)}
              pagination={false}
              size="small"
              locale={{ emptyText: "Chưa có dữ liệu" }}
              columns={[
                {
                  title: "Người dùng",
                  key: "user",
                  render: (_, u, i) => (
                    <Space>
                      <Avatar style={{ background: ["#6366F1", "#10B981", "#F59E0B", "#EC4899", "#06B6D4"][i % 5] }} size="small">
                        {u.username.slice(0, 2).toUpperCase()}
                      </Avatar>
                      <div>
                        <Text strong style={{ fontSize: 13 }}>{u.username}</Text>
                        <br />
                        <Text type="secondary" style={{ fontSize: 11 }}>{u.email}</Text>
                      </div>
                    </Space>
                  ),
                },
                {
                  title: "Ngày đăng ký",
                  key: "date",
                  align: "right" as const,
                  render: (_, u) => <Text type="secondary" style={{ fontSize: 12 }}>{new Date(u.date_joined).toLocaleDateString("vi-VN")}</Text>,
                },
              ]}
            />
          </Card>
        </Col>

        {/* Top Pages */}
        <Col xs={24} lg={12}>
          <Card
            title="🔥 Trang phổ biến"
            styles={{ body: { padding: 0 } }}
            tabList={[
              { key: "today", tab: "Hôm nay" },
              { key: "week", tab: "Tuần này" },
            ]}
            onTabChange={(key) => setActiveTab(key as "today" | "week")}
            activeTabKey={activeTab}
          >
            <Table
              dataSource={activeTab === "today" ? stats.top_pages_today : stats.top_pages_week}
              rowKey={(_, i) => String(i)}
              pagination={false}
              size="small"
              locale={{ emptyText: "Chưa có dữ liệu" }}
              columns={[
                {
                  title: "#",
                  key: "rank",
                  width: 50,
                  render: (_, __, i) => {
                    const colors = ["#F59E0B", "#94A3B8", "#D97706"];
                    return (
                      <Avatar size="small" style={{ background: i < 3 ? colors[i] : "rgba(99,102,241,0.1)", color: i < 3 ? "#fff" : "#6366f1", fontWeight: 800, fontSize: 11 }}>
                        {i + 1}
                      </Avatar>
                    );
                  },
                },
                { title: "Đường dẫn", key: "path", ellipsis: true, render: (_, p) => <Text code style={{ fontSize: 12 }}>{p.path}</Text> },
                { title: "Lượt xem", key: "views", align: "right" as const, render: (_, p) => <Text strong style={{ color: "#6366f1" }}>{p.views.toLocaleString()}</Text> },
              ]}
            />
          </Card>
        </Col>
      </Row>

      {/* ── Content Stats ── */}
      {(stats.total_vocab || stats.total_exams || stats.total_feedback) && (
        <div style={{ marginBottom: 24 }}>
          <Title level={5} style={{ marginBottom: 12 }}>📚 Thống kê nội dung</Title>
          <Row gutter={[12, 12]}>
            {([
              stats.total_vocab ? { icon: <BookOutlined />, value: stats.total_vocab, label: "Tổng từ vựng", color: "#6366F1" } : null,
              stats.total_vocab_sets ? { icon: <AppstoreOutlined />, value: stats.total_vocab_sets, label: "Bộ từ vựng", color: "#8B5CF6" } : null,
              stats.total_exams ? { icon: <FormOutlined />, value: stats.total_exams, label: "Bài thi", color: "#10B981" } : null,
              stats.total_feedback ? { icon: <CommentOutlined />, value: stats.total_feedback, label: "Feedback", color: "#F59E0B" } : null,
            ] as ({ icon: React.ReactNode; value: number; label: string; color: string } | null)[]).filter((x): x is { icon: React.ReactNode; value: number; label: string; color: string } => x !== null).map((item, i) => (
              <Col xs={12} sm={6} key={i}>
                <Card size="small" styles={{ body: { padding: 16 } }}>
                  <div style={{ color: item.color, fontSize: 20, marginBottom: 8 }}>{item.icon}</div>
                  <Statistic value={item.value} valueStyle={{ fontSize: 22, fontWeight: 800 }} />
                  <Text type="secondary" style={{ fontSize: 11, fontWeight: 600, textTransform: "uppercase" }}>{item.label}</Text>
                </Card>
              </Col>
            ))}
          </Row>
        </div>
      )}
    </div>
  );
}
