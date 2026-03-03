"use client";
import { useState, useEffect, useCallback } from "react";
import { Table, Input, Tag, Typography, Space } from "antd";
import { SearchOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import { adminGet } from "@/lib/admin-api";

const { Title, Text } = Typography;

interface Question { id: number; template_title: string | null; order: number; question_type: string; toeic_part: string | null; text: string; mondai: number | null; source: string | null; }

export default function ExamQuestionsPage() {
  const [items, setItems] = useState<Question[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  const fetchData = useCallback(() => {
    setLoading(true);
    const params = new URLSearchParams();
    if (search) params.set("search", search);
    adminGet<{ items: Question[] }>(`/crud/exam/questions/?${params}`)
      .then((d) => setItems(d.items || []))
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, [search]);
  useEffect(() => { fetchData(); }, [fetchData]);

  const columns: ColumnsType<Question> = [
    { title: "ID", dataIndex: "id", width: 60, render: (id) => <Text type="secondary" style={{ fontSize: 12 }}>{id}</Text> },
    { title: "Đề thi", dataIndex: "template_title", width: 180, ellipsis: true, render: (t) => <Text style={{ fontSize: 12 }}>{t || "—"}</Text> },
    { title: "#", dataIndex: "order", width: 50 },
    { title: "Loại", dataIndex: "question_type", width: 100, render: (t) => <Tag color="processing">{t}</Tag> },
    { title: "Part", dataIndex: "toeic_part", width: 80, render: (p) => p ? <Tag color="orange">{p}</Tag> : "—" },
    { title: "Nội dung", dataIndex: "text", ellipsis: true, render: (t) => <Text style={{ fontSize: 12 }}>{t || "—"}</Text> },
    { title: "Mondai", dataIndex: "mondai", width: 70, render: (m) => m ?? "—" },
  ];

  return (
    <div>
      <Space orientation="vertical" size="large" style={{ width: "100%" }}>
        <div><Title level={3} style={{ margin: 0 }}>❓ Câu hỏi</Title><Text type="secondary">{items.length} câu</Text></div>
        <Input.Search placeholder="Tìm câu hỏi..." allowClear onSearch={setSearch} prefix={<SearchOutlined />} style={{ maxWidth: 400 }} />
        <Table<Question> columns={columns} dataSource={items} rowKey="id" loading={loading} size="middle" pagination={{ pageSize: 50, showSizeChanger: false }} />
      </Space>
    </div>
  );
}
