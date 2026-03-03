"use client";
import { useState } from "react";
import { Card, Button, Input, Alert, Spin, Typography, Tag } from "antd";
import { ImportOutlined } from "@ant-design/icons";
import { adminPost } from "@/lib/admin-api";

const { Title, Text } = Typography;
const { TextArea } = Input;

interface ImportResult {
  success: boolean;
  message: string;
  template_id?: number;
  template_slug?: string;
  created?: number;
}

const SAMPLE_JSON = `{
  "title": "Đề số 1 – Tiếng Anh vào lớp 10",
  "description": "Đề thi thử Tiếng Anh tuyển sinh lớp 10",
  "time_limit_minutes": 60,
  "sections": [
    {
      "type": "pronunciation",
      "title": "Chọn từ có phần gạch chân phát âm khác",
      "questions": [
        {
          "num": 1,
          "text": "Choose the word whose underlined part differs...",
          "choices": [
            {"key": "A", "text": "ghost"},
            {"key": "B", "text": "office"},
            {"key": "C", "text": "long"},
            {"key": "D", "text": "modern"}
          ],
          "correct_answer": "A",
          "explanation_json": {
            "rule": "Phát âm nguyên âm 'o'",
            "detail": "'ghost' phát âm /oʊ/, còn lại /ɒ/",
            "tip": "Chú ý từ gốc tiếng Anh cổ"
          }
        }
      ]
    }
  ]
}`;

export default function ImportEnglishPage() {
  const [jsonText, setJsonText] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ImportResult | null>(null);

  const handleImport = async () => {
    if (!jsonText.trim() || loading) return;
    setLoading(true); setResult(null);
    try {
      const data = JSON.parse(jsonText);
      const res = await adminPost<ImportResult>("/crud/exam/english-import/", data);
      setResult(res);
    } catch (err) {
      if (err instanceof SyntaxError) {
        setResult({ success: false, message: "JSON không hợp lệ: " + err.message });
      } else {
        setResult({ success: false, message: String(err) });
      }
    } finally { setLoading(false); }
  };

  const handleLoadSample = () => setJsonText(SAMPLE_JSON);

  const lineCount = jsonText.trim() ? jsonText.split("\n").length : 0;
  let questionCount = 0;
  try {
    if (jsonText.trim()) {
      const d = JSON.parse(jsonText);
      questionCount = (d.sections || []).reduce((sum: number, s: { questions?: unknown[] }) => sum + (s.questions?.length || 0), 0);
    }
  } catch {}

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16 }}>
        <Title level={3} style={{ margin: 0 }}>🇬🇧 Import English Exam</Title>
        {loading && <Tag color="processing" icon={<Spin size="small" />}>Đang import...</Tag>}
      </div>
      <Text type="secondary">Paste JSON đề thi Tiếng Anh → Import vào database</Text>

      <div style={{ display: "grid", gridTemplateColumns: "1.5fr 1fr", gap: 20, marginTop: 16 }}>
        <Card title="JSON đề thi" size="small" extra={
          <Button size="small" type="link" onClick={handleLoadSample}>📋 Mẫu</Button>
        }>
          <TextArea
            value={jsonText}
            onChange={(e) => setJsonText(e.target.value)}
            rows={22}
            style={{ fontFamily: "monospace", fontSize: 12, lineHeight: 1.5 }}
            placeholder="Paste JSON đề thi vào đây..."
          />
          {lineCount > 0 && (
            <Text type="secondary" style={{ fontSize: 11, marginTop: 4, display: "block" }}>
              📄 {lineCount} dòng • {questionCount > 0 ? `📋 ${questionCount} câu hỏi` : ""}
            </Text>
          )}
        </Card>

        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <Card size="small" title="Cấu trúc JSON">
            <Text style={{ fontSize: 11 }}>
              <code>title</code>: Tên đề thi<br />
              <code>description</code>: Mô tả<br />
              <code>time_limit_minutes</code>: Thời gian (phút)<br />
              <code>sections[]</code>: Các phần bài<br />
              &nbsp;&nbsp;<code>.type</code>: pronunciation, stress, grammar, communication, cloze_announcement, sentence_order, sentence_completion, cloze_passage, closest_meaning, sentence_from_cues, sign_notice, reading_comprehension, sentence_insertion<br />
              &nbsp;&nbsp;<code>.title</code>: Tiêu đề phần<br />
              &nbsp;&nbsp;<code>.passage_text</code>: Đoạn văn (nếu có)<br />
              &nbsp;&nbsp;<code>.questions[]</code>: Câu hỏi<br />
              &nbsp;&nbsp;&nbsp;&nbsp;<code>.num</code>: Số thứ tự (1-40)<br />
              &nbsp;&nbsp;&nbsp;&nbsp;<code>.text</code>: Nội dung câu hỏi<br />
              &nbsp;&nbsp;&nbsp;&nbsp;<code>.choices[]</code>: {"[{key, text}]"}<br />
              &nbsp;&nbsp;&nbsp;&nbsp;<code>.correct_answer</code>: A/B/C/D<br />
              &nbsp;&nbsp;&nbsp;&nbsp;<code>.explanation_json</code>: {"{rule, detail, tip}"}
            </Text>
          </Card>

          <Button
            type="primary" block size="large"
            icon={<ImportOutlined />}
            loading={loading}
            disabled={lineCount === 0}
            onClick={handleImport}
          >
            {loading ? "Đang import..." : "📥 Import Exam"}
          </Button>

          {result && (
            <Alert
              type={result.success ? "success" : "error"}
              showIcon
              message={result.success ? "Import thành công!" : "Lỗi"}
              description={<>
                {result.message}
                {result.template_slug && (
                  <div style={{ fontSize: 11, marginTop: 4 }}>
                    Slug: <code>{result.template_slug}</code> • {result.created} câu
                  </div>
                )}
              </>}
            />
          )}
        </div>
      </div>
    </div>
  );
}
