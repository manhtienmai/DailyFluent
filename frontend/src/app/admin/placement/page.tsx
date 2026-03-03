"use client";
import { useState, useEffect, useCallback } from "react";
import { Table, Button, Tag, Modal, Input, Select, Switch, Typography, Space, Popconfirm } from "antd";
import { PlusOutlined, EditOutlined, DeleteOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import { adminGet, adminPost, adminPut, adminDelete } from "@/lib/admin-api";

const { Title, Text } = Typography;
const { TextArea } = Input;

interface PlacementQuestion { id: number; skill: string; difficulty: string; question_preview: string; correct_answer: string; is_active: boolean; }
const SKILLS = ["L1", "L2", "L3", "L4", "R5", "R6", "R7", "VOC", "GRM"];
const DIFFICULTIES = [1, 2, 3, 4, 5, 6];
const DIFF_LABELS: Record<number, string> = { 1: "Beginner", 2: "Elementary", 3: "Intermediate", 4: "Upper Int.", 5: "Advanced", 6: "Expert" };
const DIFF_COLORS: Record<number, string> = { 1: "green", 2: "cyan", 3: "blue", 4: "purple", 5: "orange", 6: "red" };

export default function PlacementPage() {
  const [items, setItems] = useState<PlacementQuestion[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<PlacementQuestion | null>(null);
  const [form, setForm] = useState({ skill: "VOC", difficulty: 1, question_text: "", correct_answer: "", is_active: true });

  const fetchData = useCallback(() => { setLoading(true); adminGet<{ items: PlacementQuestion[] }>("/crud/placement/questions/").then((d) => setItems(d.items || [])).catch(() => setItems([])).finally(() => setLoading(false)); }, []);
  useEffect(() => { fetchData(); }, [fetchData]);

  const openCreate = () => { setEditing(null); setForm({ skill: "VOC", difficulty: 1, question_text: "", correct_answer: "", is_active: true }); setShowForm(true); };
  const openEdit = (q: PlacementQuestion) => { setEditing(q); setForm({ skill: q.skill, difficulty: Number(q.difficulty), question_text: q.question_preview, correct_answer: q.correct_answer, is_active: q.is_active }); setShowForm(true); };
  const save = async () => { if (editing) await adminPut(`/crud/placement/questions/${editing.id}/`, form); else await adminPost("/crud/placement/questions/", form); setShowForm(false); fetchData(); };

  const columns: ColumnsType<PlacementQuestion> = [
    { title: "ID", dataIndex: "id", width: 60, render: (id) => <Text type="secondary" style={{ fontSize: 12 }}>{id}</Text> },
    { title: "Skill", dataIndex: "skill", width: 70, render: (s) => <Tag color="processing">{s}</Tag> },
    { title: "Difficulty", dataIndex: "difficulty", width: 120, render: (d) => <Tag color={DIFF_COLORS[d] || "default"}>{d} — {DIFF_LABELS[d] || ""}</Tag> },
    { title: "Câu hỏi", dataIndex: "question_preview", ellipsis: true, render: (q) => <Text style={{ fontSize: 12 }}>{q}</Text> },
    { title: "Đáp án", dataIndex: "correct_answer", width: 100, render: (a) => <Text strong style={{ fontSize: 12 }}>{a}</Text> },
    { title: "Active", dataIndex: "is_active", width: 70, render: (a) => a ? <Tag color="success">✓</Tag> : <Tag color="error">✗</Tag> },
    {
      title: "", key: "actions", width: 90, align: "center",
      render: (_, q) => (
        <Space size="small">
          <Button size="small" type="text" icon={<EditOutlined />} onClick={() => openEdit(q)} />
          <Popconfirm title="Xoá câu hỏi?" onConfirm={async () => { await adminDelete(`/crud/placement/questions/${q.id}/`); fetchData(); }} okText="Xoá" cancelText="Huỷ" okButtonProps={{ danger: true }}>
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
          <div><Title level={3} style={{ margin: 0 }}>📊 Placement Test</Title><Text type="secondary">{items.length} câu hỏi</Text></div>
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>Thêm câu hỏi</Button>
        </div>
        <Table<PlacementQuestion> columns={columns} dataSource={items} rowKey="id" loading={loading} size="middle" pagination={false} />
      </Space>
      <Modal title={editing ? "✏️ Sửa câu hỏi" : "➕ Thêm câu hỏi"} open={showForm} onCancel={() => setShowForm(false)} onOk={save} okText={`💾 ${editing ? "Lưu" : "Tạo"}`} okButtonProps={{ disabled: !form.question_text }} width={460}>
        <Space orientation="vertical" style={{ width: "100%" }} size="small">
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            <div><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Skill</Text><Select value={form.skill} onChange={v => setForm({ ...form, skill: v })} style={{ width: "100%" }} options={SKILLS.map(s => ({ value: s, label: s }))} /></div>
            <div><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Difficulty</Text><Select value={form.difficulty} onChange={v => setForm({ ...form, difficulty: v })} style={{ width: "100%" }} options={DIFFICULTIES.map(d => ({ value: d, label: `${d} — ${DIFF_LABELS[d]}` }))} /></div>
          </div>
          <div><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Nội dung câu hỏi</Text><TextArea value={form.question_text} onChange={e => setForm({ ...form, question_text: e.target.value })} rows={3} /></div>
          <div><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Đáp án đúng</Text><Input value={form.correct_answer} onChange={e => setForm({ ...form, correct_answer: e.target.value })} /></div>
          <div><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Active</Text><div><Switch checked={form.is_active} onChange={v => setForm({ ...form, is_active: v })} checkedChildren="Bật" unCheckedChildren="Tắt" /></div></div>
        </Space>
      </Modal>
    </div>
  );
}
