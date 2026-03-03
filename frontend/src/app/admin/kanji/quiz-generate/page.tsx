"use client";
import { useState, useEffect, useCallback } from "react";
import { Table, Card, Button, Input, Tag, Segmented, Typography, Space, Spin, Progress } from "antd";
import { ThunderboltOutlined, SearchOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import { adminGet, adminPost } from "@/lib/admin-api";

const { Title, Text } = Typography;

interface KanjiLesson { id: number; title: string; level: string; lesson_number: number; order: number; kanji_count: number; }
interface KanjiItem { id: number; char: string; sino_vi: string; meaning_vi: string; onyomi: string; kunyomi: string; has_quiz: boolean; quiz_types: string[]; }
const JLPT_LEVELS = ["N5", "N4", "N3", "N2", "N1"];

export default function KanjiQuizGeneratePage() {
  const [lessons, setLessons] = useState<KanjiLesson[]>([]);
  const [selectedLevel, setSelectedLevel] = useState("N5");
  const [selectedLesson, setSelectedLesson] = useState<number | null>(null);
  const [items, setItems] = useState<KanjiItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [lessonsLoading, setLessonsLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [genProgress, setGenProgress] = useState({ done: 0, total: 0, current: "" });
  const [logs, setLogs] = useState<string[]>([]);

  useEffect(() => {
    setLessonsLoading(true);
    adminGet<KanjiLesson[]>("/crud/kanji/lessons/")
      .then(data => setLessons(Array.isArray(data) ? data : (data as any)?.items || []))
      .catch(() => setLessons([])).finally(() => setLessonsLoading(false));
  }, []);

  const filteredLessons = lessons.filter(l => l.level === selectedLevel);

  const loadLesson = useCallback((lessonId: number) => {
    setSelectedLesson(lessonId); setLoading(true); setLogs([]);
    adminGet<{ items: KanjiItem[] }>(`/crud/kanji/quiz/load-lesson/?lesson_id=${lessonId}`)
      .then(d => setItems(d.items || [])).catch(() => setItems([])).finally(() => setLoading(false));
  }, []);

  const needsQuiz = items.filter(i => !i.has_quiz);
  const hasQuiz = items.filter(i => i.has_quiz);

  const generateSingle = async (item: KanjiItem) => {
    setLogs(prev => [...prev, `⏳ ${item.char} (${item.sino_vi})...`]);
    try {
      const res = await adminPost<{ status: string; message?: string }>("/crud/kanji/quiz/generate/", { kanji_id: item.id });
      setLogs(prev => [...prev, res.status === "success" ? `✅ ${item.char}: ${res.message || "OK"}` : `❌ ${item.char}: ${res.message || "Failed"}`]);
    } catch (err) { setLogs(prev => [...prev, `❌ ${item.char}: ${String(err)}`]); }
  };

  const generateAll = async () => {
    if (needsQuiz.length === 0) return;
    setGenerating(true); setGenProgress({ done: 0, total: needsQuiz.length, current: "" }); setLogs([]);
    for (let i = 0; i < needsQuiz.length; i++) {
      setGenProgress({ done: i, total: needsQuiz.length, current: needsQuiz[i].char });
      await generateSingle(needsQuiz[i]); await new Promise(r => setTimeout(r, 800));
    }
    setGenProgress({ done: needsQuiz.length, total: needsQuiz.length, current: "Done!" });
    setGenerating(false); if (selectedLesson) loadLesson(selectedLesson);
  };

  const columns: ColumnsType<KanjiItem> = [
    { title: "#", key: "idx", width: 40, render: (_, __, i) => <Text type="secondary" style={{ fontSize: 11 }}>{i + 1}</Text> },
    { title: "Kanji", dataIndex: "char", width: 60, render: (c) => <Text strong style={{ fontSize: 22, fontFamily: "'Noto Sans JP', sans-serif" }}>{c}</Text> },
    { title: "Hán Việt", dataIndex: "sino_vi", width: 100 },
    { title: "Nghĩa", dataIndex: "meaning_vi", ellipsis: true },
    { title: "Âm On", dataIndex: "onyomi", width: 100, render: (o) => <Text type="secondary" style={{ fontSize: 12, fontFamily: "'Noto Sans JP', sans-serif" }}>{o || "—"}</Text> },
    { title: "Âm Kun", dataIndex: "kunyomi", width: 100, render: (k) => <Text type="secondary" style={{ fontSize: 12, fontFamily: "'Noto Sans JP', sans-serif" }}>{k || "—"}</Text> },
    { title: "Quiz", dataIndex: "has_quiz", width: 80, render: (q, item) => q ? <Tag color="success">✓ {item.quiz_types?.length || ""}</Tag> : <Tag color="warning">—</Tag> },
    { title: "", key: "gen", width: 50, render: (_, item) => !item.has_quiz && !generating ? <Button size="small" type="text" icon={<ThunderboltOutlined />} onClick={() => generateSingle(item)} /> : null },
  ];

  return (
    <div>
      <Space orientation="vertical" size="large" style={{ width: "100%" }}>
        <div><Title level={3} style={{ margin: 0 }}>🀄 Kanji Quiz Generator</Title><Text type="secondary">Tạo đáp án nhiễu bằng AI (Gemini)</Text></div>
        <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: 20 }}>
          <Card title="Chọn Level & Bài" size="small" style={{ height: "fit-content" }}>
            <Segmented options={JLPT_LEVELS} value={selectedLevel} onChange={(v) => { setSelectedLevel(v as string); setSelectedLesson(null); setItems([]); }} block style={{ marginBottom: 12 }} />
            <div style={{ maxHeight: 400, overflowY: "auto" }}>
              {lessonsLoading ? <div style={{ textAlign: "center", padding: 20 }}><Spin /></div> : filteredLessons.length === 0 ? (
                <Text type="secondary" style={{ fontSize: 12 }}>Chưa có bài học cho {selectedLevel}</Text>
              ) : filteredLessons.map(l => (
                <div key={l.id} onClick={() => loadLesson(l.id)} style={{ padding: "8px 12px", cursor: "pointer", borderRadius: 8, marginBottom: 2, background: selectedLesson === l.id ? "var(--ant-color-primary, #1677ff)" : "transparent", color: selectedLesson === l.id ? "white" : "inherit", fontSize: 13, transition: "all 0.15s" }}>
                  <div style={{ fontWeight: 500 }}>Bài {l.lesson_number}: {l.title}</div>
                  <div style={{ fontSize: 10, opacity: 0.6 }}>{l.kanji_count} chữ Kanji</div>
                </div>
              ))}
            </div>
          </Card>

          <Card size="small">
            {!selectedLesson ? (
              <div style={{ textAlign: "center", padding: 40 }}><Text type="secondary">👈 Chọn một bài học bên trái</Text></div>
            ) : loading ? (
              <div style={{ textAlign: "center", padding: 40 }}><Spin size="large" /></div>
            ) : items.length === 0 ? (
              <div style={{ textAlign: "center", padding: 40 }}><Text type="secondary">Bài học trống</Text></div>
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
                <Table<KanjiItem> columns={columns} dataSource={items} rowKey="id" size="small" pagination={false} />
              </>
            )}
          </Card>
        </div>
      </Space>
    </div>
  );
}
