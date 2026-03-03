"use client";
import { useState, useEffect, useCallback } from "react";
import { Table, Button, Tag, Modal, Input, InputNumber, Select, Typography, Space, Popconfirm, Checkbox } from "antd";
import { DeleteOutlined, SearchOutlined, ArrowLeftOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import { useParams, useRouter } from "next/navigation";
import { adminGet, adminPost, adminPut, adminDelete } from "@/lib/admin-api";
import Link from "next/link";

const { Title, Text } = Typography;

interface SetDetail {
  id: number; title: string; collection: string | null; status: string;
  is_public: boolean; toeic_level: string | null; set_number: number;
  description: string | null; word_count: number;
  items: { id: number; order: number; word: string; definition: string; part_of_speech: string; has_quiz: boolean }[];
}
interface SearchResult { def_id: number; word: string; meaning: string; pos: string; }
interface SimpleSet { id: number; title: string; collection: string | null; toeic_level: number | null; }

export default function VocabSetDetailPage() {
  const params = useParams(); const router = useRouter();
  const setId = Number(params.id);
  const [detail, setDetail] = useState<SetDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQ, setSearchQ] = useState(""); const [searchResults, setSearchResults] = useState<SearchResult[]>([]); const [searching, setSearching] = useState(false);
  const [selectedItems, setSelectedItems] = useState<Set<number>>(new Set());
  const [allSets, setAllSets] = useState<SimpleSet[]>([]); const [moveTarget, setMoveTarget] = useState<number | null>(null);
  const [editing, setEditing] = useState(false); const [editTitle, setEditTitle] = useState("");

  const fetchDetail = useCallback(() => { setLoading(true); adminGet<SetDetail>(`/crud/vocab/sets/${setId}/`).then((d) => { setDetail(d); setEditTitle(d.title); }).catch(() => setDetail(null)).finally(() => setLoading(false)); }, [setId]);
  useEffect(() => { fetchDetail(); }, [fetchDetail]);
  useEffect(() => { adminGet<SimpleSet[]>("/crud/vocab/sets-simple/").then(setAllSets).catch(() => setAllSets([])); }, []);
  useEffect(() => {
    if (searchQ.length < 2) { setSearchResults([]); return; }
    const timer = setTimeout(() => { setSearching(true); adminGet<SearchResult[]>(`/crud/vocab/search-words/?q=${encodeURIComponent(searchQ)}`).then(setSearchResults).catch(() => setSearchResults([])).finally(() => setSearching(false)); }, 300);
    return () => clearTimeout(timer);
  }, [searchQ]);

  const addWord = async (defId: number) => { await adminPost(`/crud/vocab/sets/${setId}/add-words/`, { definition_ids: [defId] }); fetchDetail(); setSearchResults([]); setSearchQ(""); };
  const removeWord = async (itemId: number) => { if (!confirm("Xoá từ này khỏi set?")) return; await adminDelete(`/crud/vocab/sets/${setId}/words/${itemId}/`); setSelectedItems(prev => { const n = new Set(prev); n.delete(itemId); return n; }); fetchDetail(); };
  const removeSelected = async () => { if (selectedItems.size === 0) return; if (!confirm(`Xoá ${selectedItems.size} từ đã chọn?`)) return; for (const id of selectedItems) await adminDelete(`/crud/vocab/sets/${setId}/words/${id}/`); setSelectedItems(new Set()); fetchDetail(); };
  const moveSelected = async () => { if (!moveTarget || selectedItems.size === 0) return; await adminPost(`/crud/vocab/sets/${setId}/move-words/`, { item_ids: Array.from(selectedItems), target_set_id: moveTarget }); setSelectedItems(new Set()); setMoveTarget(null); fetchDetail(); };
  const saveTitle = async () => { if (!editTitle.trim() || !detail) return; await adminPut(`/crud/vocab/sets/${setId}/`, { title: editTitle.trim(), description: detail.description || "", status: detail.status, is_public: detail.is_public }); setEditing(false); fetchDetail(); };
  const deleteSet = async () => { if (!detail) return; if (!confirm(`Xoá bộ "${detail.title}"?`)) return; await adminDelete(`/crud/vocab/sets/${setId}/`); router.push("/admin/vocab/sets"); };

  const toggleSelect = (id: number) => setSelectedItems(prev => { const n = new Set(prev); n.has(id) ? n.delete(id) : n.add(id); return n; });
  const selectAll = () => { if (!detail) return; setSelectedItems(selectedItems.size === detail.items.length ? new Set() : new Set(detail.items.map(i => i.id))); };

  if (loading) return <div style={{ textAlign: "center", padding: 80 }}><Text type="secondary">Đang tải...</Text></div>;
  if (!detail) return <div style={{ textAlign: "center", padding: 80 }}><Text type="danger">Set không tồn tại</Text></div>;

  const allSelected = detail.items.length > 0 && selectedItems.size === detail.items.length;

  const columns: ColumnsType<SetDetail["items"][0]> = [
    { title: <Checkbox checked={allSelected} indeterminate={selectedItems.size > 0 && !allSelected} onChange={selectAll} />, key: "select", width: 40, render: (_, item) => <Checkbox checked={selectedItems.has(item.id)} onChange={() => toggleSelect(item.id)} /> },
    { title: "#", key: "order", width: 40, render: (_, __, i) => <Text type="secondary" style={{ fontSize: 11 }}>{i + 1}</Text> },
    { title: "Từ", dataIndex: "word", render: (w) => <Text strong>{w}</Text> },
    { title: "Nghĩa", dataIndex: "definition", ellipsis: true, render: (d) => <Text type="secondary" style={{ fontSize: 12 }}>{d}</Text> },
    { title: "POS", dataIndex: "part_of_speech", width: 70, render: (p) => <Tag color="processing" style={{ fontSize: 10 }}>{p || "—"}</Tag> },
    { title: "Quiz", dataIndex: "has_quiz", width: 50, render: (q) => q ? <Tag color="success">✓</Tag> : <Text type="secondary">—</Text> },
    { title: "", key: "actions", width: 40, render: (_, item) => <Button size="small" type="text" danger icon={<DeleteOutlined />} onClick={() => removeWord(item.id)} title="Xoá khỏi set" /> },
  ];

  return (
    <div>
      <Space orientation="vertical" size="large" style={{ width: "100%" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div style={{ flex: 1 }}>
            <Link href="/admin/vocab/sets" style={{ fontSize: 13, color: "var(--text-tertiary)" }}><ArrowLeftOutlined /> Bộ từ vựng</Link>
            {editing ? (
              <Space style={{ marginTop: 4 }}>
                <Input value={editTitle} onChange={(e) => setEditTitle(e.target.value)} style={{ fontSize: 18, fontWeight: 700, width: 300 }} autoFocus onPressEnter={saveTitle} />
                <Button onClick={saveTitle}>💾 Lưu</Button>
                <Button onClick={() => { setEditing(false); setEditTitle(detail.title); }}>Huỷ</Button>
              </Space>
            ) : (
              <Title level={3} style={{ margin: "4px 0", cursor: "pointer" }} onClick={() => setEditing(true)}>📂 {detail.title} <Text type="secondary" style={{ fontSize: 14 }}>✏️</Text></Title>
            )}
            <Space size="small">
              {detail.collection && <Tag color="processing">{detail.collection}</Tag>}
              {detail.toeic_level && <Tag color="warning">{detail.toeic_level}</Tag>}
              <Tag>{detail.status}</Tag>
              <Text type="secondary">{detail.word_count} từ</Text>
              <Text type="secondary">{detail.is_public ? "🌐 Công khai" : "🔒 Riêng tư"}</Text>
            </Space>
          </div>
          <Popconfirm title={`Xoá bộ "${detail.title}"?`} onConfirm={deleteSet} okText="Xoá" cancelText="Huỷ" okButtonProps={{ danger: true }}>
            <Button danger>🗑️ Xoá bộ</Button>
          </Popconfirm>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 340px", gap: 20, alignItems: "start" }}>
          <div>
            {selectedItems.size > 0 && (
              <Space style={{ marginBottom: 12 }}>
                <Text type="secondary">Đã chọn {selectedItems.size}/{detail.items.length}</Text>
                <Select placeholder="Chọn set đích..." value={moveTarget} onChange={setMoveTarget} style={{ width: 200 }} allowClear options={allSets.filter(s => s.id !== setId).map(s => ({ value: s.id, label: s.title }))} />
                <Button size="small" disabled={!moveTarget} onClick={moveSelected}>📦 Di chuyển</Button>
                <Button size="small" danger onClick={removeSelected}>🗑️ Xoá đã chọn</Button>
              </Space>
            )}
            <Table columns={columns} dataSource={detail.items} rowKey="id" size="small" pagination={false} rowClassName={(item) => selectedItems.has(item.id) ? "ant-table-row-selected" : ""} />
          </div>

          <div style={{ position: "sticky", top: 80, display: "flex", flexDirection: "column", gap: 16 }}>
            <div style={{ background: "var(--bg-surface, #fff)", borderRadius: 12, padding: 20, border: "1px solid var(--border-subtle, #e5e7eb)" }}>
              <Text strong>➕ Thêm từ vào set</Text>
              <Input.Search placeholder="Gõ từ cần thêm..." value={searchQ} onChange={(e) => setSearchQ(e.target.value)} loading={searching} style={{ marginTop: 8 }} />
              <div style={{ maxHeight: 400, overflowY: "auto", marginTop: 8 }}>
                {searchResults.length === 0 && searchQ.length >= 2 && !searching && <Text type="secondary" style={{ fontSize: 12, display: "block", textAlign: "center", padding: 12 }}>Không tìm thấy</Text>}
                {searchResults.map((r) => (
                  <div key={r.def_id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 0", borderBottom: "1px solid var(--border-subtle)" }}>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontWeight: 600, fontSize: 13 }}>{r.word} <Text type="secondary" style={{ fontSize: 11 }}>({r.pos})</Text></div>
                      <Text type="secondary" style={{ fontSize: 11 }} ellipsis>{r.meaning}</Text>
                    </div>
                    <Button size="small" type="primary" onClick={() => addWord(r.def_id)}>+ Thêm</Button>
                  </div>
                ))}
              </div>
            </div>
            <div style={{ fontSize: 12, color: "var(--text-secondary)" }}>
              <Text strong style={{ fontSize: 13 }}>💡 Hướng dẫn</Text>
              <ul style={{ margin: "4px 0 0", paddingLeft: 16, display: "flex", flexDirection: "column", gap: 2 }}>
                <li>Nhấn tiêu đề để <strong>đổi tên</strong></li>
                <li><strong>Tìm từ</strong> ở ô bên phải để thêm</li>
                <li><strong>Chọn nhiều từ</strong> rồi di chuyển/xoá hàng loạt</li>
              </ul>
            </div>
          </div>
        </div>
      </Space>
    </div>
  );
}
