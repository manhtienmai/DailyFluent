"use client";

import { useState, useEffect, useCallback } from "react";
import { Table, Tag, Button, Select, Typography, Space, Popconfirm } from "antd";
import { DeleteOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import { adminGet, adminPut, adminDelete } from "@/lib/admin-api";
import InlineEditCell from "@/components/admin/InlineEditCell";

const { Title, Text } = Typography;

interface FeedbackItem {
  id: number; title: string; type: string;
  status: string; user: string; total_votes: number; created_at: string;
}

const STATUS_OPTIONS = ["new", "planned", "in_progress", "done"];
const STATUS_COLORS: Record<string, string> = {
  new: "blue", planned: "purple", in_progress: "orange", done: "green",
};
const TYPE_COLORS: Record<string, string> = {
  bug: "red", feature: "blue", improvement: "orange",
};

export default function FeedbackPage() {
  const [items, setItems] = useState<FeedbackItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("all");

  const fetchData = useCallback(() => {
    setLoading(true);
    adminGet<{ items: FeedbackItem[] }>(`/crud/feedback/?status=${statusFilter}`)
      .then((d) => setItems(d.items || []))
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, [statusFilter]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const updateStatus = async (id: number, status: string) => {
    await adminPut(`/crud/feedback/${id}/`, { status });
    fetchData();
  };

  const remove = async (id: number) => {
    await adminDelete(`/crud/feedback/${id}/`);
    fetchData();
  };

  const columns: ColumnsType<FeedbackItem> = [
    { title: "ID", dataIndex: "id", width: 60, render: (id) => <Text type="secondary" style={{ fontSize: 12 }}>{id}</Text> },
    {
      title: "Tiêu đề", dataIndex: "title",
      render: (_, f) => (
        <InlineEditCell
          value={f.title}
          style={{ fontWeight: 600 }}
          onSave={async (v) => { await adminPut(`/crud/feedback/${f.id}/`, { status: f.status, title: v }); fetchData(); }}
        />
      ),
    },
    {
      title: "Loại", dataIndex: "type", width: 100,
      render: (type) => <Tag color={TYPE_COLORS[type] || "default"}>{type}</Tag>,
    },
    {
      title: "Trạng thái", dataIndex: "status", width: 140,
      render: (status, f) => (
        <Select
          value={status}
          onChange={(v) => updateStatus(f.id, v)}
          size="small"
          style={{ width: 130 }}
          options={STATUS_OPTIONS.map((s) => ({ label: s.replace("_", " "), value: s }))}
        />
      ),
    },
    { title: "User", dataIndex: "user", width: 120, render: (u) => <Text style={{ fontSize: 12 }}>{u}</Text> },
    { title: "Votes", dataIndex: "total_votes", width: 80, render: (v) => <Text strong>👍 {v}</Text> },
    { title: "Ngày", dataIndex: "created_at", width: 110, render: (d) => <Text style={{ fontSize: 12 }}>{d ? new Date(d).toLocaleDateString("vi-VN") : "—"}</Text> },
    {
      title: "", key: "actions", width: 60, align: "center",
      render: (_, f) => (
        <Popconfirm title="Xoá feedback này?" onConfirm={() => remove(f.id)} okText="Xoá" cancelText="Huỷ" okButtonProps={{ danger: true }}>
          <Button type="text" danger size="small" icon={<DeleteOutlined />} />
        </Popconfirm>
      ),
    },
  ];

  return (
    <div>
      <Space orientation="vertical" size="large" style={{ width: "100%" }}>
        <div>
          <Title level={3} style={{ margin: 0 }}>💬 Feedback</Title>
          <Text type="secondary">Phản hồi từ người dùng</Text>
        </div>

        <Space wrap>
          {["all", ...STATUS_OPTIONS].map((s) => (
            <Button
              key={s}
              type={statusFilter === s ? "primary" : "default"}
              size="small"
              onClick={() => setStatusFilter(s)}
            >
              {s === "all" ? "Tất cả" : s.replace("_", " ")}
            </Button>
          ))}
        </Space>

        <Table<FeedbackItem>
          columns={columns}
          dataSource={items}
          rowKey="id"
          loading={loading}
          size="middle"
          pagination={{ pageSize: 50, showSizeChanger: false }}
        />
      </Space>
    </div>
  );
}
