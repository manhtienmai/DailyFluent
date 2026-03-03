"use client";
import { useState, useEffect, useCallback } from "react";
import { Table, Button, Tag, Modal, Input, Select, Typography, Space, Popconfirm } from "antd";
import { PlusOutlined, EditOutlined, DeleteOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import { adminGet, adminPost, adminPut, adminDelete } from "@/lib/admin-api";
import InlineEditCell from "@/components/admin/InlineEditCell";

const { Title, Text } = Typography;

interface GrammarBook { id: number; title: string; level: string; point_count: number; }
const LEVELS = ["N5", "N4", "N3", "N2", "N1"];

export default function GrammarPage() {
  const [items, setItems] = useState<GrammarBook[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<GrammarBook | null>(null);
  const [form, setForm] = useState({ title: "", level: "N5" });

  const fetchData = useCallback(() => {
    setLoading(true);
    adminGet<{ items: GrammarBook[] }>("/crud/grammar/books/")
      .then((d) => setItems(d.items || []))
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const openCreate = () => { setEditing(null); setForm({ title: "", level: "N5" }); setShowForm(true); };
  const openEdit = (b: GrammarBook) => { setEditing(b); setForm({ title: b.title, level: b.level }); setShowForm(true); };

  const save = async () => {
    if (editing) await adminPut(`/crud/grammar/books/${editing.id}/`, form);
    else await adminPost("/crud/grammar/books/", form);
    setShowForm(false); fetchData();
  };

  const columns: ColumnsType<GrammarBook> = [
    { title: "ID", dataIndex: "id", width: 60, render: (id) => <Text type="secondary" style={{ fontSize: 12 }}>{id}</Text> },
    {
      title: "Tiêu đề", dataIndex: "title",
      render: (_, g) => (
        <InlineEditCell value={g.title} style={{ fontWeight: 600 }} onSave={async (v) => { await adminPut(`/crud/grammar/books/${g.id}/`, { title: v, level: g.level }); fetchData(); }} />
      ),
    },
    { title: "Level", dataIndex: "level", width: 80, render: (level) => <Tag color="processing">{level || "—"}</Tag> },
    { title: "Điểm ngữ pháp", dataIndex: "point_count", width: 120, render: (c) => <Text strong>{c}</Text> },
    {
      title: "", key: "actions", width: 100, align: "center",
      render: (_, g) => (
        <Space size="small">
          <Button size="small" type="text" icon={<EditOutlined />} onClick={() => openEdit(g)} />
          <Popconfirm title="Xoá sách ngữ pháp này?" onConfirm={async () => { await adminDelete(`/crud/grammar/books/${g.id}/`); fetchData(); }} okText="Xoá" cancelText="Huỷ" okButtonProps={{ danger: true }}>
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
          <div>
            <Title level={3} style={{ margin: 0 }}>📐 Ngữ pháp</Title>
            <Text type="secondary">{items.length} sách</Text>
          </div>
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>Thêm sách</Button>
        </div>
        <Table<GrammarBook> columns={columns} dataSource={items} rowKey="id" loading={loading} size="middle" pagination={false} />
      </Space>

      <Modal title={editing ? "✏️ Sửa sách" : "➕ Thêm sách ngữ pháp"} open={showForm} onCancel={() => setShowForm(false)} onOk={save} okText={`💾 ${editing ? "Lưu" : "Tạo"}`} okButtonProps={{ disabled: !form.title }} width={420}>
        <div style={{ marginBottom: 12 }}>
          <Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Tiêu đề</Text>
          <Input value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} placeholder="VD: Minna no Nihongo N4" />
        </div>
        <div>
          <Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Cấp JLPT</Text>
          <Select value={form.level} onChange={v => setForm({ ...form, level: v })} style={{ width: "100%" }} options={LEVELS.map(l => ({ value: l, label: l }))} />
        </div>
      </Modal>
    </div>
  );
}
