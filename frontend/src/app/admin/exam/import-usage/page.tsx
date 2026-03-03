"use client";
import { useState, useEffect, useRef, useCallback } from "react";
import { Card, Button, Input, Select, Tag, Typography, Space, Alert, Spin } from "antd";
import { RobotOutlined, PlusOutlined } from "@ant-design/icons";
import { adminGet, adminPost } from "@/lib/admin-api";

const { Title, Text } = Typography;
const { TextArea } = Input;

interface ExamBook { id: number; title: string; level: string; category: string; }
interface ImportResult { success: boolean; message: string; template_id?: number; template_slug?: string; created?: number; total?: number; errors?: string[]; raw_response?: string; ai_data?: Record<string, unknown>; }
const LEVELS = ["N5", "N4", "N3", "N2", "N1"];
const MODELS = [
  { value: "gemini-2.5-flash", label: "⚡ Gemini 2.5 Flash (nhanh)" },
  { value: "gemini-2.0-flash", label: "⚡ Gemini 2.0 Flash" },
  { value: "gemini-2.5-pro", label: "🧠 Gemini 2.5 Pro (chính xác)" },
  { value: "gemini-1.5-pro", label: "🧠 Gemini 1.5 Pro" },
];

export default function ImportUsagePage() {
  const [rawText, setRawText] = useState("");
  const [books, setBooks] = useState<ExamBook[]>([]);
  const [selectedBook, setSelectedBook] = useState<number | null>(null);
  const [level, setLevel] = useState("N2");
  const [model, setModel] = useState("gemini-2.5-flash");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [showPreview, setShowPreview] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [showNewBook, setShowNewBook] = useState(false);
  const [newBookTitle, setNewBookTitle] = useState("");
  const [newBookLevel, setNewBookLevel] = useState("N2");
  const [creatingBook, setCreatingBook] = useState(false);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchBooks = useCallback(() => { adminGet<{ items: ExamBook[] }>("/crud/exam/books/").then((d) => setBooks(d.items || [])).catch(() => setBooks([])); }, []);
  useEffect(() => { fetchBooks(); }, [fetchBooks]);
  useEffect(() => { return () => { if (timerRef.current) clearInterval(timerRef.current); }; }, []);

  const handleImport = async () => {
    if (!rawText.trim() || loading) return; setLoading(true); setResult(null); setElapsed(0);
    const start = Date.now(); timerRef.current = setInterval(() => setElapsed(Math.floor((Date.now() - start) / 1000)), 1000);
    try {
      const res = await adminPost<ImportResult>("/crud/exam/import-usage-ai/", { raw_text: rawText, book_id: selectedBook, level, model });
      setResult(res); if (res.success && res.ai_data) setShowPreview(true);
    } catch (err) { setResult({ success: false, message: String(err) }); }
    finally { setLoading(false); if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; } }
  };

  const handleCreateBook = async () => {
    if (!newBookTitle.trim() || creatingBook) return; setCreatingBook(true);
    try {
      const res = await adminPost<{ success: boolean; id?: number; message?: string }>("/crud/exam/books/", { title: newBookTitle, level: newBookLevel, category: "MOJI" });
      if (res.success && res.id) { await fetchBooks(); setSelectedBook(res.id); setNewBookTitle(""); setShowNewBook(false); }
    } catch { /* */ } finally { setCreatingBook(false); }
  };

  const textLines = rawText.trim().split("\n").filter((l) => l.trim()).length;
  const mojiBooks = books.filter((b) => b.category === "MOJI");

  return (
    <div>
      <Space orientation="vertical" size="large" style={{ width: "100%" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <Title level={3} style={{ margin: 0 }}>🤖 AI Import 用法</Title>
          {loading && <Tag color="warning" icon={<Spin size="small" />}>Đang xử lý... {elapsed}s</Tag>}
        </div>
        <Text type="secondary">Paste nội dung đề thi 用法 → Gemini AI extract + giải thích → tự động lưu database</Text>

        <div style={{ display: "grid", gridTemplateColumns: "1.5fr 1fr", gap: 20 }}>
          <Card title="Nội dung đề thi (paste từ web/pdf)" size="small">
            <TextArea value={rawText} onChange={(e) => setRawText(e.target.value)} rows={18} style={{ fontFamily: "monospace", fontSize: 13, lineHeight: 1.6 }}
              placeholder={`Paste nội dung đề thi 用法 vào đây...\n\nVí dụ:\n禁止\n1. 免許がないのに車を運転するのは法律（禁止）だ。\n2. このビルの中に立ち入ることは（禁止）されています。\n...`} />
            {textLines > 0 && <Text type="secondary" style={{ fontSize: 12, marginTop: 8, display: "block" }}>📄 {textLines} dòng</Text>}
          </Card>

          <Space orientation="vertical" size="middle" style={{ width: "100%" }}>
            <Card size="small" title="Cấu hình AI">
              <Space orientation="vertical" style={{ width: "100%" }} size="small">
                <div><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Trình độ JLPT</Text>
                  <Select value={level} onChange={setLevel} style={{ width: "100%" }} options={LEVELS.map(l => ({ value: l, label: l }))} /></div>
                <div><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Gemini Model</Text>
                  <Select value={model} onChange={setModel} style={{ width: "100%" }} options={MODELS} /></div>
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Sách (tuỳ chọn)</Text>
                    <Button size="small" type={showNewBook ? "primary" : "text"} icon={showNewBook ? undefined : <PlusOutlined />} onClick={() => setShowNewBook(!showNewBook)}>
                      {showNewBook ? "✕ Huỷ" : "Thêm sách"}
                    </Button>
                  </div>
                  {showNewBook ? (
                    <Card size="small" style={{ marginTop: 4, borderStyle: "dashed" }}>
                      <Input value={newBookTitle} onChange={(e) => setNewBookTitle(e.target.value)} placeholder="Tên sách mới..." onPressEnter={handleCreateBook} />
                      <Select value={newBookLevel} onChange={setNewBookLevel} style={{ width: "100%", marginTop: 6 }} options={LEVELS.map(l => ({ value: l, label: l }))} />
                      <Button block style={{ marginTop: 6 }} onClick={handleCreateBook} disabled={!newBookTitle.trim()} loading={creatingBook}>📚 Tạo sách mới</Button>
                    </Card>
                  ) : (
                    <Select value={selectedBook} onChange={setSelectedBook} placeholder="— Không chọn —" allowClear style={{ width: "100%" }}
                      options={mojiBooks.map(b => ({ value: b.id, label: `${b.title} (${b.level})` }))} />
                  )}
                </div>
              </Space>
            </Card>

            <Button type="primary" block icon={<RobotOutlined />} loading={loading} disabled={textLines === 0} onClick={handleImport} size="large">
              {loading ? `Đang xử lý AI... (${elapsed}s)` : "🤖 AI Extract & Import"}
            </Button>
            {loading && <Text type="secondary" style={{ textAlign: "center", display: "block", fontSize: 12 }}>Có thể chuyển sang trang khác trong lúc chờ AI xử lý.</Text>}

            {result && <Alert type={result.success ? "success" : "error"} showIcon message={result.success ? "Import thành công!" : "Lỗi"}
              description={<>{result.message}{result.template_slug && <div style={{ fontSize: 12, marginTop: 4 }}>Slug: <code>{result.template_slug}</code> • {elapsed}s</div>}
                {result.errors && result.errors.length > 0 && <div style={{ marginTop: 4, color: "#dc2626" }}>{result.errors.map((e, i) => <div key={i}>⚠ {e}</div>)}</div>}</>} />}

            {result?.ai_data && showPreview && (
              <Card size="small" title={<>📋 AI Response Preview <Button size="small" type="text" onClick={() => setShowPreview(false)}>Ẩn</Button></>}>
                <pre style={{ fontSize: 11, fontFamily: "monospace", maxHeight: 300, overflow: "auto", whiteSpace: "pre-wrap", wordBreak: "break-word" }}>{JSON.stringify(result.ai_data, null, 2)}</pre>
              </Card>
            )}

            <Card size="small" title="📋 Hướng dẫn">
              <Text style={{ fontSize: 12 }}>1. Copy đề thi 用法 từ web/PDF<br />2. Paste vào ô bên trái<br />3. Chọn trình độ + sách<br />4. Click <strong>AI Extract & Import</strong><br />5. Có thể chuyển trang khác trong lúc chờ</Text>
            </Card>
          </Space>
        </div>
      </Space>
    </div>
  );
}
