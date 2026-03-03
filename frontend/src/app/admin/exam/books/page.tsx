"use client";
import { useState, useEffect, useCallback } from "react";
import { Table, Button, Tag, Modal, Input, InputNumber, Select, Switch, Typography, Space, Popconfirm } from "antd";
import { PlusOutlined, EditOutlined, DeleteOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import { adminGet, adminPost, adminPut, adminDelete } from "@/lib/admin-api";
import InlineEditCell from "@/components/admin/InlineEditCell";

const { Title, Text } = Typography;
const { TextArea } = Input;

interface ExamBook { id: number; title: string; level: string; category: string; total_lessons: number; is_active: boolean; description: string | null; cover_image: string | null; }
const LEVELS = ["N5", "N4", "N3", "N2", "N1", "TOEIC"];
const CATEGORIES = ["MOJI", "BUN", "DOKKAI", "CHOUKAI", "MIX", "LISTENING", "READING", "TOEIC_FULL"];

export default function ExamBooksPage() {
  const [items, setItems] = useState<ExamBook[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<ExamBook | null>(null);
  const [form, setForm] = useState({ title: "", level: "N5", category: "MOJI", description: "", total_lessons: 0, is_active: true });

  const fetchData = useCallback(() => {
    setLoading(true);
    adminGet<{ items: ExamBook[] }>("/crud/exam/books/")
      .then((d) => setItems(d.items || []))
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, []);
  useEffect(() => { fetchData(); }, [fetchData]);

  const openCreate = () => { setEditing(null); setForm({ title: "", level: "N5", category: "MOJI", description: "", total_lessons: 0, is_active: true }); setShowForm(true); };
  const openEdit = (b: ExamBook) => { setEditing(b); setForm({ title: b.title, level: b.level, category: b.category, description: b.description || "", total_lessons: b.total_lessons, is_active: b.is_active }); setShowForm(true); };
  const save = async () => { if (editing) await adminPut(`/crud/exam/books/${editing.id}/`, form); else await adminPost("/crud/exam/books/", form); setShowForm(false); fetchData(); };

  const columns: ColumnsType<ExamBook> = [
    { title: "ID", dataIndex: "id", width: 60, render: (id) => <Text type="secondary" style={{ fontSize: 12 }}>{id}</Text> },
    { title: "Tiêu đề", dataIndex: "title", render: (_, b) => <InlineEditCell value={b.title} style={{ fontWeight: 600 }} onSave={async (v) => { await adminPut(`/crud/exam/books/${b.id}/`, { ...b, title: v }); fetchData(); }} /> },
    { title: "Level", dataIndex: "level", width: 80, render: (l) => <Tag color="processing">{l}</Tag> },
    { title: "Category", dataIndex: "category", width: 100, render: (c) => <Tag color="orange">{c}</Tag> },
    { title: "Lessons", dataIndex: "total_lessons", width: 80, render: (c) => <Text strong>{c}</Text> },
    { title: "Active", dataIndex: "is_active", width: 70, render: (a) => a ? <Tag color="success">✓</Tag> : <Tag color="error">✗</Tag> },
    {
      title: "", key: "actions", width: 90, align: "center",
      render: (_, b) => (
        <Space size="small">
          <Button size="small" type="text" icon={<EditOutlined />} onClick={() => openEdit(b)} />
          <Popconfirm title="Xoá sách này?" onConfirm={async () => { await adminDelete(`/crud/exam/books/${b.id}/`); fetchData(); }} okText="Xoá" cancelText="Huỷ" okButtonProps={{ danger: true }}>
            <Button size="small" type="text" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Space orientation="vertical" size="large" style={{ width: "100%" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div><Title level={3} style={{ margin: 0 }}>📚 Sách đề thi</Title><Text type="secondary">{items.length} sách</Text></div>
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>Thêm sách</Button>
        </div>
        <Table<ExamBook> columns={columns} dataSource={items} rowKey="id" loading={loading} size="middle" pagination={false} />
      </Space>
      <Modal title={editing ? "✏️ Sửa sách" : "➕ Thêm sách đề thi"} open={showForm} onCancel={() => setShowForm(false)} onOk={save} okText={`💾 ${editing ? "Lưu" : "Tạo"}`} okButtonProps={{ disabled: !form.title }} width={460}>
        <Space orientation="vertical" style={{ width: "100%" }} size="small">
          <div><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Tiêu đề</Text><Input value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} placeholder="Mimikara N2 — Moji goi" /></div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            <div><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Level</Text><Select value={form.level} onChange={v => setForm({ ...form, level: v })} style={{ width: "100%" }} options={LEVELS.map(l => ({ value: l, label: l }))} /></div>
            <div><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Category</Text><Select value={form.category} onChange={v => setForm({ ...form, category: v })} style={{ width: "100%" }} options={CATEGORIES.map(c => ({ value: c, label: c }))} /></div>
            <div><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Số lessons</Text><InputNumber value={form.total_lessons} onChange={v => setForm({ ...form, total_lessons: v || 0 })} style={{ width: "100%" }} /></div>
            <div><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Active</Text><div><Switch checked={form.is_active} onChange={v => setForm({ ...form, is_active: v })} checkedChildren="Bật" unCheckedChildren="Tắt" /></div></div>
          </div>
          <div><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Mô tả</Text><TextArea value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} rows={3} /></div>
        </Space>
      </Modal>
    </div>
  );
}
