"use client";

import { useState, useEffect, useCallback } from "react";
import { Table, Input, Button, Tag, Typography, Space } from "antd";
import { SearchOutlined, UploadOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import { adminGet } from "@/lib/admin-api";
import Link from "next/link";

const { Title, Text } = Typography;

interface Template {
  id: number; title: string; book_title: string | null; level: string;
  category: string; group_type: string; lesson_index: number;
  question_count: number; main_question_type: string | null;
  is_full_toeic: boolean;
}

const CAT_COLORS: Record<string, string> = { toeic: "green", jlpt: "blue", choukai: "orange", dokkai: "purple" };

export default function ExamTemplatesPage() {
  const [items, setItems] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("all");
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  const fetchData = useCallback(() => {
    setLoading(true);
    const params = new URLSearchParams();
    if (search) params.set("search", search);
    if (category !== "all") params.set("category", category);
    params.set("page", String(page));
    adminGet<{ items: Template[]; count: number }>(`/crud/exam/templates/?${params}`)
      .then((d) => { setItems(d.items || []); setTotalCount(d.count || 0); })
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, [search, category, page]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const columns: ColumnsType<Template> = [
    { title: "ID", dataIndex: "id", width: 60, render: (id) => <Text type="secondary" style={{ fontSize: 12 }}>{id}</Text> },
    { title: "Tiêu đề", dataIndex: "title", ellipsis: true, render: (t) => <Text strong>{t}</Text> },
    { title: "Sách", dataIndex: "book_title", width: 150, ellipsis: true, render: (b) => <Text style={{ fontSize: 12 }}>{b || "—"}</Text> },
    { title: "Level", dataIndex: "level", width: 70, render: (l) => <Tag color="processing">{l || "—"}</Tag> },
    { title: "Category", dataIndex: "category", width: 90, render: (c) => <Tag color={CAT_COLORS[c] || "default"}>{c}</Tag> },
    { title: "Loại", key: "type", width: 100, render: (_, t) => <Text style={{ fontSize: 12 }}>{t.group_type || t.main_question_type || "—"}</Text> },
    { title: "Câu hỏi", dataIndex: "question_count", width: 80, render: (c) => <Text strong>{c}</Text> },
    { title: "Full", dataIndex: "is_full_toeic", width: 60, render: (f) => f ? <Tag color="success">Full</Tag> : "—" },
  ];

  return (
    <div>
      <Space orientation="vertical" size="large" style={{ width: "100%" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <Title level={3} style={{ margin: 0 }}>📝 Bài thi</Title>
            <Text type="secondary">{totalCount} đề thi</Text>
          </div>
          <Link href="/admin/exam/import-toeic"><Button icon={<UploadOutlined />}>Import TOEIC</Button></Link>
        </div>

        <Space wrap>
          <Input.Search placeholder="Tìm bài thi..." allowClear onSearch={(v) => { setSearch(v); setPage(1); }} prefix={<SearchOutlined />} style={{ width: 300 }} />
          {["all", "toeic", "jlpt", "choukai", "dokkai"].map((c) => (
            <Button key={c} type={category === c ? "primary" : "default"} size="small" onClick={() => { setCategory(c); setPage(1); }}>
              {c === "all" ? "Tất cả" : c.toUpperCase()}
            </Button>
          ))}
        </Space>

        <Table<Template>
          columns={columns} dataSource={items} rowKey="id" loading={loading} size="middle"
          pagination={{
            current: page, total: totalCount, pageSize: 50,
            onChange: (p) => setPage(p), showSizeChanger: false,
            showTotal: (total, range) => `${range[0]}-${range[1]} / ${total}`,
          }}
        />
      </Space>
    </div>
  );
}
