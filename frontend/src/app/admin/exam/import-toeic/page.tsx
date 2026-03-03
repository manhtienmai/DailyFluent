"use client";
import { useState, useEffect } from "react";
import { Card, Button, Input, Select, Typography, Space, Alert } from "antd";
import { UploadOutlined } from "@ant-design/icons";
import { adminGet, adminPost } from "@/lib/admin-api";
import Link from "next/link";

const { Title, Text } = Typography;
const { TextArea } = Input;

interface Template { id: number; title: string; book_title: string | null; level: string; category: string; question_count: number; }

export default function ImportToeicPage() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<number | null>(null);
  const [jsonData, setJsonData] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ success: boolean; message: string } | null>(null);

  useEffect(() => { adminGet<{ items: Template[] }>("/crud/exam/templates/?category=toeic").then(d => setTemplates(d.items || [])).catch(() => setTemplates([])); }, []);

  const handleImport = async () => {
    if (!jsonData.trim()) return; setLoading(true); setResult(null);
    try { const res = await adminPost<{ success: boolean; message: string }>("/crud/exam/import-toeic/", { json_data: jsonData, template_id: selectedTemplate }); setResult(res); }
    catch (err) { setResult({ success: false, message: String(err) }); }
    finally { setLoading(false); }
  };

  const previewCount = (() => { try { const d = JSON.parse(jsonData); if (d.questions) return d.questions.length; if (Array.isArray(d)) return d.length; return 0; } catch { return 0; } })();

  return (
    <div>
      <Space orientation="vertical" size="large" style={{ width: "100%" }}>
        <div><Title level={3} style={{ margin: 0 }}>📤 Import TOEIC</Title><Text type="secondary">Import bài thi TOEIC từ JSON</Text></div>
        <div style={{ display: "grid", gridTemplateColumns: "1.5fr 1fr", gap: 20 }}>
          <Card title="TOEIC JSON Data" size="small">
            <TextArea value={jsonData} onChange={(e) => setJsonData(e.target.value)} disabled={loading}
              placeholder='{"title": "TOEIC Test 1", "questions": [...]}'
              rows={16} style={{ fontFamily: "monospace", fontSize: 13 }} />
            {previewCount > 0 && <Text type="secondary" style={{ fontSize: 12, marginTop: 8, display: "block" }}>📊 {previewCount} câu hỏi</Text>}
          </Card>
          <Space orientation="vertical" size="middle" style={{ width: "100%" }}>
            <Card size="small" title="Cấu hình">
              <div><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Template đề thi (tuỳ chọn)</Text>
                <Select value={selectedTemplate} onChange={setSelectedTemplate} placeholder="— Tạo mới —" allowClear style={{ width: "100%" }}
                  options={templates.map(t => ({ value: t.id, label: `${t.title} (${t.question_count} câu)` }))} /></div>
            </Card>
            <Button type="primary" icon={<UploadOutlined />} block loading={loading} disabled={previewCount === 0} onClick={handleImport}>
              {loading ? "Importing..." : `📤 Import ${previewCount} câu`}
            </Button>
            {result && <Alert type={result.success ? "success" : "error"} showIcon message={result.success ? "✅ Import thành công!" : "❌ Lỗi"} description={result.message} />}
            <Card size="small" title="📋 Hướng dẫn">
              <Text style={{ fontSize: 12 }}>
                JSON format: <code>{`{ title, level, category, questions: [...] }`}</code><br />
                Mỗi question: <code>{`{ text, options, answer, toeic_part }`}</code><br />
                Hỗ trợ Part 1-7<br />
                <Link href="/admin/exam/templates">→ Xem tất cả đề thi</Link>
              </Text>
            </Card>
          </Space>
        </div>
      </Space>
    </div>
  );
}
