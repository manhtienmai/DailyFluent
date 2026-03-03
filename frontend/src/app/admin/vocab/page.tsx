"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Table, Input, Button, Tag, Modal, Select, Space, Typography, Card,
  Popconfirm, Spin, Descriptions, Divider, Row, Col, Form,
} from "antd";
import {
  PlusOutlined, DeleteOutlined, EditOutlined, DownOutlined, UpOutlined,
  SearchOutlined, ThunderboltOutlined, ImportOutlined,
} from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import { adminGet, adminPost, adminPut, adminDelete } from "@/lib/admin-api";
import InlineEditCell from "@/components/admin/InlineEditCell";
import Link from "next/link";

const { Title, Text } = Typography;

/* ── Types ── */
interface Vocab {
  id: number; word: string; language: string; entry_count: number;
  extra_data?: Record<string, string>; first_meaning?: string; first_pos?: string;
}
interface VocabDetail {
  id: number; word: string; language: string;
  extra_data?: Record<string, string>; entries: Entry[];
}
interface Entry {
  id: number; part_of_speech: string; ipa: string;
  audio_us: string; audio_uk: string; definitions: Def[];
}
interface Def {
  id: number; meaning: string; extra_data?: Record<string, unknown>;
  examples: { id: number; sentence: string; translation: string; source: string }[];
}
interface PaginatedResponse { items: Vocab[]; count: number; }

const POS_OPTIONS = ["noun", "verb", "adj", "adv", "particle", "expression", "other"];

/* ── Page ── */
export default function VocabPage() {
  const [items, setItems] = useState<Vocab[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [language, setLanguage] = useState("all");
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  // Expanded
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [expandedDetail, setExpandedDetail] = useState<VocabDetail | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  // Modals
  const [showCreate, setShowCreate] = useState(false);
  const [createForm, setCreateForm] = useState({ word: "", language: "jp", reading: "", han_viet: "", part_of_speech: "noun", meaning: "" });
  const [creating, setCreating] = useState(false);

  const [addingEntry, setAddingEntry] = useState<number | null>(null);
  const [entryForm, setEntryForm] = useState({ part_of_speech: "noun", ipa: "" });

  const [addingDef, setAddingDef] = useState<{ vocabId: number; entryId: number } | null>(null);
  const [defForm, setDefForm] = useState({ meaning: "" });

  const fetchData = useCallback(() => {
    setLoading(true);
    const params = new URLSearchParams();
    if (search) params.set("search", search);
    if (language !== "all") params.set("language", language);
    params.set("page", String(page));
    adminGet<PaginatedResponse>(`/crud/vocab/?${params}`)
      .then((d) => { setItems(d.items || []); setTotalCount(d.count || 0); })
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, [search, language, page]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const fetchDetail = async (id: number) => {
    setLoadingDetail(true);
    try { setExpandedDetail(await adminGet<VocabDetail>(`/crud/vocab/${id}/`)); }
    catch { setExpandedDetail(null); }
    setLoadingDetail(false);
  };

  const toggleExpand = (id: number) => {
    if (expandedId === id) { setExpandedId(null); setExpandedDetail(null); }
    else { setExpandedId(id); fetchDetail(id); }
  };

  const handleCreate = async () => {
    if (!createForm.word.trim()) return;
    setCreating(true);
    try {
      await adminPost("/crud/vocab/create/", createForm);
      setShowCreate(false);
      setCreateForm({ word: "", language: "jp", reading: "", han_viet: "", part_of_speech: "noun", meaning: "" });
      fetchData();
    } catch { /* ignore */ }
    setCreating(false);
  };

  const handleUpdateVocab = async (id: number, field: string, value: string) => {
    await adminPut(`/crud/vocab/update/${id}/`, { [field]: value });
    fetchData();
    if (expandedId === id) fetchDetail(id);
  };

  const handleAddEntry = async () => {
    if (!addingEntry) return;
    await adminPost(`/crud/vocab/${addingEntry}/entries/`, entryForm);
    setAddingEntry(null); setEntryForm({ part_of_speech: "noun", ipa: "" });
    fetchDetail(addingEntry); fetchData();
  };

  const handleUpdateEntry = async (vocabId: number, entryId: number, field: string, value: string) => {
    const entry = expandedDetail?.entries.find(e => e.id === entryId);
    if (!entry) return;
    await adminPut(`/crud/vocab/${vocabId}/entries/${entryId}/`, {
      part_of_speech: field === "part_of_speech" ? value : entry.part_of_speech,
      ipa: field === "ipa" ? value : entry.ipa,
    });
    fetchDetail(vocabId);
  };

  const handleAddDef = async () => {
    if (!addingDef || !defForm.meaning.trim()) return;
    await adminPost(`/crud/vocab/${addingDef.vocabId}/entries/${addingDef.entryId}/definitions/`, defForm);
    setAddingDef(null); setDefForm({ meaning: "" });
    fetchDetail(addingDef.vocabId); fetchData();
  };

  const handleUpdateDef = async (vocabId: number, entryId: number, defId: number, meaning: string) => {
    await adminPut(`/crud/vocab/${vocabId}/entries/${entryId}/definitions/${defId}/`, { meaning });
    fetchDetail(vocabId); fetchData();
  };

  /* ── Columns ── */
  const columns: ColumnsType<Vocab> = [
    { title: "ID", dataIndex: "id", width: 60, render: (id) => <Text type="secondary" style={{ fontSize: 12 }}>{id}</Text> },
    {
      title: "Từ / Kanji", dataIndex: "word",
      render: (_, v) => {
        const reading = v.extra_data?.reading || "";
        return (
          <div>
            <Text strong style={{ fontSize: 16, fontFamily: v.language === "jp" ? "'Noto Sans JP', sans-serif" : undefined }}>{v.word}</Text>
            {reading && <div><Text type="secondary" style={{ fontSize: 12, fontFamily: "'Noto Sans JP', sans-serif" }}>{reading}</Text></div>}
          </div>
        );
      },
    },
    {
      title: "Hán Việt", key: "han_viet", width: 120,
      render: (_, v) => <Text type="secondary" style={{ fontSize: 12, fontWeight: 600, textTransform: "uppercase" }}>{v.extra_data?.han_viet || "—"}</Text>,
    },
    {
      title: "Nghĩa", key: "meaning", ellipsis: true,
      render: (_, v) => <Text type="secondary" style={{ fontSize: 12 }}>{v.first_meaning || "—"}</Text>,
    },
    {
      title: "POS", key: "pos", width: 80,
      render: (_, v) => v.first_pos ? <Tag color="processing" style={{ fontSize: 10 }}>{v.first_pos}</Tag> : "—",
    },
    {
      title: "Ngôn ngữ", dataIndex: "language", width: 80, align: "center",
      render: (lang) => <Tag color={lang === "jp" ? "warning" : "processing"}>{lang === "jp" ? "🇯🇵" : "🇬🇧"}</Tag>,
    },
    {
      title: "", key: "actions", width: 100, align: "center",
      render: (_, v) => (
        <Space size="small" onClick={(e) => e.stopPropagation()}>
          <Button size="small" type="text" icon={expandedId === v.id ? <UpOutlined /> : <DownOutlined />} onClick={() => toggleExpand(v.id)} />
          <Popconfirm title={`Xoá từ "${v.word}"?`} onConfirm={async () => {
            await adminDelete(`/crud/vocab/${v.id}/`);
            if (expandedId === v.id) { setExpandedId(null); setExpandedDetail(null); }
            fetchData();
          }} okText="Xoá" cancelText="Huỷ" okButtonProps={{ danger: true }}>
            <Button size="small" type="text" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  /* ── Expanded row render ── */
  const expandedRowRender = (v: Vocab) => {
    if (expandedId !== v.id) return null;
    if (loadingDetail) return <div style={{ textAlign: "center", padding: 24 }}><Spin /></div>;
    if (!expandedDetail) return <Text type="secondary">Không thể tải chi tiết</Text>;

    return (
      <div style={{ padding: "8px 0" }}>
        {/* Vocab fields */}
        <Row gutter={12} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Text type="secondary" style={{ fontSize: 11, fontWeight: 600, display: "block", marginBottom: 2 }}>Từ / Kanji</Text>
            <Input value={expandedDetail.word} readOnly style={{ fontSize: 18, fontWeight: 700, fontFamily: "'Noto Sans JP', sans-serif" }} />
          </Col>
          <Col span={6}>
            <Text type="secondary" style={{ fontSize: 11, fontWeight: 600, display: "block", marginBottom: 2 }}>Reading</Text>
            <Input
              defaultValue={expandedDetail.extra_data?.reading || ""}
              style={{ fontFamily: "'Noto Sans JP', sans-serif" }}
              onBlur={(e) => { if (e.target.value !== (expandedDetail.extra_data?.reading || "")) handleUpdateVocab(v.id, "reading", e.target.value); }}
              onPressEnter={(e) => (e.target as HTMLInputElement).blur()}
            />
          </Col>
          <Col span={6}>
            <Text type="secondary" style={{ fontSize: 11, fontWeight: 600, display: "block", marginBottom: 2 }}>Hán Việt</Text>
            <Input
              defaultValue={expandedDetail.extra_data?.han_viet || ""}
              style={{ textTransform: "uppercase", fontWeight: 600 }}
              onBlur={(e) => { if (e.target.value !== (expandedDetail.extra_data?.han_viet || "")) handleUpdateVocab(v.id, "han_viet", e.target.value); }}
              onPressEnter={(e) => (e.target as HTMLInputElement).blur()}
            />
          </Col>
          <Col span={6}>
            <Text type="secondary" style={{ fontSize: 11, fontWeight: 600, display: "block", marginBottom: 2 }}>Ngôn ngữ</Text>
            <div style={{ padding: "8px 12px" }}>{expandedDetail.language === "jp" ? "🇯🇵 Japanese" : "🇬🇧 English"}</div>
          </Col>
        </Row>

        {/* Entries */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
          <Text strong>📝 Entries ({expandedDetail.entries.length})</Text>
          <Button size="small" type="primary" icon={<PlusOutlined />} onClick={() => { setAddingEntry(v.id); setEntryForm({ part_of_speech: "noun", ipa: "" }); }}>
            Entry
          </Button>
        </div>

        {expandedDetail.entries.length === 0 ? (
          <Card size="small"><Text type="secondary">Chưa có entry — nhấn &quot;+ Entry&quot; để thêm</Text></Card>
        ) : (
          <Space orientation="vertical" style={{ width: "100%" }} size="small">
            {expandedDetail.entries.map((entry) => (
              <Card key={entry.id} size="small" title={
                <Space>
                  <Tag color="processing">{entry.part_of_speech || "—"}</Tag>
                  {entry.ipa && <Text type="secondary" italic style={{ fontSize: 12 }}>{entry.ipa}</Text>}
                </Space>
              } extra={
                <Space size="small">
                  <Button size="small" type="primary" icon={<PlusOutlined />} onClick={() => { setAddingDef({ vocabId: v.id, entryId: entry.id }); setDefForm({ meaning: "" }); }}>Nghĩa</Button>
                  <Popconfirm title="Xoá entry này?" onConfirm={async () => { await adminDelete(`/crud/vocab/${v.id}/entries/${entry.id}/`); fetchDetail(v.id); fetchData(); }} okText="Xoá" cancelText="Huỷ" okButtonProps={{ danger: true }}>
                    <Button size="small" danger icon={<DeleteOutlined />} />
                  </Popconfirm>
                </Space>
              }>
                {entry.definitions.length === 0 ? (
                  <Text type="secondary" style={{ fontSize: 12 }}>Chưa có nghĩa</Text>
                ) : (
                  <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                    {entry.definitions.map((def) => (
                      <div key={def.id} style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <Text type="secondary" style={{ fontSize: 12, flexShrink: 0 }}>#{def.id}</Text>
                        <Input
                          variant="borderless"
                          defaultValue={def.meaning}
                          style={{ flex: 1, fontSize: 13 }}
                          onBlur={(e) => { if (e.target.value !== def.meaning) handleUpdateDef(v.id, entry.id, def.id, e.target.value); }}
                          onPressEnter={(e) => (e.target as HTMLInputElement).blur()}
                        />
                        <Popconfirm title="Xoá nghĩa?" onConfirm={() => { adminDelete(`/crud/vocab/${v.id}/entries/${entry.id}/definitions/${def.id}/`); fetchDetail(v.id); fetchData(); }} okText="Xoá" cancelText="Huỷ" okButtonProps={{ danger: true }}>
                          <Button type="text" danger size="small" icon={<DeleteOutlined />} />
                        </Popconfirm>
                      </div>
                    ))}
                  </div>
                )}
                {/* Examples */}
                {entry.definitions.some(d => d.examples.length > 0) && (
                  <>
                    <Divider style={{ margin: "8px 0" }} />
                    <Text type="secondary" style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase" }}>Ví dụ</Text>
                    {entry.definitions.flatMap(d => d.examples).slice(0, 3).map(ex => (
                      <div key={ex.id} style={{ fontSize: 11, marginTop: 2 }}>
                        <span dangerouslySetInnerHTML={{ __html: ex.sentence }} />
                        {ex.translation && <Text type="secondary" style={{ marginLeft: 8 }}>— {ex.translation}</Text>}
                      </div>
                    ))}
                  </>
                )}
              </Card>
            ))}
          </Space>
        )}
      </div>
    );
  };

  return (
    <div>
      <Space orientation="vertical" size="large" style={{ width: "100%" }}>
        {/* Header */}
        <Row justify="space-between" align="middle">
          <Col>
            <Title level={3} style={{ margin: 0 }}>📖 Từ vựng</Title>
            <Text type="secondary">{totalCount} từ</Text>
          </Col>
          <Space>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => setShowCreate(true)}>Tạo từ mới</Button>
            <Link href="/admin/vocab/bulk-add"><Button icon={<ThunderboltOutlined />}>Thêm hàng loạt</Button></Link>
            <Link href="/admin/vocab/import-jp"><Button icon={<ImportOutlined />}>Import JP</Button></Link>
          </Space>
        </Row>

        {/* Filters */}
        <Row gutter={16} align="middle">
          <Col flex="1" style={{ maxWidth: 400 }}>
            <Input.Search
              placeholder="Tìm theo từ, reading, hán việt, nghĩa..."
              allowClear
              onSearch={(v) => { setSearch(v); setPage(1); }}
              onChange={(e) => { if (!e.target.value) { setSearch(""); setPage(1); } }}
              prefix={<SearchOutlined />}
            />
          </Col>
          <Col>
            <Space>
              {[{ key: "all", label: "Tất cả" }, { key: "jp", label: "🇯🇵 Japanese" }, { key: "en", label: "🇬🇧 English" }].map((l) => (
                <Button key={l.key} type={language === l.key ? "primary" : "default"} size="small" onClick={() => { setLanguage(l.key); setPage(1); }}>
                  {l.label}
                </Button>
              ))}
            </Space>
          </Col>
        </Row>

        {/* Table */}
        <Table<Vocab>
          columns={columns}
          dataSource={items}
          rowKey="id"
          loading={loading}
          size="middle"
          onRow={(v) => ({ onClick: () => toggleExpand(v.id), style: { cursor: "pointer", background: expandedId === v.id ? "rgba(99,102,241,0.04)" : undefined } })}
          expandable={{
            expandedRowRender,
            expandedRowKeys: expandedId ? [expandedId] : [],
            showExpandColumn: false,
          }}
          pagination={{
            current: page, total: totalCount, pageSize: 50,
            onChange: (p) => setPage(p), showSizeChanger: false,
            showTotal: (total, range) => `${range[0]}-${range[1]} / ${total}`,
          }}
        />
      </Space>

      {/* ── Create Modal ── */}
      <Modal
        title="✨ Tạo từ vựng mới"
        open={showCreate}
        onCancel={() => setShowCreate(false)}
        onOk={handleCreate}
        okText="💾 Tạo từ"
        confirmLoading={creating}
        okButtonProps={{ disabled: !createForm.word.trim() }}
        width={560}
      >
        <Row gutter={12} style={{ marginBottom: 12 }}>
          <Col span={12}>
            <Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Từ / Kanji *</Text>
            <Input placeholder="男性" value={createForm.word} onChange={(e) => setCreateForm({ ...createForm, word: e.target.value })}
              style={{ fontSize: 18, fontWeight: 700, fontFamily: "'Noto Sans JP', sans-serif" }} autoFocus />
          </Col>
          <Col span={12}>
            <Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Ngôn ngữ</Text>
            <Select value={createForm.language} onChange={(v) => setCreateForm({ ...createForm, language: v })} style={{ width: "100%" }}
              options={[{ value: "jp", label: "🇯🇵 Japanese" }, { value: "en", label: "🇬🇧 English" }]} />
          </Col>
        </Row>
        <Row gutter={12} style={{ marginBottom: 12 }}>
          <Col span={12}>
            <Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Reading (Hiragana)</Text>
            <Input placeholder="だんせい" value={createForm.reading} onChange={(e) => setCreateForm({ ...createForm, reading: e.target.value })}
              style={{ fontFamily: "'Noto Sans JP', sans-serif" }} />
          </Col>
          <Col span={12}>
            <Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Hán Việt</Text>
            <Input placeholder="NAM TÍNH" value={createForm.han_viet} onChange={(e) => setCreateForm({ ...createForm, han_viet: e.target.value })}
              style={{ textTransform: "uppercase" }} />
          </Col>
        </Row>
        <Row gutter={12}>
          <Col span={12}>
            <Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Loại từ</Text>
            <Select value={createForm.part_of_speech} onChange={(v) => setCreateForm({ ...createForm, part_of_speech: v })} style={{ width: "100%" }}
              options={POS_OPTIONS.map(p => ({ value: p, label: p }))} />
          </Col>
          <Col span={12}>
            <Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Nghĩa tiếng Việt *</Text>
            <Input placeholder="đàn ông, nam giới" value={createForm.meaning} onChange={(e) => setCreateForm({ ...createForm, meaning: e.target.value })}
              onPressEnter={handleCreate} />
          </Col>
        </Row>
      </Modal>

      {/* ── Add Entry Modal ── */}
      <Modal
        title="➕ Thêm Entry"
        open={!!addingEntry}
        onCancel={() => setAddingEntry(null)}
        onOk={handleAddEntry}
        okText="💾 Thêm"
        width={400}
      >
        <div style={{ marginBottom: 12 }}>
          <Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Loại từ</Text>
          <Select value={entryForm.part_of_speech} onChange={(v) => setEntryForm({ ...entryForm, part_of_speech: v })} style={{ width: "100%" }}
            options={POS_OPTIONS.map(p => ({ value: p, label: p }))} />
        </div>
        <div>
          <Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>IPA / Phiên âm</Text>
          <Input placeholder="/ˈrek.ɚd/" value={entryForm.ipa} onChange={(e) => setEntryForm({ ...entryForm, ipa: e.target.value })} onPressEnter={handleAddEntry} />
        </div>
      </Modal>

      {/* ── Add Definition Modal ── */}
      <Modal
        title="➕ Thêm nghĩa"
        open={!!addingDef}
        onCancel={() => setAddingDef(null)}
        onOk={handleAddDef}
        okText="💾 Thêm"
        okButtonProps={{ disabled: !defForm.meaning.trim() }}
        width={420}
      >
        <Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Nghĩa tiếng Việt *</Text>
        <Input placeholder="đàn ông, nam giới" value={defForm.meaning} autoFocus
          onChange={(e) => setDefForm({ ...defForm, meaning: e.target.value })}
          onPressEnter={handleAddDef} />
      </Modal>
    </div>
  );
}
