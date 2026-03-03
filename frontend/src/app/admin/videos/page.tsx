"use client";
import { useState, useEffect, useCallback } from "react";
import { Table, Button, Tag, Modal, Input, Select, Typography, Space, Popconfirm } from "antd";
import { PlusOutlined, EditOutlined, DeleteOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import { adminGet, adminPost, adminPut, adminDelete } from "@/lib/admin-api";
import InlineEditCell from "@/components/admin/InlineEditCell";

const { Title, Text } = Typography;
const { TextArea } = Input;

interface Video { id: number; title: string; level: string; category: string; created_at: string; transcript_count: number; }
const LEVELS = ["N5", "N4", "N3", "N2", "N1"];

export default function VideosPage() {
  const [items, setItems] = useState<Video[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Video | null>(null);
  const [form, setForm] = useState({ title: "", level: "N5", youtube_id: "", description: "" });

  const fetchData = useCallback(() => {
    setLoading(true);
    adminGet<{ items: Video[] }>("/crud/videos/")
      .then((d) => setItems(d.items || []))
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const openCreate = () => { setEditing(null); setForm({ title: "", level: "N5", youtube_id: "", description: "" }); setShowForm(true); };
  const openEdit = (v: Video) => { setEditing(v); setForm({ title: v.title, level: v.level, youtube_id: "", description: "" }); setShowForm(true); };

  const save = async () => {
    if (editing) await adminPut(`/crud/videos/${editing.id}/`, form);
    else await adminPost("/crud/videos/", form);
    setShowForm(false); fetchData();
  };

  const columns: ColumnsType<Video> = [
    { title: "ID", dataIndex: "id", width: 60, render: (id) => <Text type="secondary" style={{ fontSize: 12 }}>{id}</Text> },
    {
      title: "Tiêu đề", dataIndex: "title",
      render: (_, v) => <InlineEditCell value={v.title} style={{ fontWeight: 600 }} onSave={async (val) => { await adminPut(`/crud/videos/${v.id}/`, { title: val, level: v.level, youtube_id: "", description: "" }); fetchData(); }} />,
    },
    { title: "Level", dataIndex: "level", width: 70, render: (l) => <Tag color="processing">{l}</Tag> },
    {
      title: "Category", key: "cat",
      render: (_, v) => <InlineEditCell value={v.category || ""} onSave={async (val) => { await adminPut(`/crud/videos/${v.id}/`, { title: v.title, level: v.level, category: val, youtube_id: "", description: "" }); fetchData(); }} />,
    },
    { title: "Transcripts", dataIndex: "transcript_count", width: 90, render: (c) => <Text strong>{c}</Text> },
    { title: "Ngày tạo", dataIndex: "created_at", width: 110, render: (d) => <Text style={{ fontSize: 12 }}>{d ? new Date(d).toLocaleDateString("vi-VN") : "—"}</Text> },
    {
      title: "", key: "actions", width: 80, align: "center",
      render: (_, v) => (
        <Space size="small">
          <Button size="small" type="text" icon={<EditOutlined />} onClick={() => openEdit(v)} />
          <Popconfirm title="Xoá video này?" onConfirm={async () => { await adminDelete(`/crud/videos/${v.id}/`); fetchData(); }} okText="Xoá" cancelText="Huỷ" okButtonProps={{ danger: true }}>
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
            <Title level={3} style={{ margin: 0 }}>🎬 Video</Title>
            <Text type="secondary">{items.length} videos</Text>
          </div>
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>Thêm video</Button>
        </div>
        <Table<Video> columns={columns} dataSource={items} rowKey="id" loading={loading} size="middle" pagination={false} />
      </Space>

      <Modal title={editing ? "✏️ Sửa video" : "➕ Thêm video"} open={showForm} onCancel={() => setShowForm(false)} onOk={save} okText={`💾 ${editing ? "Lưu" : "Tạo"}`} okButtonProps={{ disabled: !form.title }} width={460}>
        <div style={{ marginBottom: 12 }}>
          <Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Tiêu đề</Text>
          <Input value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} placeholder="Lesson 01 — Giới thiệu bản thân" />
        </div>
        <Space style={{ width: "100%", marginBottom: 12 }}>
          <div style={{ flex: 1 }}>
            <Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Level</Text>
            <Select value={form.level} onChange={v => setForm({ ...form, level: v })} style={{ width: "100%" }} options={LEVELS.map(l => ({ value: l, label: l }))} />
          </div>
          <div style={{ flex: 1 }}>
            <Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>YouTube ID</Text>
            <Input value={form.youtube_id} onChange={e => setForm({ ...form, youtube_id: e.target.value })} placeholder="dQw4w9WgXcQ" />
          </div>
        </Space>
        <div>
          <Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Mô tả</Text>
          <TextArea value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} rows={3} />
        </div>
      </Modal>
    </div>
  );
}
