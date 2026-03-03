"use client";
import { useState, useEffect, useCallback } from "react";
import { Table, Button, Input, Tag, Typography, Space } from "antd";
import { SearchOutlined, BookOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import { adminGet } from "@/lib/admin-api";
import Link from "next/link";

const { Title, Text } = Typography;

interface Template { id: number; title: string; book_title: string | null; level: string; category: string; question_count: number; }

export default function DokkaiToolPage() {
  const [items, setItems] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  const fetchData = useCallback(() => {
    setLoading(true);
    const params = new URLSearchParams();
    params.set("category", "dokkai");
    if (search) params.set("search", search);
    params.set("page", String(page));
    adminGet<{ items: Template[]; count: number }>(`/crud/exam/templates/?${params}`)
      .then((d) => { setItems(d.items || []); setTotalCount(d.count || 0); })
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, [search, page]);
  useEffect(() => { fetchData(); }, [fetchData]);

  const columns: ColumnsType<Template> = [
    { title: "ID", dataIndex: "id", width: 60, render: (id) => <Text type="secondary" style={{ fontSize: 12 }}>{id}</Text> },
    { title: "Tiêu đề", dataIndex: "title", ellipsis: true, render: (t) => <Text strong>{t}</Text> },
    { title: "Sách", dataIndex: "book_title", width: 150, ellipsis: true, render: (b) => <Text style={{ fontSize: 12 }}>{b || "—"}</Text> },
    { title: "Level", dataIndex: "level", width: 70, render: (l) => <Tag color="processing">{l || "—"}</Tag> },
    { title: "Câu hỏi", dataIndex: "question_count", width: 80, render: (c) => <Text strong>{c}</Text> },
    {
      title: "Hành động", key: "actions", width: 120, align: "center",
      render: (_, t) => <Link href={`/admin/exam/dokkai-editor/${t.id}`}><Button size="small" icon={<BookOutlined />}>Mở Editor</Button></Link>,
    },
  ];

  return (
    <div>
      <Space orientation="vertical" size="large" style={{ width: "100%" }}>
        <div><Title level={3} style={{ margin: 0 }}>📖 Dokkai Tool</Title><Text type="secondary">{totalCount} bài đọc hiểu</Text></div>
        <Input.Search placeholder="Tìm bài đọc hiểu..." allowClear onSearch={(v) => { setSearch(v); setPage(1); }} prefix={<SearchOutlined />} style={{ maxWidth: 400 }} />
        <Table<Template> columns={columns} dataSource={items} rowKey="id" loading={loading} size="middle"
          pagination={{ current: page, total: totalCount, pageSize: 50, onChange: (p) => setPage(p), showSizeChanger: false, showTotal: (total, range) => `${range[0]}-${range[1]} / ${total}` }} />
      </Space>
    </div>
  );
}
