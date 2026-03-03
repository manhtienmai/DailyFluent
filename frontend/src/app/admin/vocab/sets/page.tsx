"use client";
import { useState, useEffect, useCallback } from "react";
import { Table, Button, Tag, Modal, Input, Select, Switch, Typography, Space, Popconfirm } from "antd";
import { PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import { adminGet, adminPost, adminPut, adminDelete } from "@/lib/admin-api";
import Link from "next/link";

const { Title, Text } = Typography;
const { TextArea } = Input;

interface VocabSet {
  id: number; title: string; collection: string | null; status: string;
  is_public: boolean; toeic_level: string | null; set_number: number; word_count: number;
}

export default function VocabSetsPage() {
  const [items, setItems] = useState<VocabSet[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState(""); const [page, setPage] = useState(1); const [totalCount, setTotalCount] = useState(0);
  const [showCreate, setShowCreate] = useState(false); const [newTitle, setNewTitle] = useState(""); const [newDesc, setNewDesc] = useState(""); const [creating, setCreating] = useState(false);
  const [editSet, setEditSet] = useState<VocabSet | null>(null); const [editTitle, setEditTitle] = useState(""); const [editDesc, setEditDesc] = useState(""); const [editStatus, setEditStatus] = useState("published"); const [editPublic, setEditPublic] = useState(true); const [saving, setSaving] = useState(false);

  const fetchData = useCallback(() => {
    setLoading(true);
    const params = new URLSearchParams();
    if (search) params.set("search", search); params.set("page", String(page));
    adminGet<{ items: VocabSet[]; count: number }>(`/crud/vocab/sets/?${params}`)
      .then((d) => { setItems(d.items || []); setTotalCount(d.count || 0); })
      .catch(() => setItems([])).finally(() => setLoading(false));
  }, [search, page]);
  useEffect(() => { fetchData(); }, [fetchData]);

  const handleCreate = async () => {
    if (!newTitle.trim()) return; setCreating(true);
    try { await adminPost("/crud/vocab/quick-create-set/", { title: newTitle.trim(), description: newDesc.trim() }); setShowCreate(false); setNewTitle(""); setNewDesc(""); fetchData(); } catch { /* ignore */ }
    setCreating(false);
  };

  const openEdit = (s: VocabSet) => { setEditSet(s); setEditTitle(s.title); setEditDesc(""); setEditStatus(s.status || "published"); setEditPublic(s.is_public); };
  const handleEdit = async () => {
    if (!editSet || !editTitle.trim()) return; setSaving(true);
    try { await adminPut(`/crud/vocab/sets/${editSet.id}/`, { title: editTitle.trim(), description: editDesc, status: editStatus, is_public: editPublic }); setEditSet(null); fetchData(); } catch { /* ignore */ }
    setSaving(false);
  };
  const handleDelete = async (id: number, title: string) => { if (!confirm(`Xoá bộ từ "${title}"?`)) return; await adminDelete(`/crud/vocab/sets/${id}/`); fetchData(); };

  const columns: ColumnsType<VocabSet> = [
    { title: "ID", dataIndex: "id", width: 50, render: (id) => <Text type="secondary" style={{ fontSize: 12 }}>{id}</Text> },
    { title: "Tiêu đề", dataIndex: "title", render: (_, s) => <Link href={`/admin/vocab/sets/${s.id}`} style={{ fontWeight: 600, color: "var(--action-primary)" }}>{s.title}</Link> },
    { title: "Collection", dataIndex: "collection", width: 120, render: (c) => c || "—" },
    { title: "Level", dataIndex: "toeic_level", width: 80, render: (l) => l ? <Tag color="processing">{l}</Tag> : "—" },
    { title: "Trạng thái", dataIndex: "status", width: 100, render: (s) => <Tag>{s || "—"}</Tag> },
    { title: "Từ", dataIndex: "word_count", width: 60, render: (c) => <Text strong>{c}</Text> },
    { title: "Public", dataIndex: "is_public", width: 60, render: (p) => p ? <Tag color="success">✓</Tag> : <Tag color="error">✗</Tag> },
    {
      title: "", key: "actions", width: 130, align: "center",
      render: (_, s) => (
        <Space size="small">
          <Button size="small" type="text" icon={<EditOutlined />} onClick={() => openEdit(s)} />
          <Link href={`/admin/vocab/sets/${s.id}`}><Button size="small" type="text">📋</Button></Link>
          <Popconfirm title={`Xoá "${s.title}"?`} onConfirm={() => handleDelete(s.id, s.title)} okText="Xoá" cancelText="Huỷ" okButtonProps={{ danger: true }}>
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
          <div><Title level={3} style={{ margin: 0 }}>📂 Bộ từ vựng</Title><Text type="secondary">Quản lý {totalCount} bộ từ vựng</Text></div>
          <Space>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => setShowCreate(true)}>Tạo bộ mới</Button>
            <Link href="/admin/vocab/import-jp"><Button>🇯🇵 Import JP</Button></Link>
          </Space>
        </div>
        <Input.Search placeholder="Tìm bộ từ vựng..." allowClear onSearch={(v) => { setSearch(v); setPage(1); }} prefix={<SearchOutlined />} style={{ maxWidth: 400 }} />
        <Table<VocabSet> columns={columns} dataSource={items} rowKey="id" loading={loading} size="middle"
          pagination={{ current: page, total: totalCount, pageSize: 50, onChange: (p) => setPage(p), showSizeChanger: false, showTotal: (total, range) => `${range[0]}-${range[1]} / ${total}` }} />
      </Space>

      <Modal title="✨ Tạo bộ từ vựng mới" open={showCreate} onCancel={() => setShowCreate(false)} onOk={handleCreate} okText="Tạo bộ" okButtonProps={{ disabled: creating || !newTitle.trim() }} confirmLoading={creating} width={480}>
        <Space orientation="vertical" style={{ width: "100%" }} size="small">
          <div><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Tiêu đề *</Text><Input placeholder="VD: Mimikara N2 — Bài 1" value={newTitle} onChange={(e) => setNewTitle(e.target.value)} autoFocus onPressEnter={handleCreate} /></div>
          <div><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Mô tả</Text><TextArea placeholder="Mô tả ngắn (tuỳ chọn)" value={newDesc} onChange={(e) => setNewDesc(e.target.value)} rows={3} /></div>
        </Space>
      </Modal>

      <Modal title="✏️ Chỉnh sửa bộ từ vựng" open={!!editSet} onCancel={() => setEditSet(null)} onOk={handleEdit} okText="Lưu thay đổi" okButtonProps={{ disabled: saving || !editTitle.trim() }} confirmLoading={saving} width={480}>
        <Space orientation="vertical" style={{ width: "100%" }} size="small">
          <div><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Tiêu đề *</Text><Input value={editTitle} onChange={(e) => setEditTitle(e.target.value)} autoFocus onPressEnter={handleEdit} /></div>
          <div><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Mô tả</Text><TextArea value={editDesc} onChange={(e) => setEditDesc(e.target.value)} rows={2} /></div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <div><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Trạng thái</Text><Select value={editStatus} onChange={setEditStatus} style={{ width: "100%" }} options={[{ value: "published", label: "Published" }, { value: "draft", label: "Draft" }, { value: "archived", label: "Archived" }]} /></div>
            <div><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Hiển thị</Text><div><Switch checked={editPublic} onChange={setEditPublic} checkedChildren="Công khai" unCheckedChildren="Riêng tư" /></div></div>
          </div>
        </Space>
      </Modal>
    </div>
  );
}
