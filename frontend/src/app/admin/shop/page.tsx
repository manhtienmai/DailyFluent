"use client";
import { useState, useEffect, useCallback } from "react";
import { Table, Button, Tag, Modal, Input, InputNumber, Select, Switch, Typography, Space, Popconfirm } from "antd";
import { PlusOutlined, EditOutlined, DeleteOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import { adminGet, adminPost, adminPut, adminDelete } from "@/lib/admin-api";
import InlineEditCell from "@/components/admin/InlineEditCell";

const { Title, Text } = Typography;

interface Frame { id: number; name: string; rarity: string; price: number; is_active: boolean; display_order: number; }
const RARITIES = ["COMMON", "RARE", "EPIC", "LEGENDARY"];
const RARITY_COLORS: Record<string, string> = { COMMON: "default", RARE: "processing", EPIC: "warning", LEGENDARY: "error" };

export default function ShopPage() {
  const [items, setItems] = useState<Frame[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Frame | null>(null);
  const [form, setForm] = useState({ name: "", rarity: "COMMON", price: 100, is_active: true, display_order: 0 });

  const fetchData = useCallback(() => { setLoading(true); adminGet<{ items: Frame[] }>("/crud/shop/frames/").then((d) => setItems(d.items || [])).catch(() => setItems([])).finally(() => setLoading(false)); }, []);
  useEffect(() => { fetchData(); }, [fetchData]);

  const openCreate = () => { setEditing(null); setForm({ name: "", rarity: "COMMON", price: 100, is_active: true, display_order: 0 }); setShowForm(true); };
  const openEdit = (f: Frame) => { setEditing(f); setForm({ name: f.name, rarity: f.rarity, price: f.price, is_active: f.is_active, display_order: f.display_order }); setShowForm(true); };
  const save = async () => { if (editing) await adminPut(`/crud/shop/frames/${editing.id}/`, form); else await adminPost("/crud/shop/frames/", form); setShowForm(false); fetchData(); };

  const columns: ColumnsType<Frame> = [
    { title: "ID", dataIndex: "id", width: 60, render: (id) => <Text type="secondary" style={{ fontSize: 12 }}>{id}</Text> },
    { title: "Tên frame", dataIndex: "name", render: (_, f) => <InlineEditCell value={f.name} style={{ fontWeight: 600 }} onSave={async (v) => { await adminPut(`/crud/shop/frames/${f.id}/`, { ...f, name: v }); fetchData(); }} /> },
    { title: "Rarity", dataIndex: "rarity", width: 100, render: (r) => <Tag color={RARITY_COLORS[r] || "default"}>{r}</Tag> },
    { title: "Giá", dataIndex: "price", width: 80, render: (p) => <Text strong>{p} 🪙</Text> },
    { title: "Active", dataIndex: "is_active", width: 70, render: (a) => a ? <Tag color="success">✓</Tag> : <Tag color="error">✗</Tag> },
    { title: "Thứ tự", dataIndex: "display_order", width: 70 },
    {
      title: "", key: "actions", width: 90, align: "center",
      render: (_, f) => (
        <Space size="small">
          <Button size="small" type="text" icon={<EditOutlined />} onClick={() => openEdit(f)} />
          <Popconfirm title="Xoá frame?" onConfirm={async () => { await adminDelete(`/crud/shop/frames/${f.id}/`); fetchData(); }} okText="Xoá" cancelText="Huỷ" okButtonProps={{ danger: true }}>
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
          <div><Title level={3} style={{ margin: 0 }}>🛍️ Shop</Title><Text type="secondary">{items.length} frames</Text></div>
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>Thêm frame</Button>
        </div>
        <Table<Frame> columns={columns} dataSource={items} rowKey="id" loading={loading} size="middle" pagination={false} />
      </Space>
      <Modal title={editing ? "✏️ Sửa frame" : "➕ Thêm frame"} open={showForm} onCancel={() => setShowForm(false)} onOk={save} okText={`💾 ${editing ? "Lưu" : "Tạo"}`} okButtonProps={{ disabled: !form.name }} width={420}>
        <Space orientation="vertical" style={{ width: "100%" }} size="small">
          <div><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Tên</Text><Input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="Golden Crown" /></div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            <div><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Rarity</Text><Select value={form.rarity} onChange={v => setForm({ ...form, rarity: v })} style={{ width: "100%" }} options={RARITIES.map(r => ({ value: r, label: r }))} /></div>
            <div><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Giá (coins)</Text><InputNumber value={form.price} onChange={v => setForm({ ...form, price: v || 0 })} style={{ width: "100%" }} /></div>
            <div><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Thứ tự</Text><InputNumber value={form.display_order} onChange={v => setForm({ ...form, display_order: v || 0 })} style={{ width: "100%" }} /></div>
            <div><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Active</Text><div><Switch checked={form.is_active} onChange={v => setForm({ ...form, is_active: v })} checkedChildren="Bật" unCheckedChildren="Tắt" /></div></div>
          </div>
        </Space>
      </Modal>
    </div>
  );
}
