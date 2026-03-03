"use client";
import { useState, useEffect, useRef, useCallback } from "react";
import { Card, Button, Input, Select, Tag, Typography, Space, Alert, Spin } from "antd";
import { RobotOutlined, PlusOutlined, ImportOutlined } from "@ant-design/icons";
import { adminGet, adminPost } from "@/lib/admin-api";

const { Title, Text } = Typography;
const { TextArea } = Input;

interface ExamBook { id: number; title: string; level: string; category: string; }
interface ImportResult { success: boolean; message: string; template_id?: number; template_slug?: string; created?: number; total?: number; errors?: string[]; raw_response?: string; ai_data?: Record<string, unknown>; grammar_points_synced?: Record<string, unknown>; }
const LEVELS = ["N5", "N4", "N3", "N2", "N1"];
const MODELS = [
  { value: "gemini-2.5-flash", label: "⚡ Gemini 2.5 Flash (nhanh)" },
  { value: "gemini-2.0-flash", label: "⚡ Gemini 2.0 Flash" },
  { value: "gemini-2.5-pro", label: "🧠 Gemini 2.5 Pro (chính xác)" },
  { value: "gemini-1.5-pro", label: "🧠 Gemini 1.5 Pro" },
];

export default function ImportGrammarPage() {
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
  const [jsonText, setJsonText] = useState("");
  const [jsonLevel, setJsonLevel] = useState("N2");
  const [jsonBookId, setJsonBookId] = useState<number | null>(null);
  const [jsonLoading, setJsonLoading] = useState(false);
  const [jsonResult, setJsonResult] = useState<ImportResult | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchBooks = useCallback(() => { adminGet<{ items: ExamBook[] }>("/crud/exam/books/").then((d) => setBooks(d.items || [])).catch(() => setBooks([])); }, []);
  useEffect(() => { fetchBooks(); }, [fetchBooks]);
  useEffect(() => { return () => { if (timerRef.current) clearInterval(timerRef.current); }; }, []);

  const handleImport = async () => {
    if (!rawText.trim() || loading) return;
    setLoading(true); setResult(null); setElapsed(0);
    const start = Date.now();
    timerRef.current = setInterval(() => setElapsed(Math.floor((Date.now() - start) / 1000)), 1000);
    try {
      const res = await adminPost<ImportResult>("/crud/exam/import-grammar-ai/", { raw_text: rawText, book_id: selectedBook, level, model });
      setResult(res); if (res.success && res.ai_data) setShowPreview(true);
    } catch (err) { setResult({ success: false, message: String(err) }); }
    finally { setLoading(false); if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; } }
  };

  const handleCreateBook = async () => {
    if (!newBookTitle.trim() || creatingBook) return; setCreatingBook(true);
    try {
      const res = await adminPost<{ success: boolean; id?: number }>("/crud/exam/books/", { title: newBookTitle, level: newBookLevel, category: "BUN" });
      if (res.success && res.id) { await fetchBooks(); setSelectedBook(res.id); setNewBookTitle(""); setShowNewBook(false); }
    } catch { /* */ } finally { setCreatingBook(false); }
  };

  const handleJsonImport = async () => {
    if (!jsonText.trim() || jsonLoading) return; setJsonLoading(true); setJsonResult(null);
    try {
      const res = await adminPost<ImportResult>("/crud/exam/import-grammar-json/", { json_text: jsonText, book_id: jsonBookId, level: jsonLevel });
      setJsonResult(res); if (res.success) setJsonText("");
    } catch (err) { setJsonResult({ success: false, message: String(err) }); }
    finally { setJsonLoading(false); }
  };

  const textLines = rawText.trim().split("\n").filter((l) => l.trim()).length;
  let jsonPreview: { questions?: unknown[] } | null = null;
  try { if (jsonText.trim()) { let c = jsonText.trim().replace(/^```(?:json)?\s*/, "").replace(/\s*```\s*$/, ""); jsonPreview = JSON.parse(c); } } catch { /* invalid */ }
  const bunBooks = books.filter((b) => b.category === "BUN");

  return (
    <div>
      <Space orientation="vertical" size="large" style={{ width: "100%" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <Title level={3} style={{ margin: 0 }}>🤖 AI Import 文法</Title>
          {loading && <Tag color="warning" icon={<Spin size="small" />}>Đang xử lý... {elapsed}s</Tag>}
        </div>
        <Text type="secondary">Paste HTML đề thi ngữ pháp → Gemini AI extract + giải thích → tự động lưu database</Text>

        <div style={{ display: "grid", gridTemplateColumns: "1.5fr 1fr", gap: 20 }}>
          <Card title="Nội dung HTML đề thi ngữ pháp" size="small">
            <TextArea value={rawText} onChange={(e) => setRawText(e.target.value)} rows={18} style={{ fontFamily: "monospace", fontSize: 13, lineHeight: 1.6 }}
              placeholder={`Paste HTML đề thi ngữ pháp vào đây...\n\nVí dụ:\n<div class="thithu_ques" data-id="1">\n  <span class="txt1">お客様にいろいろと文句を（　　）あげく...</span>\n  ...\n</div>`} />
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
                      options={bunBooks.map(b => ({ value: b.id, label: `${b.title} (${b.level})` }))} />
                  )}
                </div>
              </Space>
            </Card>

            <Button type="primary" block icon={<RobotOutlined />} loading={loading} disabled={textLines === 0} onClick={handleImport} size="large">
              {loading ? `Đang xử lý AI... (${elapsed}s)` : "AI Extract & Import 文法"}
            </Button>
            {loading && <Text type="secondary" style={{ textAlign: "center", display: "block", fontSize: 12 }}>Thời gian xử lý khoảng 30-60s cho 18 câu.</Text>}

            {result && <Alert type={result.success ? "success" : "error"} showIcon message={result.success ? "Import thành công!" : "Lỗi"}
              description={<>{result.message}{result.template_slug && <div style={{ fontSize: 12, marginTop: 4 }}>Slug: <code>{result.template_slug}</code> • {elapsed}s</div>}
                {result.errors && result.errors.length > 0 && <div style={{ marginTop: 4, color: "#dc2626" }}>{result.errors.map((e, i) => <div key={i}>⚠ {e}</div>)}</div>}</>} />}

            {result?.ai_data && showPreview && (
              <Card size="small" title={<>📋 AI Response Preview <Button size="small" type="text" onClick={() => setShowPreview(false)}>Ẩn</Button></>}>
                <pre style={{ fontSize: 11, fontFamily: "monospace", maxHeight: 300, overflow: "auto", whiteSpace: "pre-wrap", wordBreak: "break-word" }}>{JSON.stringify(result.ai_data, null, 2)}</pre>
              </Card>
            )}

            <Card size="small" title="📋 Hướng dẫn">
              <Text style={{ fontSize: 12 }}>1. Copy toàn bộ HTML đề thi 文法 từ web<br />2. Paste vào ô bên trái<br />3. Chọn trình độ JLPT và sách<br />4. Click <strong>AI Extract & Import 文法</strong><br />5. AI tự trích xuất câu hỏi, đáp án, điểm ngữ pháp</Text>
            </Card>
          </Space>
        </div>

        {/* ── JSON Direct Import ── */}
        <div style={{ borderTop: "2px dashed var(--border-default, #e5e7eb)", paddingTop: 28 }}>
          <Space align="center" style={{ marginBottom: 16 }}><Title level={4} style={{ margin: 0 }}>📋 Import JSON trực tiếp</Title><Tag color="blue">Không cần AI</Tag></Space>
          <Text type="secondary" style={{ display: "block", marginBottom: 16, fontSize: 13 }}>Nếu bạn đã có JSON output từ Gemini, paste trực tiếp vào đây.</Text>

          <div style={{ display: "grid", gridTemplateColumns: "1.5fr 1fr", gap: 20 }}>
            <Card title="JSON Data" size="small">
              <TextArea value={jsonText} onChange={(e) => setJsonText(e.target.value)} rows={14} style={{ fontFamily: "monospace", fontSize: 13, lineHeight: 1.6 }}
                placeholder={`Paste JSON từ Gemini vào đây...\n\n{\n  "book_title": "Tên sách",\n  "questions": [\n    { "id": 1, "sentence": "...", ... }\n  ]\n}`} />
              <Space style={{ marginTop: 8 }}>
                {jsonPreview && <Tag color="green">✓ Valid JSON{jsonPreview.questions ? ` • ${(jsonPreview.questions as unknown[]).length} câu` : ""}</Tag>}
                {jsonText.trim() && !jsonPreview && <Tag color="red">✗ JSON không hợp lệ</Tag>}
              </Space>
            </Card>

            <Space orientation="vertical" size="middle" style={{ width: "100%" }}>
              <Card size="small" title="Cấu hình">
                <Space orientation="vertical" style={{ width: "100%" }} size="small">
                  <div><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Trình độ JLPT</Text>
                    <Select value={jsonLevel} onChange={setJsonLevel} style={{ width: "100%" }} options={LEVELS.map(l => ({ value: l, label: l }))} /></div>
                  <div><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Sách</Text>
                    <Select value={jsonBookId} onChange={setJsonBookId} placeholder="— Không chọn —" allowClear style={{ width: "100%" }}
                      options={bunBooks.map(b => ({ value: b.id, label: `${b.title} (${b.level})` }))} /></div>
                </Space>
              </Card>
              <Button type="primary" block icon={<ImportOutlined />} loading={jsonLoading} disabled={!jsonPreview} onClick={handleJsonImport} style={{ background: "#10b981", borderColor: "#10b981" }}>
                {jsonLoading ? "Đang import..." : "📥 Import JSON → Database"}
              </Button>
              {jsonResult && <Alert type={jsonResult.success ? "success" : "error"} showIcon message={jsonResult.success ? "Import thành công!" : "Lỗi"}
                description={<>{jsonResult.message}{jsonResult.template_slug && <div style={{ fontSize: 11, marginTop: 4 }}>Template: <code>{jsonResult.template_slug}</code> • {jsonResult.created}/{jsonResult.total} câu</div>}
                  {jsonResult.grammar_points_synced && <div style={{ fontSize: 11, marginTop: 4, color: "#6366f1" }}>🔄 Grammar synced: {JSON.stringify(jsonResult.grammar_points_synced)}</div>}
                  {jsonResult.errors && jsonResult.errors.length > 0 && <div style={{ marginTop: 4 }}>{jsonResult.errors.map((e, i) => <div key={i}>⚠ {e}</div>)}</div>}</>} />}
              <Card size="small" title="💡 Khi nào dùng?">
                <Text style={{ fontSize: 11 }}>• Đã gọi Gemini API thủ công<br />• Import lại JSON đã sửa tay<br />• JSON cần cấu trúc <code>{`{"questions": [...]}`}</code><br />• Tự động tạo GrammarPoint + sync FSRS</Text>
              </Card>
            </Space>
          </div>
        </div>
      </Space>
    </div>
  );
}
