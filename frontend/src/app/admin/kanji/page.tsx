"use client";
import { useState, useEffect, useCallback } from "react";
import { Table, Button, Tag, Modal, Input, InputNumber, Select, Typography, Space, Popconfirm, Tabs, Row, Col } from "antd";
import { PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined, SearchOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import { adminGet, adminPost, adminPut, adminDelete } from "@/lib/admin-api";
import InlineEditCell from "@/components/admin/InlineEditCell";

const { Title, Text } = Typography;
const { TextArea } = Input;

interface KanjiLesson { id: number; title: string; level: string; lesson_number: number; order: number; kanji_count: number; }
interface KanjiItem {
  id: number; char: string; sino_vi: string; keyword: string;
  onyomi: string; kunyomi: string; meaning_vi: string;
  strokes: number | null; note: string; lesson_id: number | null;
  lesson_title: string; order: number;
}
const JLPT_LEVELS = ["N5", "N4", "N3", "N2", "N1"];

export default function KanjiPage() {
  const [tab, setTab] = useState<"lessons" | "kanji">("lessons");
  const [lessons, setLessons] = useState<KanjiLesson[]>([]);
  const [kanjiList, setKanjiList] = useState<KanjiItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filterLevel, setFilterLevel] = useState("");
  const [filterLesson, setFilterLesson] = useState(0);

  const [showCreateLesson, setShowCreateLesson] = useState(false);
  const [newLesson, setNewLesson] = useState({ topic: "", jlpt_level: "N5", lesson_number: 1, order: 0 });

  const [showEditLesson, setShowEditLesson] = useState(false);
  const [editingLessonId, setEditingLessonId] = useState<number | null>(null);
  const [editLesson, setEditLesson] = useState({ topic: "", jlpt_level: "N5", lesson_number: 1, order: 0 });

  const [showKanjiForm, setShowKanjiForm] = useState(false);
  const [editingKanji, setEditingKanji] = useState<KanjiItem | null>(null);
  const [kanjiForm, setKanjiForm] = useState({
    char: "", sino_vi: "", keyword: "", onyomi: "", kunyomi: "",
    meaning_vi: "", strokes: null as number | null, note: "", lesson_id: null as number | null, order: 0,
  });

  const fetchLessons = useCallback(() => {
    setLoading(true);
    adminGet<{ items: KanjiLesson[] }>("/crud/kanji/lessons/")
      .then(d => setLessons(d.items || []))
      .catch(() => setLessons([]))
      .finally(() => setLoading(false));
  }, []);

  const fetchKanji = useCallback(() => {
    setLoading(true);
    let url = "/crud/kanji/list/";
    const params: string[] = [];
    if (search) params.push(`search=${encodeURIComponent(search)}`);
    if (filterLevel) params.push(`level=${filterLevel}`);
    if (filterLesson) params.push(`lesson_id=${filterLesson}`);
    if (params.length) url += `?${params.join("&")}`;
    adminGet<{ items: KanjiItem[] }>(url)
      .then(d => setKanjiList(d.items || []))
      .catch(() => setKanjiList([]))
      .finally(() => setLoading(false));
  }, [search, filterLevel, filterLesson]);

  useEffect(() => { if (tab === "lessons") fetchLessons(); else fetchKanji(); }, [tab, fetchLessons, fetchKanji]);

  // Lesson CRUD
  const createLesson = async () => {
    await adminPost("/crud/kanji/lessons/", newLesson);
    setShowCreateLesson(false); setNewLesson({ topic: "", jlpt_level: "N5", lesson_number: 1, order: 0 }); fetchLessons();
  };
  const openEditLesson = (l: KanjiLesson) => {
    setEditingLessonId(l.id); setEditLesson({ topic: l.title, jlpt_level: l.level, lesson_number: l.lesson_number, order: l.order }); setShowEditLesson(true);
  };
  const updateLesson = async () => {
    if (!editingLessonId) return;
    await adminPut(`/crud/kanji/lessons/${editingLessonId}/`, editLesson); setShowEditLesson(false); setEditingLessonId(null); fetchLessons();
  };

  // Kanji CRUD
  const openCreateKanji = () => {
    setEditingKanji(null); setKanjiForm({ char: "", sino_vi: "", keyword: "", onyomi: "", kunyomi: "", meaning_vi: "", strokes: null, note: "", lesson_id: null, order: 0 }); setShowKanjiForm(true);
  };
  const openEditKanji = (k: KanjiItem) => {
    setEditingKanji(k); setKanjiForm({ char: k.char, sino_vi: k.sino_vi, keyword: k.keyword, onyomi: k.onyomi, kunyomi: k.kunyomi, meaning_vi: k.meaning_vi, strokes: k.strokes, note: k.note, lesson_id: k.lesson_id, order: k.order }); setShowKanjiForm(true);
  };
  const saveKanji = async () => {
    if (editingKanji) await adminPut(`/crud/kanji/${editingKanji.id}/`, kanjiForm);
    else await adminPost("/crud/kanji/create/", kanjiForm);
    setShowKanjiForm(false); fetchKanji();
  };

  // Lesson columns
  const lessonCols: ColumnsType<KanjiLesson> = [
    { title: "ID", dataIndex: "id", width: 50, render: (id) => <Text type="secondary" style={{ fontSize: 12 }}>{id}</Text> },
    { title: "JLPT", dataIndex: "level", width: 70, render: (l) => <Tag color="processing">{l}</Tag> },
    { title: "Bài", dataIndex: "lesson_number", width: 70, render: (n) => <Text strong>Bài {n}</Text> },
    {
      title: "Chủ đề", dataIndex: "title",
      render: (_, l) => <InlineEditCell value={l.title} onSave={async (v) => { await adminPut(`/crud/kanji/lessons/${l.id}/`, { topic: v, jlpt_level: l.level, lesson_number: l.lesson_number, order: l.order }); fetchLessons(); }} />,
    },
    { title: "Thứ tự", dataIndex: "order", width: 70 },
    { title: "Kanji", dataIndex: "kanji_count", width: 70, render: (c) => <Text strong>{c}</Text> },
    {
      title: "", key: "actions", width: 140, align: "center",
      render: (_, l) => (
        <Space size="small">
          <Button size="small" type="text" icon={<EditOutlined />} onClick={() => openEditLesson(l)} />
          <Button size="small" type="text" icon={<EyeOutlined />} onClick={() => { setTab("kanji"); setFilterLesson(l.id); }}>Xem</Button>
          <Popconfirm title="Xoá bài học?" onConfirm={async () => { await adminDelete(`/crud/kanji/lessons/${l.id}/`); fetchLessons(); }} okText="Xoá" cancelText="Huỷ" okButtonProps={{ danger: true }}>
            <Button size="small" type="text" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // Kanji columns
  const kanjiCols: ColumnsType<KanjiItem> = [
    { title: "漢字", dataIndex: "char", width: 60, align: "center", render: (c) => <Text style={{ fontSize: 28, fontWeight: 700, fontFamily: "'Noto Sans JP', sans-serif" }}>{c}</Text> },
    { title: "Hán Việt", key: "sv", render: (_, k) => <InlineEditCell value={k.sino_vi || ""} style={{ fontWeight: 600 }} onSave={async (v) => { await adminPut(`/crud/kanji/${k.id}/`, { ...k, sino_vi: v, note: "" }); fetchKanji(); }} /> },
    { title: "Keyword", key: "kw", render: (_, k) => <InlineEditCell value={k.keyword || ""} style={{ fontSize: 12 }} onSave={async (v) => { await adminPut(`/crud/kanji/${k.id}/`, { ...k, keyword: v, note: "" }); fetchKanji(); }} /> },
    { title: "Âm On", key: "on", render: (_, k) => <InlineEditCell value={k.onyomi || ""} style={{ fontSize: 12, fontFamily: "'Noto Sans JP'" }} onSave={async (v) => { await adminPut(`/crud/kanji/${k.id}/`, { ...k, onyomi: v, note: "" }); fetchKanji(); }} /> },
    { title: "Âm Kun", key: "kun", render: (_, k) => <InlineEditCell value={k.kunyomi || ""} style={{ fontSize: 12, fontFamily: "'Noto Sans JP'" }} onSave={async (v) => { await adminPut(`/crud/kanji/${k.id}/`, { ...k, kunyomi: v, note: "" }); fetchKanji(); }} /> },
    { title: "Nghĩa", key: "mv", render: (_, k) => <InlineEditCell value={k.meaning_vi || ""} style={{ fontSize: 12 }} onSave={async (v) => { await adminPut(`/crud/kanji/${k.id}/`, { ...k, meaning_vi: v, note: "" }); fetchKanji(); }} /> },
    { title: "Nét", dataIndex: "strokes", width: 50, align: "center", render: (s) => s ?? "—" },
    { title: "Bài", dataIndex: "lesson_title", width: 120, ellipsis: true, render: (t) => <Text type="secondary" style={{ fontSize: 11 }}>{t || "—"}</Text> },
    {
      title: "", key: "actions", width: 80, align: "center",
      render: (_, k) => (
        <Space size="small">
          <Button size="small" type="text" icon={<EditOutlined />} onClick={() => openEditKanji(k)} />
          <Popconfirm title="Xoá Kanji?" onConfirm={async () => { await adminDelete(`/crud/kanji/${k.id}/`); fetchKanji(); }} okText="Xoá" cancelText="Huỷ" okButtonProps={{ danger: true }}>
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
            <Title level={3} style={{ margin: 0 }}>漢 Kanji</Title>
            <Text type="secondary">{tab === "lessons" ? `${lessons.length} bài học` : `${kanjiList.length} Hán tự`}</Text>
          </div>
          {tab === "lessons" && <Button type="primary" icon={<PlusOutlined />} onClick={() => setShowCreateLesson(true)}>Thêm bài học</Button>}
          {tab === "kanji" && <Button type="primary" icon={<PlusOutlined />} onClick={openCreateKanji}>Thêm Kanji</Button>}
        </div>

        <Tabs activeKey={tab} onChange={(k) => setTab(k as "lessons" | "kanji")} items={[
          { key: "lessons", label: "📚 Bài học" },
          { key: "kanji", label: "漢 Hán tự" },
        ]} />

        {tab === "lessons" && <Table<KanjiLesson> columns={lessonCols} dataSource={lessons} rowKey="id" loading={loading} size="middle" pagination={false} />}

        {tab === "kanji" && (
          <>
            <Row gutter={12}>
              <Col flex="1"><Input.Search placeholder="Tìm kanji, Hán Việt, keyword..." allowClear onSearch={setSearch} prefix={<SearchOutlined />} /></Col>
              <Col><Select value={filterLevel || undefined} onChange={(v) => setFilterLevel(v || "")} allowClear placeholder="JLPT" style={{ width: 100 }} options={JLPT_LEVELS.map(l => ({ value: l, label: l }))} /></Col>
              <Col>
                <Select value={filterLesson || undefined} onChange={(v) => setFilterLesson(v || 0)} allowClear placeholder="Bài học" style={{ width: 220 }}
                  options={lessons.map(l => ({ value: l.id, label: `[${l.level}] Bài ${l.lesson_number}: ${l.title}` }))} />
              </Col>
            </Row>
            <Table<KanjiItem> columns={kanjiCols} dataSource={kanjiList} rowKey="id" loading={loading} size="middle" pagination={{ pageSize: 50, showSizeChanger: false }} />
          </>
        )}
      </Space>

      {/* Create Lesson Modal */}
      <Modal title="📚 Thêm bài học Kanji" open={showCreateLesson} onCancel={() => setShowCreateLesson(false)} onOk={createLesson} okText="💾 Tạo" okButtonProps={{ disabled: !newLesson.topic }} width={420}>
        <Space orientation="vertical" style={{ width: "100%" }}>
          <div><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Cấp JLPT</Text><Select value={newLesson.jlpt_level} onChange={v => setNewLesson({ ...newLesson, jlpt_level: v })} style={{ width: "100%" }} options={JLPT_LEVELS.map(l => ({ value: l, label: l }))} /></div>
          <div><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Số bài</Text><InputNumber value={newLesson.lesson_number} onChange={v => setNewLesson({ ...newLesson, lesson_number: v || 1 })} style={{ width: "100%" }} /></div>
          <div><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Chủ đề</Text><Input value={newLesson.topic} onChange={e => setNewLesson({ ...newLesson, topic: e.target.value })} placeholder="VD: Số đếm, Thiên nhiên..." /></div>
          <div><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Thứ tự</Text><InputNumber value={newLesson.order} onChange={v => setNewLesson({ ...newLesson, order: v || 0 })} style={{ width: "100%" }} /></div>
        </Space>
      </Modal>

      {/* Edit Lesson Modal */}
      <Modal title="✏️ Sửa bài học Kanji" open={showEditLesson} onCancel={() => setShowEditLesson(false)} onOk={updateLesson} okText="💾 Lưu" okButtonProps={{ disabled: !editLesson.topic }} width={420}>
        <Space orientation="vertical" style={{ width: "100%" }}>
          <div><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Cấp JLPT</Text><Select value={editLesson.jlpt_level} onChange={v => setEditLesson({ ...editLesson, jlpt_level: v })} style={{ width: "100%" }} options={JLPT_LEVELS.map(l => ({ value: l, label: l }))} /></div>
          <div><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Số bài</Text><InputNumber value={editLesson.lesson_number} onChange={v => setEditLesson({ ...editLesson, lesson_number: v || 1 })} style={{ width: "100%" }} /></div>
          <div><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Chủ đề</Text><Input value={editLesson.topic} onChange={e => setEditLesson({ ...editLesson, topic: e.target.value })} /></div>
          <div><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Thứ tự</Text><InputNumber value={editLesson.order} onChange={v => setEditLesson({ ...editLesson, order: v || 0 })} style={{ width: "100%" }} /></div>
        </Space>
      </Modal>

      {/* Create/Edit Kanji Modal */}
      <Modal title={editingKanji ? "✏️ Sửa Kanji" : "➕ Thêm Kanji"} open={showKanjiForm} onCancel={() => setShowKanjiForm(false)} onOk={saveKanji} okText={`💾 ${editingKanji ? "Lưu" : "Tạo"}`} okButtonProps={{ disabled: !kanjiForm.char }} width={520}>
        <Row gutter={12}>
          <Col span={12}><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>漢字</Text><Input value={kanjiForm.char} onChange={e => setKanjiForm({ ...kanjiForm, char: e.target.value })} maxLength={1} style={{ fontSize: 24, textAlign: "center", fontFamily: "'Noto Sans JP'" }} /></Col>
          <Col span={12}><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Âm Hán Việt</Text><Input value={kanjiForm.sino_vi} onChange={e => setKanjiForm({ ...kanjiForm, sino_vi: e.target.value })} placeholder="NHẬT" /></Col>
          <Col span={12}><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Keyword</Text><Input value={kanjiForm.keyword} onChange={e => setKanjiForm({ ...kanjiForm, keyword: e.target.value })} placeholder="Sun" /></Col>
          <Col span={12}><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Âm On</Text><Input value={kanjiForm.onyomi} onChange={e => setKanjiForm({ ...kanjiForm, onyomi: e.target.value })} placeholder="ニチ・ジツ" /></Col>
          <Col span={12}><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Âm Kun</Text><Input value={kanjiForm.kunyomi} onChange={e => setKanjiForm({ ...kanjiForm, kunyomi: e.target.value })} placeholder="ひ・-び" /></Col>
          <Col span={12}><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Nghĩa TV</Text><Input value={kanjiForm.meaning_vi} onChange={e => setKanjiForm({ ...kanjiForm, meaning_vi: e.target.value })} placeholder="Mặt trời" /></Col>
          <Col span={12}><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Số nét</Text><InputNumber value={kanjiForm.strokes} onChange={v => setKanjiForm({ ...kanjiForm, strokes: v })} style={{ width: "100%" }} /></Col>
          <Col span={12}><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Thứ tự</Text><InputNumber value={kanjiForm.order} onChange={v => setKanjiForm({ ...kanjiForm, order: v || 0 })} style={{ width: "100%" }} /></Col>
        </Row>
        <div style={{ marginTop: 12 }}>
          <Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Bài học</Text>
          <Select value={kanjiForm.lesson_id ?? undefined} onChange={v => setKanjiForm({ ...kanjiForm, lesson_id: v ?? null })} allowClear placeholder="— Chưa gán bài —" style={{ width: "100%" }}
            options={lessons.map(l => ({ value: l.id, label: `[${l.level}] Bài ${l.lesson_number}: ${l.title}` }))} />
        </div>
        <div style={{ marginTop: 12 }}>
          <Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Ghi chú / Câu chuyện nhớ</Text>
          <TextArea value={kanjiForm.note} onChange={e => setKanjiForm({ ...kanjiForm, note: e.target.value })} rows={3} />
        </div>
      </Modal>
    </div>
  );
}
