"use client";
import { useState, useEffect } from "react";
import { Card, Button, Input, Select, Typography, Space, Alert, Statistic, Row, Col } from "antd";
import { UploadOutlined } from "@ant-design/icons";
import { adminGet, adminPost } from "@/lib/admin-api";

const { Title, Text } = Typography;
const { TextArea } = Input;

interface VocabSet { id: number; title: string; collection: string | null; }
interface Stats { created_vocabs: number; existing_vocabs: number; created_definitions: number; created_examples: number; added_to_set: number; skipped: number; }

export default function ImportJPPage() {
  const [jsonData, setJsonData] = useState("");
  const [sets, setSets] = useState<VocabSet[]>([]);
  const [selectedSet, setSelectedSet] = useState<number | null>(null);
  const [newSetTitle, setNewSetTitle] = useState("");
  const [source, setSource] = useState("other");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ success: boolean; stats?: Stats; message?: string } | null>(null);

  useEffect(() => { adminGet<VocabSet[]>("/crud/vocab/sets-simple/").then(setSets).catch(() => setSets([])); }, []);

  const handleImport = async () => {
    if (!jsonData.trim()) return; setLoading(true); setResult(null);
    try {
      const res = await adminPost<{ success: boolean; stats?: Stats; message?: string; set_id?: number }>("/crud/vocab/import-jp/", { json_data: jsonData, set_id: selectedSet, new_set_title: newSetTitle, source });
      setResult(res);
      if (res.success && res.set_id && !selectedSet) adminGet<VocabSet[]>("/crud/vocab/sets-simple/").then(setSets);
    } catch (err) { setResult({ success: false, message: String(err) }); }
    finally { setLoading(false); }
  };

  const previewCount = (() => { try { const d = JSON.parse(jsonData); return Array.isArray(d) ? d.length : 0; } catch { return 0; } })();

  return (
    <div>
      <Space orientation="vertical" size="large" style={{ width: "100%" }}>
        <div><Title level={3} style={{ margin: 0 }}>🇯🇵 Import Japanese Vocabulary</Title><Text type="secondary">Import từ JSON (Mimikara format)</Text></div>

        <div style={{ display: "grid", gridTemplateColumns: "1.5fr 1fr", gap: 20 }}>
          <Card title="JSON Data (mảng các object)" size="small">
            <TextArea value={jsonData} onChange={(e) => setJsonData(e.target.value)} disabled={loading}
              placeholder={'[\n  {\n    "word": "勉強",\n    "meanings": [\n      { "pos": "noun", "meaning": "study" }\n    ]\n  }\n]'}
              rows={14} style={{ fontFamily: "monospace", fontSize: 13 }} />
            {previewCount > 0 && <Text type="secondary" style={{ fontSize: 12, marginTop: 8, display: "block" }}>📊 Phát hiện <strong>{previewCount}</strong> từ trong JSON</Text>}
          </Card>

          <Space orientation="vertical" size="middle" style={{ width: "100%" }}>
            <Card size="small" title="Cấu hình">
              <Space orientation="vertical" style={{ width: "100%" }} size="small">
                <div><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Thêm vào Set</Text>
                  <Select value={selectedSet} onChange={setSelectedSet} placeholder="— Không chọn —" allowClear disabled={loading} style={{ width: "100%" }}
                    options={sets.map(s => ({ value: s.id, label: s.title }))} /></div>
                {!selectedSet && <div><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Hoặc tạo Set mới</Text>
                  <Input value={newSetTitle} onChange={(e) => setNewSetTitle(e.target.value)} disabled={loading} placeholder="Tên set mới..." /></div>}
                <div><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Source</Text>
                  <Select value={source} onChange={setSource} disabled={loading} style={{ width: "100%" }}
                    options={[{ value: "other", label: "Other" }, { value: "textbook", label: "Textbook" }, { value: "cambridge", label: "Cambridge" }, { value: "user", label: "User" }]} /></div>
              </Space>
            </Card>
            <Button type="primary" icon={<UploadOutlined />} block loading={loading} disabled={previewCount === 0} onClick={handleImport}>
              {loading ? "Importing..." : `🇯🇵 Import ${previewCount} từ`}
            </Button>

            {result && (
              <Alert type={result.success ? "success" : "error"} showIcon message={result.success ? "Import thành công!" : "Lỗi"}
                description={result.stats ? (
                  <Row gutter={[8, 8]}>
                    <Col span={12}><Statistic title="Từ mới" value={result.stats.created_vocabs} valueStyle={{ fontSize: 16 }} /></Col>
                    <Col span={12}><Statistic title="Từ đã có" value={result.stats.existing_vocabs} valueStyle={{ fontSize: 16 }} /></Col>
                    <Col span={12}><Statistic title="Nghĩa tạo" value={result.stats.created_definitions} valueStyle={{ fontSize: 16 }} /></Col>
                    <Col span={12}><Statistic title="Ví dụ" value={result.stats.created_examples} valueStyle={{ fontSize: 16 }} /></Col>
                    <Col span={12}><Statistic title="Vào set" value={result.stats.added_to_set} valueStyle={{ fontSize: 16 }} /></Col>
                    {result.stats.skipped > 0 && <Col span={12}><Statistic title="Bỏ qua" value={result.stats.skipped} valueStyle={{ fontSize: 16, color: "#f59e0b" }} /></Col>}
                  </Row>
                ) : result.message} />
            )}
          </Space>
        </div>
      </Space>
    </div>
  );
}
