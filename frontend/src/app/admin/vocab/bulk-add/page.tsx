"use client";
import { useState, useEffect, useRef, useCallback } from "react";
import { Card, Button, Input, Select, InputNumber, Tag, Typography, Space, Progress } from "antd";
import { ThunderboltOutlined, StopOutlined } from "@ant-design/icons";
import { adminGet, adminPost } from "@/lib/admin-api";

const { Title, Text } = Typography;
const { TextArea } = Input;

interface VocabSet { id: number; title: string; collection: string | null; toeic_level: string | null; }
interface WordResult { word: string; status: "pending" | "processing" | "success" | "error" | "skipped"; message?: string; definitions?: number; reused?: boolean; }

export default function BulkAddToolPage() {
  const [wordInput, setWordInput] = useState("");
  const [queue, setQueue] = useState<WordResult[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [sets, setSets] = useState<VocabSet[]>([]);
  const [selectedSet, setSelectedSet] = useState<number | null>(null);
  const [limit, setLimit] = useState(0);
  const abortRef = useRef(false);
  const logRef = useRef<HTMLDivElement>(null);

  useEffect(() => { adminGet<VocabSet[]>("/crud/vocab/sets-simple/").then(setSets).catch(() => setSets([])); }, []);

  const startBulk = useCallback(async () => {
    const words = wordInput.split("\n").map((w) => w.trim().toLowerCase()).filter((w) => w.length > 0);
    const unique = [...new Set(words)]; if (unique.length === 0) return;
    const initial: WordResult[] = unique.map((w) => ({ word: w, status: "pending" }));
    setQueue(initial); setIsRunning(true); abortRef.current = false;

    for (let i = 0; i < unique.length; i++) {
      if (abortRef.current) break;
      setQueue((prev) => prev.map((item, idx) => idx === i ? { ...item, status: "processing" } : item));
      try {
        const res = await adminPost<{ status: string; message: string; word: string; definitions?: number; reused?: boolean }>("/crud/vocab/bulk-process/", { word: unique[i], limit, set_id: selectedSet });
        setQueue((prev) => prev.map((item, idx) => idx === i ? { ...item, status: res.status === "success" ? "success" : "error", message: res.message, definitions: res.definitions, reused: res.reused } : item));
      } catch (err) { setQueue((prev) => prev.map((item, idx) => idx === i ? { ...item, status: "error", message: String(err) } : item)); }
      if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
      await new Promise((r) => setTimeout(r, 300));
    }
    setIsRunning(false);
  }, [wordInput, limit, selectedSet]);

  const stopBulk = () => { abortRef.current = true; };

  const stats = {
    total: queue.length, success: queue.filter((w) => w.status === "success").length,
    error: queue.filter((w) => w.status === "error").length,
    pending: queue.filter((w) => w.status === "pending" || w.status === "processing").length,
  };
  const progress = stats.total > 0 ? ((stats.success + stats.error) / stats.total) * 100 : 0;
  const wordCount = wordInput.split("\n").filter((w) => w.trim()).length;

  return (
    <div>
      <Space orientation="vertical" size="large" style={{ width: "100%" }}>
        <div><Title level={3} style={{ margin: 0 }}>⚡ Bulk Add Vocabulary</Title><Text type="secondary">Paste word list → scrape Cambridge Dictionary → save to DB</Text></div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
          <Card title="Danh sách từ" size="small">
            <Space orientation="vertical" style={{ width: "100%" }} size="middle">
              <TextArea value={wordInput} onChange={(e) => setWordInput(e.target.value)} placeholder={"abandon\nability\nabsolute\nabsorb\nabstract"} disabled={isRunning} rows={10} style={{ fontFamily: "monospace", fontSize: 13 }} />
              <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                <div style={{ flex: 1, minWidth: 200 }}>
                  <Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Thêm vào Set</Text>
                  <Select value={selectedSet} onChange={setSelectedSet} placeholder="— Không chọn —" allowClear disabled={isRunning} style={{ width: "100%" }}
                    options={sets.map(s => ({ value: s.id, label: `${s.title}${s.collection ? ` (${s.collection})` : ""}` }))} />
                </div>
                <div style={{ width: 120 }}>
                  <Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Giới hạn</Text>
                  <InputNumber value={limit} onChange={(v) => setLimit(v || 0)} disabled={isRunning} min={0} max={10} style={{ width: "100%" }} />
                  <Text type="secondary" style={{ fontSize: 10 }}>0 = tất cả</Text>
                </div>
              </div>
              <Space>
                {!isRunning ? (
                  <Button type="primary" icon={<ThunderboltOutlined />} onClick={startBulk} disabled={!wordInput.trim()}>Bắt đầu ({wordCount} từ)</Button>
                ) : (
                  <Button danger icon={<StopOutlined />} onClick={stopBulk}>Dừng</Button>
                )}
              </Space>
            </Space>
          </Card>

          <Card title="Tiến độ" size="small">
            {queue.length > 0 ? (
              <>
                <div style={{ marginBottom: 16 }}>
                  <Space size="small" style={{ marginBottom: 8 }}>
                    <Tag color="success">✅ {stats.success}</Tag>
                    <Tag color="error">❌ {stats.error}</Tag>
                    <Tag>⏳ {stats.pending}</Tag>
                  </Space>
                  <Progress percent={Math.round(progress)} status={isRunning ? "active" : undefined} strokeColor={{ from: "#10B981", to: "#06B6D4" }} />
                </div>
                <div ref={logRef} style={{ maxHeight: 400, overflowY: "auto", borderRadius: 8, border: "1px solid var(--border-subtle, #e5e7eb)", background: "var(--bg-app, #f9fafb)" }}>
                  {queue.map((item, i) => (
                    <div key={i} style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 12px", borderBottom: "1px solid var(--border-subtle, #e5e7eb)", fontSize: 13, opacity: item.status === "pending" ? 0.4 : 1 }}>
                      <span style={{ width: 20, textAlign: "center" }}>
                        {item.status === "pending" && "⏳"}{item.status === "processing" && "🔄"}{item.status === "success" && "✅"}{item.status === "error" && "❌"}
                      </span>
                      <Text strong style={{ minWidth: 100 }}>{item.word}</Text>
                      <span style={{ flex: 1, fontSize: 12, color: item.status === "error" ? "#ef4444" : "var(--text-tertiary)" }}>
                        {item.message || ""}{item.reused && <Tag color="processing" style={{ marginLeft: 4, fontSize: 10 }}>reused</Tag>}
                      </span>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div style={{ textAlign: "center", padding: 40 }}><Text type="secondary">📝 Nhập danh sách từ bên trái và nhấn Bắt đầu</Text></div>
            )}
          </Card>
        </div>
      </Space>
    </div>
  );
}
