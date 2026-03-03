"use client";
import { useState, useEffect } from "react";
import { Card, Button, Input, Tag, Typography, Space, Spin, Badge, Segmented } from "antd";
import { PlusOutlined, SoundOutlined } from "@ant-design/icons";
import { adminGet, adminPost } from "@/lib/admin-api";

const { Title, Text } = Typography;

interface Book { id: number; title: string; level: string; category: string; total_lessons: number; }
interface Choice { key: string; text: string; text_vi?: string; }
interface TranscriptLine { speaker?: string; text: string; text_vi?: string; }
interface QuestionData { id?: number; mondai: string; order: number; order_in_mondai: number; text: string; text_vi?: string; correct_answer: string; choices: Choice[]; image_url?: string; audio_url?: string; transcript_data?: { lines?: TranscriptLine[] }; explanation_vi?: string; }
interface MondaiGroup { mondai: string; count: number; }

const MONDAI_LABELS: Record<string, string> = {
  "1": "もんだい1 課題理解", "2": "もんだい2 ポイント理解", "3": "もんだい3 概要理解",
  "4": "もんだい4 発話表現", "5": "もんだい5 即時応答",
  "01": "もんだい1 課題理解", "02": "もんだい2 ポイント理解", "03": "もんだい3 概要理解",
  "04": "もんだい4 発話表現", "05": "もんだい5 即時応答",
};
const MONDAI_COLORS = ["#6366f1", "#0ea5e9", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"];

export default function ChoukaiToolPage() {
  const [books, setBooks] = useState<Book[]>([]);
  const [selectedBook, setSelectedBook] = useState<Book | null>(null);
  const [questions, setQuestions] = useState<QuestionData[]>([]);
  const [mondaiGroups, setMondaiGroups] = useState<MondaiGroup[]>([]);
  const [totalQ, setTotalQ] = useState(0);
  const [activeMondai, setActiveMondai] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [newBookTitle, setNewBookTitle] = useState("");
  const [creating, setCreating] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);

  useEffect(() => {
    adminGet<{ items: Book[] }>("/crud/exam/books/")
      .then(d => setBooks((d.items || []).filter(b => b.category.toUpperCase() === "CHOUKAI")))
      .catch(() => setBooks([]));
  }, []);

  const loadQuestions = (book: Book) => {
    setSelectedBook(book); setLoading(true);
    adminGet<{ questions: QuestionData[]; mondai_groups: MondaiGroup[]; total: number }>(`/crud/choukai/load-questions/?book_id=${book.id}`)
      .then(d => { setQuestions(d.questions || []); setMondaiGroups(d.mondai_groups || []); setTotalQ(d.total || 0); if (d.mondai_groups?.length) setActiveMondai(d.mondai_groups[0].mondai); setLogs(prev => [...prev, `📚 Loaded ${d.total} questions from "${book.title}"`]); })
      .catch(err => { setQuestions([]); setMondaiGroups([]); setTotalQ(0); setLogs(prev => [...prev, `❌ Error: ${err}`]); })
      .finally(() => setLoading(false));
  };

  const createBook = async () => {
    if (!newBookTitle.trim()) return; setCreating(true);
    try {
      const res = await adminPost<{ success: boolean; id: number }>("/crud/choukai/create-book/", { title: newBookTitle, category: "CHOUKAI" });
      if (res.success) { const nb = { id: res.id, title: newBookTitle, level: "N2", category: "CHOUKAI", total_lessons: 0 }; setBooks(prev => [nb, ...prev]); setNewBookTitle(""); loadQuestions(nb); }
    } catch {} finally { setCreating(false); }
  };

  const activeQuestions = questions.filter(q => q.mondai === activeMondai);
  const mondaiIdx = mondaiGroups.findIndex(g => g.mondai === activeMondai);

  return (
    <div>
      <Space orientation="vertical" size="large" style={{ width: "100%" }}>
        <div><Title level={3} style={{ margin: 0 }}>🎧 Choukai Tool</Title><Text type="secondary">Editor toàn diện cho bài nghe hiểu</Text></div>
        <div style={{ display: "grid", gridTemplateColumns: "260px 1fr", gap: 16 }}>
          <Space orientation="vertical" size="middle" style={{ width: "100%" }}>
            <Card title="📚 Sách Choukai" size="small">
              <div style={{ display: "flex", gap: 4, marginBottom: 12 }}>
                <Input size="small" value={newBookTitle} onChange={e => setNewBookTitle(e.target.value)} placeholder="Tên sách mới..." onPressEnter={createBook} />
                <Button size="small" icon={<PlusOutlined />} onClick={createBook} loading={creating} />
              </div>
              {books.length === 0 && <Text type="secondary" style={{ fontSize: 12 }}>Chưa có sách choukai</Text>}
              <div style={{ maxHeight: 350, overflowY: "auto" }}>
                {books.map(b => (
                  <div key={b.id} onClick={() => loadQuestions(b)} style={{ padding: "8px 12px", cursor: "pointer", borderRadius: 8, marginBottom: 2, fontSize: 12, background: selectedBook?.id === b.id ? "var(--ant-color-primary, #1677ff)" : "transparent", color: selectedBook?.id === b.id ? "white" : "inherit", fontWeight: selectedBook?.id === b.id ? 600 : 400, transition: "all 0.15s" }}>
                    <div>{b.title}</div>
                    <div style={{ fontSize: 10, opacity: 0.7, marginTop: 2 }}>{b.level}{b.total_lessons > 0 ? ` · ${b.total_lessons} bài` : ""}</div>
                  </div>
                ))}
              </div>
            </Card>
            <Card title="📋 Log" size="small">
              <div style={{ maxHeight: 200, overflowY: "auto", fontSize: 10, fontFamily: "monospace", lineHeight: 1.5 }}>
                {logs.length === 0 ? <Text type="secondary">Chưa có hoạt động</Text> : logs.slice(-20).map((l, i) => <div key={i}>{l}</div>)}
              </div>
            </Card>
          </Space>

          <div>
            {!selectedBook ? (
              <Card><div style={{ textAlign: "center", padding: 40 }}><Text type="secondary">👈 Chọn sách bên trái</Text></div></Card>
            ) : loading ? (
              <Card><div style={{ textAlign: "center", padding: 40 }}><Spin size="large" /></div></Card>
            ) : (
              <Space orientation="vertical" size="middle" style={{ width: "100%" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  <Title level={4} style={{ margin: 0 }}>{selectedBook.title}</Title>
                  <Tag color="processing">{selectedBook.level}</Tag>
                  <Text type="secondary" style={{ marginLeft: "auto" }}><strong>{totalQ}</strong> câu hỏi · <strong>{mondaiGroups.length}</strong> もんだい</Text>
                </div>
                {mondaiGroups.length > 0 && (
                  <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                    {mondaiGroups.map((g, i) => {
                      const isActive = activeMondai === g.mondai; const color = MONDAI_COLORS[i % MONDAI_COLORS.length];
                      return (
                        <Button key={g.mondai} onClick={() => setActiveMondai(g.mondai)} type={isActive ? "primary" : "default"}
                          style={{ borderColor: isActive ? color : undefined, background: isActive ? color : undefined }}>
                          {MONDAI_LABELS[g.mondai] || `もんだい${g.mondai}`} <Badge count={g.count} style={{ backgroundColor: isActive ? "rgba(255,255,255,0.3)" : color, marginLeft: 6 }} />
                        </Button>
                      );
                    })}
                  </div>
                )}
                {activeQuestions.length === 0 ? (
                  <Card><div style={{ textAlign: "center", padding: 40 }}><Text type="secondary">Không có câu hỏi trong mondai này</Text></div></Card>
                ) : (
                  <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                    {activeQuestions.map((q, qi) => <QuestionCard key={q.id || qi} q={q} index={qi} mondaiColor={MONDAI_COLORS[mondaiIdx % MONDAI_COLORS.length]} />)}
                  </div>
                )}
              </Space>
            )}
          </div>
        </div>
      </Space>
    </div>
  );
}

function QuestionCard({ q, index, mondaiColor }: { q: QuestionData; index: number; mondaiColor: string }) {
  const [showTranscript, setShowTranscript] = useState(false);
  const lines = q.transcript_data?.lines || [];
  const correctKey = q.correct_answer;

  return (
    <Card size="small" styles={{ body: { padding: 0 } }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "10px 16px", borderBottom: "1px solid var(--border-default, #e5e7eb)", background: "var(--bg-app-subtle, #f9fafb)" }}>
        <span style={{ width: 28, height: 28, borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", background: mondaiColor, color: "white", fontSize: 12, fontWeight: 700 }}>{index + 1}</span>
        <Text type="secondary" style={{ flex: 1, fontSize: 12 }}>Đáp án: <strong>{correctKey}</strong></Text>
        {q.audio_url && <audio controls src={q.audio_url} style={{ height: 28, maxWidth: 180 }} />}
      </div>
      <div style={{ padding: "12px 16px" }}>
        <div style={{ display: "flex", gap: 16 }}>
          {q.image_url && <div style={{ flexShrink: 0 }}><img src={q.image_url} alt="" loading="lazy" style={{ width: 180, borderRadius: 8, border: "1px solid var(--border-default, #e5e7eb)" }} /></div>}
          <div style={{ flex: 1 }}>
            {q.text && <div style={{ fontSize: 13, marginBottom: 8, lineHeight: 1.6 }} dangerouslySetInnerHTML={{ __html: q.text.replace(/\n/g, "<br/>") }} />}
            <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              {q.choices.map((c, ci) => {
                const isCorrect = c.key === correctKey || String(ci + 1) === correctKey;
                return (
                  <div key={ci} style={{ display: "flex", alignItems: "center", gap: 8, padding: "6px 10px", borderRadius: 8, fontSize: 13, border: isCorrect ? "2px solid #10b981" : "1px solid var(--border-default, #e5e7eb)", background: isCorrect ? "rgba(16,185,129,.08)" : "transparent" }}>
                    <span style={{ width: 22, height: 22, borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 11, fontWeight: 700, background: isCorrect ? "#10b981" : "var(--bg-app-subtle, #f9fafb)", color: isCorrect ? "white" : "var(--text-tertiary)" }}>{c.key || ci + 1}</span>
                    <span style={{ fontWeight: isCorrect ? 600 : 400 }} dangerouslySetInnerHTML={{ __html: c.text }} />
                  </div>
                );
              })}
            </div>
          </div>
        </div>
        {lines.length > 0 && (
          <div style={{ marginTop: 12 }}>
            <Button size="small" type="text" icon={<SoundOutlined />} onClick={() => setShowTranscript(!showTranscript)}>
              {showTranscript ? "▲ Ẩn script" : "▼ Xem script"} ({lines.length} dòng)
            </Button>
            {showTranscript && (
              <Card size="small" style={{ marginTop: 8 }}>
                {lines.map((line, li) => (
                  <div key={li} style={{ marginBottom: 6 }}>
                    <div style={{ fontSize: 13, lineHeight: 1.6 }}>
                      {line.speaker && <Tag color={line.speaker === "M" ? "blue" : line.speaker === "F" ? "magenta" : "default"} style={{ marginRight: 6 }}>{line.speaker}</Tag>}
                      <span dangerouslySetInnerHTML={{ __html: line.text }} />
                    </div>
                    {line.text_vi && <div style={{ fontSize: 11, color: "var(--text-tertiary)", marginTop: 2, paddingLeft: line.speaker ? 30 : 0 }}>{line.text_vi}</div>}
                  </div>
                ))}
              </Card>
            )}
          </div>
        )}
      </div>
    </Card>
  );
}
