"use client";
import { useState, useEffect, useCallback } from "react";
import { Table, Button, Tag, Modal, Input, InputNumber, Switch, Typography, Space, Popconfirm } from "antd";
import { PlusOutlined, EditOutlined, DeleteOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import { adminGet, adminPost, adminPut, adminDelete } from "@/lib/admin-api";
import InlineEditCell from "@/components/admin/InlineEditCell";

const { Title, Text } = Typography;

interface Course { id: number; title: string; slug: string; order: number; is_active: boolean; section_count: number; }

export default function CoursesPage() {
  const [items, setItems] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Course | null>(null);
  const [form, setForm] = useState({ title: "", order: 0, is_active: true });

  const fetchData = useCallback(() => {
    setLoading(true);
    adminGet<{ items: Course[] }>("/crud/courses/")
      .then((d) => setItems(d.items || []))
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, []);
  useEffect(() => { fetchData(); }, [fetchData]);

  const openCreate = () => { setEditing(null); setForm({ title: "", order: 0, is_active: true }); setShowForm(true); };
  const openEdit = (c: Course) => { setEditing(c); setForm({ title: c.title, order: c.order, is_active: c.is_active }); setShowForm(true); };
  const save = async () => { if (editing) await adminPut(`/crud/courses/${editing.id}/`, form); else await adminPost("/crud/courses/", form); setShowForm(false); fetchData(); };

  const columns: ColumnsType<Course> = [
    { title: "ID", dataIndex: "id", width: 60, render: (id) => <Text type="secondary" style={{ fontSize: 12 }}>{id}</Text> },
    { title: "Tiêu đề", dataIndex: "title", render: (_, c) => <InlineEditCell value={c.title} style={{ fontWeight: 600 }} onSave={async (v) => { await adminPut(`/crud/courses/${c.id}/`, { title: v, order: c.order, is_active: c.is_active }); fetchData(); }} /> },
    { title: "Slug", dataIndex: "slug", width: 150, render: (s) => <Text style={{ fontSize: 12 }}>{s}</Text> },
    { title: "Thứ tự", dataIndex: "order", width: 70 },
    { title: "Sections", dataIndex: "section_count", width: 80, render: (c) => <Text strong>{c}</Text> },
    { title: "Active", dataIndex: "is_active", width: 70, render: (a) => a ? <Tag color="success">✓</Tag> : <Tag color="error">✗</Tag> },
    {
      title: "", key: "actions", width: 90, align: "center",
      render: (_, c) => (
        <Space size="small">
          <Button size="small" type="text" icon={<EditOutlined />} onClick={() => openEdit(c)} />
          <Popconfirm title="Xoá khoá học này?" onConfirm={async () => { await adminDelete(`/crud/courses/${c.id}/`); fetchData(); }} okText="Xoá" cancelText="Huỷ" okButtonProps={{ danger: true }}>
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
          <div><Title level={3} style={{ margin: 0 }}>🎓 Khoá học</Title><Text type="secondary">Course → Section → Lesson — {items.length} khoá</Text></div>
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>Thêm khoá</Button>
        </div>
        <Table<Course> columns={columns} dataSource={items} rowKey="id" loading={loading} size="middle" pagination={false} />
      </Space>
      <Modal title={editing ? "✏️ Sửa khoá học" : "➕ Thêm khoá học"} open={showForm} onCancel={() => setShowForm(false)} onOk={save} okText={`💾 ${editing ? "Lưu" : "Tạo"}`} okButtonProps={{ disabled: !form.title }} width={420}>
        <Space orientation="vertical" style={{ width: "100%" }} size="small">
          <div><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Tiêu đề</Text><Input value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} placeholder="VD: Mimikara N2" /></div>
          <div><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Thứ tự</Text><InputNumber value={form.order} onChange={v => setForm({ ...form, order: v || 0 })} style={{ width: "100%" }} /></div>
          <div><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Active</Text><div><Switch checked={form.is_active} onChange={v => setForm({ ...form, is_active: v })} checkedChildren="Bật" unCheckedChildren="Tắt" /></div></div>
        </Space>
      </Modal>
    </div>
  );
}
