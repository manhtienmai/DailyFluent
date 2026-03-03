"use client";
import { useState, useEffect, useCallback } from "react";
import { Table, Button, Tag, Modal, Input, InputNumber, Select, Switch, Tabs, Typography, Space, Popconfirm } from "antd";
import { PlusOutlined, EditOutlined, DeleteOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import { adminGet, adminPost, adminPut, adminDelete } from "@/lib/admin-api";
import InlineEditCell from "@/components/admin/InlineEditCell";

const { Title, Text } = Typography;

interface Plan { id: number; name: string; price: number; duration_days: number; is_active: boolean; is_popular: boolean; }
interface Payment { id: number; user: string; plan: string; amount: number; status: string; created_at: string; }
const STATUSES = ["pending", "processing", "completed", "failed", "cancelled"];
const STATUS_COLORS: Record<string, string> = { pending: "warning", processing: "processing", completed: "success", failed: "error", cancelled: "default" };

export default function PaymentPage() {
  const [tab, setTab] = useState<"plans" | "payments">("plans");
  const [plans, setPlans] = useState<Plan[]>([]);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Plan | null>(null);
  const [form, setForm] = useState({ name: "", price: 0, duration_days: 30, is_active: true, is_popular: false });

  const fetchPlans = useCallback(() => { setLoading(true); adminGet<{ items: Plan[] }>("/crud/payment/plans/").then(d => setPlans(d.items || [])).catch(() => setPlans([])).finally(() => setLoading(false)); }, []);
  const fetchPayments = useCallback(() => { setLoading(true); adminGet<{ items: Payment[] }>("/crud/payment/payments/").then(d => setPayments(d.items || [])).catch(() => setPayments([])).finally(() => setLoading(false)); }, []);
  useEffect(() => { if (tab === "plans") fetchPlans(); else fetchPayments(); }, [tab, fetchPlans, fetchPayments]);

  const openCreate = () => { setEditing(null); setForm({ name: "", price: 0, duration_days: 30, is_active: true, is_popular: false }); setShowForm(true); };
  const openEdit = (p: Plan) => { setEditing(p); setForm({ name: p.name, price: p.price, duration_days: p.duration_days, is_active: p.is_active, is_popular: p.is_popular }); setShowForm(true); };
  const save = async () => { if (editing) await adminPut(`/crud/payment/plans/${editing.id}/`, form); else await adminPost("/crud/payment/plans/", form); setShowForm(false); fetchPlans(); };
  const updatePaymentStatus = async (id: number, status: string) => { await adminPut(`/crud/payment/payments/${id}/status/`, { status }); fetchPayments(); };

  const planCols: ColumnsType<Plan> = [
    { title: "ID", dataIndex: "id", width: 60, render: (id) => <Text type="secondary" style={{ fontSize: 12 }}>{id}</Text> },
    { title: "Tên gói", dataIndex: "name", render: (_, p) => <InlineEditCell value={p.name} style={{ fontWeight: 600 }} onSave={async (v) => { await adminPut(`/crud/payment/plans/${p.id}/`, { ...p, name: v }); fetchPlans(); }} /> },
    { title: "Giá", dataIndex: "price", width: 120, render: (p) => <Text strong>{p.toLocaleString()}₫</Text> },
    { title: "Thời hạn", dataIndex: "duration_days", width: 90, render: (d) => `${d} ngày` },
    { title: "Active", dataIndex: "is_active", width: 70, render: (a) => a ? <Tag color="success">✓</Tag> : <Tag color="error">✗</Tag> },
    { title: "Popular", dataIndex: "is_popular", width: 70, render: (p) => p ? <Tag color="warning">⭐</Tag> : "—" },
    {
      title: "", key: "actions", width: 90, align: "center",
      render: (_, p) => (
        <Space size="small">
          <Button size="small" type="text" icon={<EditOutlined />} onClick={() => openEdit(p)} />
          <Popconfirm title="Xoá gói?" onConfirm={async () => { await adminDelete(`/crud/payment/plans/${p.id}/`); fetchPlans(); }} okText="Xoá" cancelText="Huỷ" okButtonProps={{ danger: true }}>
            <Button size="small" type="text" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const paymentCols: ColumnsType<Payment> = [
    { title: "ID", dataIndex: "id", width: 60, render: (id) => <Text type="secondary" style={{ fontSize: 12 }}>{id}</Text> },
    { title: "User", dataIndex: "user", render: (u) => <Text strong>{u}</Text> },
    { title: "Gói", dataIndex: "plan", width: 130 },
    { title: "Số tiền", dataIndex: "amount", width: 120, render: (a) => <Text strong>{a.toLocaleString()}₫</Text> },
    {
      title: "Trạng thái", dataIndex: "status", width: 140,
      render: (s, p) => (
        <Select value={s} onChange={(v) => updatePaymentStatus(p.id, v)} size="small" style={{ width: 120 }}
          options={STATUSES.map(st => ({ value: st, label: <Tag color={STATUS_COLORS[st]}>{st}</Tag> }))} />
      ),
    },
    { title: "Ngày", dataIndex: "created_at", width: 100, render: (d) => <Text style={{ fontSize: 12 }}>{new Date(d).toLocaleDateString("vi-VN")}</Text> },
  ];

  return (
    <div>
      <Space orientation="vertical" size="large" style={{ width: "100%" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div><Title level={3} style={{ margin: 0 }}>💳 Thanh toán</Title><Text type="secondary">Gói & Giao dịch</Text></div>
          {tab === "plans" && <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>Thêm gói</Button>}
        </div>
        <Tabs activeKey={tab} onChange={(k) => setTab(k as "plans" | "payments")} items={[
          { key: "plans", label: "💰 Gói" },
          { key: "payments", label: "📋 Giao dịch" },
        ]} />
        {tab === "plans" && <Table<Plan> columns={planCols} dataSource={plans} rowKey="id" loading={loading} size="middle" pagination={false} />}
        {tab === "payments" && <Table<Payment> columns={paymentCols} dataSource={payments} rowKey="id" loading={loading} size="middle" pagination={{ pageSize: 50, showSizeChanger: false }} />}
      </Space>
      <Modal title={editing ? "✏️ Sửa gói" : "➕ Thêm gói thanh toán"} open={showForm} onCancel={() => setShowForm(false)} onOk={save} okText={`💾 ${editing ? "Lưu" : "Tạo"}`} okButtonProps={{ disabled: !form.name }} width={420}>
        <Space orientation="vertical" style={{ width: "100%" }} size="small">
          <div><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Tên gói</Text><Input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="Premium 1 tháng" /></div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            <div><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Giá (VND)</Text><InputNumber value={form.price} onChange={v => setForm({ ...form, price: v || 0 })} style={{ width: "100%" }} /></div>
            <div><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Thời hạn (ngày)</Text><InputNumber value={form.duration_days} onChange={v => setForm({ ...form, duration_days: v || 30 })} style={{ width: "100%" }} /></div>
          </div>
          <div style={{ display: "flex", gap: 24 }}>
            <div><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Active</Text><div><Switch checked={form.is_active} onChange={v => setForm({ ...form, is_active: v })} checkedChildren="Bật" unCheckedChildren="Tắt" /></div></div>
            <div><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Popular</Text><div><Switch checked={form.is_popular} onChange={v => setForm({ ...form, is_popular: v })} checkedChildren="⭐" unCheckedChildren="—" /></div></div>
          </div>
        </Space>
      </Modal>
    </div>
  );
}
