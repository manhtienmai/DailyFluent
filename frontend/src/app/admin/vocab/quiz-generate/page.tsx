"use client";
import { useState, useEffect, useCallback } from "react";
import { Table, Card, Button, Input, Tag, Typography, Space, Spin, Progress } from "antd";
import { ThunderboltOutlined, SearchOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import { adminGet, adminPost } from "@/lib/admin-api";

const { Title, Text } = Typography;

interface VocabSet { id: number; title: string; collection: string | null; toeic_level: string | null; }
interface SetItem { id: number; word: string; reading: string; definition: string; has_quiz: boolean; quiz_types: string[]; }

export default function QuizGeneratePage() {
  const [sets, setSets] = useState<VocabSet[]>([]);
  const [selectedSet, setSelectedSet] = useState<number | null>(null);
  const [items, setItems] = useState<SetItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [setsLoading, setSetsLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [genProgress, setGenProgress] = useState({ done: 0, total: 0, current: "" });
  const [logs, setLogs] = useState<string[]>([]);
  const [searchSet, setSearchSet] = useState("");

  useEffect(() => {
    setSetsLoading(true);
    adminGet<VocabSet[]>("/crud/vocab/sets-simple/")
      .then(data => { if (Array.isArray(data)) setSets(data); else if ((data as any)?.items) setSets((data as any).items); else setSets([]); })
      .catch(() => setSets([])).finally(() => setSetsLoading(false));
  }, []);

  const loadSet = useCallback((setId: number) => {
    setSelectedSet(setId); setLoading(true);
    adminGet<{ items: SetItem[] }>(`/crud/vocab/quiz/load-set/?set_id=${setId}`)
      .then(d => setItems(d.items || [])).catch(() => setItems([])).finally(() => setLoading(false));
  }, []);

  const needsQuiz = items.filter(i => !i.has_quiz);
  const hasQuiz = items.filter(i => i.has_quiz);

  const generateSingle = async (item: SetItem) => {
    setLogs(prev => [...prev, `⏳ ${item.word}...`]);
    try {
      const res = await adminPost<{ status: string; message?: string }>("/crud/vocab/quiz/generate/", { set_item_id: item.id });
      setLogs(prev => [...prev, res.status === "success" ? `✅ ${item.word}: ${res.message || "OK"}` : `❌ ${item.word}: ${res.message || "Failed"}`]);
    } catch (err) { setLogs(prev => [...prev, `❌ ${item.word}: ${String(err)}`]); }
  };

  const generateAll = async () => {
    if (needsQuiz.length === 0) return;
    setGenerating(true); setGenProgress({ done: 0, total: needsQuiz.length, current: "" }); setLogs([]);
    for (let i = 0; i < needsQuiz.length; i++) {
      setGenProgress({ done: i, total: needsQuiz.length, current: needsQuiz[i].word });
      await generateSingle(needsQuiz[i]);
      await new Promise(r => setTimeout(r, 800));
    }
    setGenProgress({ done: needsQuiz.length, total: needsQuiz.length, current: "Done!" });
    setGenerating(false);
    if (selectedSet) loadSet(selectedSet);
  };

  const filteredSets = searchSet ? sets.filter(s => s.title.toLowerCase().includes(searchSet.toLowerCase())) : sets;

  const columns: ColumnsType<SetItem> = [
    { title: "#", key: "idx", width: 40, render: (_, __, i) => <Text type="secondary" style={{ fontSize: 11 }}>{i + 1}</Text> },
    { title: "Từ", dataIndex: "word", render: (w) => <Text strong style={{ fontFamily: "'Noto Sans JP', sans-serif" }}>{w}</Text> },
    { title: "Reading", dataIndex: "reading", width: 120, render: (r) => <Text type="secondary" style={{ fontSize: 12, fontFamily: "'Noto Sans JP', sans-serif" }}>{r || "—"}</Text> },
    { title: "Nghĩa", dataIndex: "definition", ellipsis: true },
    { title: "Quiz", dataIndex: "has_quiz", width: 80, render: (q, item) => q ? <Tag color="success">✓ {item.quiz_types?.length || ""}</Tag> : <Tag color="warning">—</Tag> },
    {
      title: "", key: "gen", width: 50,
      render: (_, item) => !item.has_quiz && !generating ? <Button size="small" type="text" icon={<ThunderboltOutlined />} onClick={() => generateSingle(item)} /> : null,
    },
  ];

  return (
    <div>
      <Space orientation="vertical" size="large" style={{ width: "100%" }}>
        <div><Title level={3} style={{ margin: 0 }}>🧩 Quiz Generator</Title><Text type="secondary">Tạo distractors bằng AI (Gemini) — {sets.length} sets</Text></div>
        <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: 20 }}>
          <Card title="Chọn Set" size="small" style={{ height: "fit-content" }}>
            <Input placeholder="Tìm set..." value={searchSet} onChange={e => setSearchSet(e.target.value)} prefix={<SearchOutlined />} size="small" style={{ marginBottom: 8 }} />
            <div style={{ maxHeight: 450, overflowY: "auto" }}>
              {setsLoading ? <div style={{ textAlign: "center", padding: 20 }}><Spin /></div> : filteredSets.length === 0 ? (
                <Text type="secondary" style={{ fontSize: 12 }}>{sets.length === 0 ? "⚠️ Không có set" : "Không tìm thấy"}</Text>
              ) : filteredSets.map(s => (
                <div key={s.id} onClick={() => loadSet(s.id)} style={{ padding: "8px 12px", cursor: "pointer", borderRadius: 8, marginBottom: 2, background: selectedSet === s.id ? "var(--ant-color-primary, #1677ff)" : "transparent", color: selectedSet === s.id ? "white" : "inherit", fontSize: 13, transition: "all 0.15s" }}>
                  <div style={{ fontWeight: 500 }}>{s.title}</div>
                  {(s.collection || s.toeic_level) && <div style={{ fontSize: 10, opacity: 0.6 }}>{s.collection}{s.toeic_level && ` · ${s.toeic_level}`}</div>}
                </div>
              ))}
            </div>
          </Card>

          <Card size="small">
            {!selectedSet ? (
              <div style={{ textAlign: "center", padding: 40 }}><Text type="secondary">👈 Chọn một Set bên trái</Text></div>
            ) : loading ? (
              <div style={{ textAlign: "center", padding: 40 }}><Spin size="large" /></div>
            ) : items.length === 0 ? (
              <div style={{ textAlign: "center", padding: 40 }}><Text type="secondary">Set trống</Text></div>
            ) : (
              <>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
                  <Space size="small">
                    <Tag color="success">✓ {hasQuiz.length} có quiz</Tag>
                    <Tag color="warning">⚡ {needsQuiz.length} cần tạo</Tag>
                    <Text type="secondary" style={{ fontSize: 11 }}>Tổng: {items.length}</Text>
                  </Space>
                  <Button type="primary" icon={<ThunderboltOutlined />} onClick={generateAll} disabled={generating || needsQuiz.length === 0} loading={generating}>
                    {generating ? `${genProgress.done}/${genProgress.total}` : `Generate ${needsQuiz.length} quiz`}
                  </Button>
                </div>
                {generating && <Progress percent={Math.round((genProgress.done / genProgress.total) * 100)} status="active" strokeColor={{ from: "#F59E0B", to: "#10B981" }} size="small" style={{ marginBottom: 8 }} />}
                {logs.length > 0 && (
                  <div style={{ maxHeight: 120, overflowY: "auto", background: "var(--bg-app, #f9fafb)", borderRadius: 8, padding: 8, marginBottom: 12, fontSize: 11, fontFamily: "monospace" }}>
                    {logs.map((l, i) => <div key={i} style={{ padding: "2px 0" }}>{l}</div>)}
                  </div>
                )}
                <Table<SetItem> columns={columns} dataSource={items} rowKey="id" size="small" pagination={false} />
              </>
            )}
          </Card>
        </div>
      </Space>
    </div>
  );
}
