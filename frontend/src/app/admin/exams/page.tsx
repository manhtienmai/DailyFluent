"use client";

import { useEffect, useState } from "react";
import { Table, Button, Input, Tag, Switch, message, Space } from "antd";
import { SearchOutlined, LockOutlined, UnlockOutlined } from "@ant-design/icons";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ExamItem {
  id: number;
  title: string;
  slug: string;
  description: string;
  total_questions: number;
  is_public: boolean;
  is_active: boolean;
  created_at: string | null;
}

export default function AdminExamLockPage() {
  const [exams, setExams] = useState<ExamItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedIds, setSelectedIds] = useState<number[]>([]);

  const fetchExams = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/crud/exams/english/?search=${search}`, { credentials: "include" });
      const data = await res.json();
      if (data.success) setExams(data.items);
    } catch {
      message.error("Lỗi tải danh sách đề thi");
    }
    setLoading(false);
  };

  useEffect(() => { fetchExams(); }, [search]);

  const handleToggle = async (id: number) => {
    try {
      const res = await fetch(`${API}/api/crud/exams/english/${id}/toggle-public/`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
      });
      const data = await res.json();
      if (data.success) {
        message.success(data.message);
        setExams(prev => prev.map(e => e.id === id ? { ...e, is_public: data.is_public } : e));
      }
    } catch {
      message.error("Lỗi cập nhật");
    }
  };

  const handleBulk = async (action: "public" | "lock") => {
    if (selectedIds.length === 0) return message.warning("Chọn ít nhất 1 đề");
    try {
      const res = await fetch(`${API}/api/crud/exams/english/bulk-toggle/`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ids: selectedIds, action }),
      });
      const data = await res.json();
      if (data.success) {
        message.success(data.message);
        setSelectedIds([]);
        fetchExams();
      }
    } catch {
      message.error("Lỗi cập nhật hàng loạt");
    }
  };

  const publicCount = exams.filter(e => e.is_public).length;
  const lockedCount = exams.filter(e => !e.is_public).length;

  const columns = [
    {
      title: "ID",
      dataIndex: "id",
      width: 60,
    },
    {
      title: "Tên đề thi",
      dataIndex: "title",
      render: (text: string, record: ExamItem) => (
        <div>
          <div style={{ fontWeight: 600 }}>{text}</div>
          <div style={{ fontSize: 12, color: "#888" }}>{record.slug}</div>
        </div>
      ),
    },
    {
      title: "Số câu",
      dataIndex: "total_questions",
      width: 80,
      align: "center" as const,
    },
    {
      title: "Trạng thái",
      dataIndex: "is_public",
      width: 150,
      align: "center" as const,
      render: (isPublic: boolean) => isPublic
        ? <Tag color="green" icon={<UnlockOutlined />}>Công khai</Tag>
        : <Tag color="red" icon={<LockOutlined />}>Khóa VIP</Tag>,
    },
    {
      title: "Thao tác",
      width: 120,
      align: "center" as const,
      render: (_: unknown, record: ExamItem) => (
        <Switch
          checked={record.is_public}
          onChange={() => handleToggle(record.id)}
          checkedChildren="Public"
          unCheckedChildren="Locked"
        />
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8 }}>
        🔐 Quản lý khóa đề thi
      </h1>
      <p style={{ color: "#888", marginBottom: 24 }}>
        Quản lý trạng thái công khai / khóa VIP cho các đề thi English vào Lớp 10.
      </p>

      {/* Stats */}
      <div style={{ display: "flex", gap: 16, marginBottom: 16 }}>
        <div style={{ padding: "12px 20px", borderRadius: 8, background: "#f0fdf4", border: "1px solid #bbf7d0", flex: 1 }}>
          <div style={{ fontSize: 24, fontWeight: 700, color: "#16a34a" }}>{publicCount}</div>
          <div style={{ fontSize: 13, color: "#4ade80" }}>Đề công khai</div>
        </div>
        <div style={{ padding: "12px 20px", borderRadius: 8, background: "#fef2f2", border: "1px solid #fecaca", flex: 1 }}>
          <div style={{ fontSize: 24, fontWeight: 700, color: "#dc2626" }}>{lockedCount}</div>
          <div style={{ fontSize: 13, color: "#f87171" }}>Đề khóa VIP</div>
        </div>
        <div style={{ padding: "12px 20px", borderRadius: 8, background: "#f8fafc", border: "1px solid #e2e8f0", flex: 1 }}>
          <div style={{ fontSize: 24, fontWeight: 700, color: "#475569" }}>{exams.length}</div>
          <div style={{ fontSize: 13, color: "#94a3b8" }}>Tổng số đề</div>
        </div>
      </div>

      {/* Controls */}
      <div style={{ display: "flex", gap: 12, marginBottom: 16, alignItems: "center", flexWrap: "wrap" }}>
        <Input
          placeholder="Tìm kiếm đề thi..."
          prefix={<SearchOutlined />}
          value={search}
          onChange={e => setSearch(e.target.value)}
          style={{ maxWidth: 300 }}
          allowClear
        />
        <Space>
          <Button
            type="primary"
            icon={<UnlockOutlined />}
            onClick={() => handleBulk("public")}
            disabled={selectedIds.length === 0}
          >
            Mở công khai ({selectedIds.length})
          </Button>
          <Button
            danger
            icon={<LockOutlined />}
            onClick={() => handleBulk("lock")}
            disabled={selectedIds.length === 0}
          >
            Khóa VIP ({selectedIds.length})
          </Button>
        </Space>
      </div>

      {/* Table */}
      <Table
        columns={columns}
        dataSource={exams}
        rowKey="id"
        loading={loading}
        size="middle"
        pagination={false}
        rowSelection={{
          selectedRowKeys: selectedIds,
          onChange: (keys) => setSelectedIds(keys as number[]),
        }}
      />
    </div>
  );
}
