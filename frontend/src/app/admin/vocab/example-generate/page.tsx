"use client";
import { useState, useEffect, useCallback } from "react";
import { Table, Card, Button, Input, Tag, Typography, Space, Spin, Progress, Tooltip, Collapse } from "antd";
import { ThunderboltOutlined, SearchOutlined, CheckCircleOutlined, ExperimentOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import { adminGet, adminPost } from "@/lib/admin-api";

const { Title, Text } = Typography;

interface VocabSet {
  id: number;
  title: string;
  collection: string | null;
  toeic_level: string | null;
}

interface SetItem {
  id: number;
  definition_id: number;
  word: string;
  reading: string;
  meaning: string;
  example_count: number;
  gemini_count: number;
  has_examples: boolean;
  usage: string;
  gemini_examples: { sentence: string; reading: string; meaning_en: string }[];
}

interface GenerateResult {
  status: string;
  word: string;
  saved_count: number;
  usage: string;
  examples: { sentence: string; translation: string }[];
  gemini_examples: { sentence: string; reading: string; meaning_en: string }[];
}

export default function ExampleGeneratePage() {
  const [sets, setSets] = useState<VocabSet[]>([]);
  const [selectedSet, setSelectedSet] = useState<number | null>(null);
  const [items, setItems] = useState<SetItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [setsLoading, setSetsLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [genProgress, setGenProgress] = useState({ done: 0, total: 0, current: "" });
  const [logs, setLogs] = useState<string[]>([]);
  const [searchSet, setSearchSet] = useState("");
  const [expandedWord, setExpandedWord] = useState<string | null>(null);
  const [previewData, setPreviewData] = useState<Record<string, GenerateResult>>({});

  useEffect(() => {
    setSetsLoading(true);
    adminGet<VocabSet[]>("/crud/vocab/sets-simple/")
      .then((data) => {
        if (Array.isArray(data)) setSets(data);
        else if ((data as unknown as { items: VocabSet[] })?.items) setSets((data as unknown as { items: VocabSet[] }).items);
        else setSets([]);
      })
      .catch(() => setSets([]))
      .finally(() => setSetsLoading(false));
  }, []);

  const loadSet = useCallback((setId: number) => {
    setSelectedSet(setId);
    setLoading(true);
    setPreviewData({});
    adminGet<{ items: SetItem[] }>(`/crud/vocab/example/load-set/?set_id=${setId}`)
      .then((d) => setItems(d.items || []))
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, []);

  const needsExamples = items.filter((i) => i.gemini_count === 0);
  const hasExamples = items.filter((i) => i.gemini_count > 0);

  const generateSingle = async (item: SetItem) => {
    setLogs((prev) => [...prev, `⏳ ${item.word}...`]);
    try {
      const res = await adminPost<GenerateResult>("/crud/vocab/example/generate/", {
        definition_id: item.definition_id,
      });
      if (res.status === "success") {
        setLogs((prev) => [...prev, `✅ ${item.word}: ${res.saved_count} ví dụ`]);
        setPreviewData((prev) => ({ ...prev, [item.word]: res }));
        return true;
      } else {
        setLogs((prev) => [...prev, `❌ ${item.word}: ${res.message || "Failed"}`]);
        return false;
      }
    } catch (err) {
      setLogs((prev) => [...prev, `❌ ${item.word}: ${String(err)}`]);
      return false;
    }
  };

  const generateAll = async () => {
    if (needsExamples.length === 0) return;
    setGenerating(true);
    setGenProgress({ done: 0, total: needsExamples.length, current: "" });
    setLogs([]);
    for (let i = 0; i < needsExamples.length; i++) {
      setGenProgress({ done: i, total: needsExamples.length, current: needsExamples[i].word });
      await generateSingle(needsExamples[i]);
      // Small delay to avoid rate limiting
      await new Promise((r) => setTimeout(r, 1200));
    }
    setGenProgress({ done: needsExamples.length, total: needsExamples.length, current: "Done!" });
    setGenerating(false);
    if (selectedSet) loadSet(selectedSet);
  };

  const filteredSets = searchSet
    ? sets.filter((s) => s.title.toLowerCase().includes(searchSet.toLowerCase()))
    : sets;

  const columns: ColumnsType<SetItem> = [
    {
      title: "#",
      key: "idx",
      width: 40,
      render: (_, __, i) => <Text type="secondary" style={{ fontSize: 11 }}>{i + 1}</Text>,
    },
    {
      title: "Từ",
      dataIndex: "word",
      width: 120,
      render: (w: string) => (
        <Text strong style={{ fontFamily: "'Noto Sans JP', sans-serif", fontSize: 15 }}>{w}</Text>
      ),
    },
    {
      title: "Reading",
      dataIndex: "reading",
      width: 120,
      render: (r: string) => (
        <Text type="secondary" style={{ fontSize: 12, fontFamily: "'Noto Sans JP', sans-serif" }}>{r || "—"}</Text>
      ),
    },
    {
      title: "Nghĩa",
      dataIndex: "meaning",
      ellipsis: true,
      render: (m: string) => <Text style={{ fontSize: 13 }}>{m}</Text>,
    },
    {
      title: "Ví dụ",
      key: "examples",
      width: 90,
      render: (_, item) => {
        if (item.gemini_count > 0) {
          return <Tag color="success" icon={<CheckCircleOutlined />}>{item.gemini_count} AI</Tag>;
        }
        if (item.example_count > 0) {
          return <Tag color="blue">{item.example_count}</Tag>;
        }
        return <Tag color="warning">—</Tag>;
      },
    },
    {
      title: "",
      key: "gen",
      width: 50,
      render: (_, item) =>
        !generating ? (
          <Tooltip title="Sinh ví dụ bằng AI">
            <Button
              size="small"
              type="text"
              icon={<ThunderboltOutlined />}
              onClick={() => generateSingle(item)}
            />
          </Tooltip>
        ) : null,
    },
  ];

  return (
    <div>
      <Space direction="vertical" size="large" style={{ width: "100%" }}>
        <div>
          <Title level={3} style={{ margin: 0 }}>
            <ExperimentOutlined /> Sinh ví dụ JP (Gemini)
          </Title>
          <Text type="secondary">
            Tự động sinh câu ví dụ tiếng Nhật với furigana, dịch VI/EN — {sets.length} sets
          </Text>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: 20 }}>
          {/* Left: Set selector */}
          <Card title="Chọn Set" size="small" style={{ height: "fit-content" }}>
            <Input
              placeholder="Tìm set..."
              value={searchSet}
              onChange={(e) => setSearchSet(e.target.value)}
              prefix={<SearchOutlined />}
              size="small"
              style={{ marginBottom: 8 }}
            />
            <div style={{ maxHeight: 500, overflowY: "auto" }}>
              {setsLoading ? (
                <div style={{ textAlign: "center", padding: 20 }}><Spin /></div>
              ) : filteredSets.length === 0 ? (
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {sets.length === 0 ? "⚠️ Không có set" : "Không tìm thấy"}
                </Text>
              ) : (
                filteredSets.map((s) => (
                  <div
                    key={s.id}
                    onClick={() => loadSet(s.id)}
                    style={{
                      padding: "8px 12px",
                      cursor: "pointer",
                      borderRadius: 8,
                      marginBottom: 2,
                      background: selectedSet === s.id ? "var(--ant-color-primary, #1677ff)" : "transparent",
                      color: selectedSet === s.id ? "white" : "inherit",
                      fontSize: 13,
                      transition: "all 0.15s",
                    }}
                  >
                    <div style={{ fontWeight: 500 }}>{s.title}</div>
                    {(s.collection || s.toeic_level) && (
                      <div style={{ fontSize: 10, opacity: 0.6 }}>
                        {s.collection}
                        {s.toeic_level && ` · ${s.toeic_level}`}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </Card>

          {/* Right: Items + generate */}
          <Card size="small">
            {!selectedSet ? (
              <div style={{ textAlign: "center", padding: 40 }}>
                <Text type="secondary">👈 Chọn một Set bên trái</Text>
              </div>
            ) : loading ? (
              <div style={{ textAlign: "center", padding: 40 }}>
                <Spin size="large" />
              </div>
            ) : items.length === 0 ? (
              <div style={{ textAlign: "center", padding: 40 }}>
                <Text type="secondary">Set trống</Text>
              </div>
            ) : (
              <>
                {/* Stats + generate all button */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
                  <Space size="small">
                    <Tag color="success">✓ {hasExamples.length} có ví dụ AI</Tag>
                    <Tag color="warning">⚡ {needsExamples.length} cần tạo</Tag>
                    <Text type="secondary" style={{ fontSize: 11 }}>Tổng: {items.length}</Text>
                  </Space>
                  <Button
                    type="primary"
                    icon={<ThunderboltOutlined />}
                    onClick={generateAll}
                    disabled={generating || needsExamples.length === 0}
                    loading={generating}
                  >
                    {generating
                      ? `${genProgress.done}/${genProgress.total}`
                      : `Sinh ${needsExamples.length} ví dụ`}
                  </Button>
                </div>

                {/* Progress bar */}
                {generating && (
                  <Progress
                    percent={Math.round((genProgress.done / genProgress.total) * 100)}
                    status="active"
                    strokeColor={{ from: "#6366f1", to: "#10B981" }}
                    size="small"
                    style={{ marginBottom: 8 }}
                  />
                )}

                {/* Log output */}
                {logs.length > 0 && (
                  <div
                    style={{
                      maxHeight: 140,
                      overflowY: "auto",
                      background: "var(--bg-app, #f9fafb)",
                      borderRadius: 8,
                      padding: 8,
                      marginBottom: 12,
                      fontSize: 11,
                      fontFamily: "monospace",
                    }}
                  >
                    {logs.map((l, i) => (
                      <div key={i} style={{ padding: "2px 0" }}>{l}</div>
                    ))}
                  </div>
                )}

                {/* Table */}
                <Table<SetItem>
                  columns={columns}
                  dataSource={items}
                  rowKey="id"
                  size="small"
                  pagination={false}
                  expandable={{
                    expandedRowKeys: expandedWord ? [expandedWord] : [],
                    onExpand: (expanded, record) => setExpandedWord(expanded ? String(record.id) : null),
                    expandedRowRender: (record) => {
                      const preview = previewData[record.word];
                      const geminiExamples = preview?.gemini_examples || record.gemini_examples || [];
                      const usage = preview?.usage || record.usage;

                      if (!usage && geminiExamples.length === 0 && !preview) {
                        return <Text type="secondary" style={{ fontSize: 12 }}>Chưa có ví dụ AI. Nhấn ⚡ để sinh.</Text>;
                      }

                      return (
                        <div style={{ padding: "4px 0" }}>
                          {usage && (
                            <div style={{ marginBottom: 8 }}>
                              <Text strong style={{ fontSize: 12, color: "#6366f1" }}>Cách dùng:</Text>
                              <div style={{ fontSize: 13, marginTop: 2 }}>{usage}</div>
                            </div>
                          )}
                          {geminiExamples.length > 0 && (
                            <div>
                              <Text strong style={{ fontSize: 12, color: "#6366f1" }}>Ví dụ:</Text>
                              {geminiExamples.map((ex, i) => (
                                <div key={i} style={{ marginTop: 6, padding: "6px 10px", background: "#f8f9fa", borderRadius: 6, borderLeft: "3px solid #6366f1" }}>
                                  <div style={{ fontFamily: "'Noto Sans JP', sans-serif", fontSize: 15, fontWeight: 500 }}>
                                    {ex.sentence}
                                  </div>
                                  <div style={{ fontFamily: "'Noto Sans JP', sans-serif", fontSize: 13, color: "#6366f1" }}>
                                    {ex.reading}
                                  </div>
                                  {ex.meaning_en && (
                                    <div style={{ fontSize: 12, color: "#64748b", marginTop: 2 }}>
                                      {ex.meaning_en}
                                    </div>
                                  )}
                                </div>
                              ))}
                            </div>
                          )}
                          {preview?.examples && preview.examples.length > 0 && geminiExamples.length === 0 && (
                            <div>
                              <Text strong style={{ fontSize: 12, color: "#6366f1" }}>Ví dụ (DB):</Text>
                              {preview.examples.map((ex, i) => (
                                <div key={i} style={{ marginTop: 4, fontSize: 13 }}>
                                  <div>{ex.sentence}</div>
                                  <div style={{ color: "#64748b", fontSize: 12 }}>{ex.translation}</div>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      );
                    },
                    rowExpandable: () => true,
                  }}
                />
              </>
            )}
          </Card>
        </div>
      </Space>
    </div>
  );
}
