"use client";
import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { Card, Button, Input, Segmented, Tag, Typography, Space, Spin } from "antd";
import { SaveOutlined, CameraOutlined, ExperimentOutlined, BookOutlined, TranslationOutlined, ThunderboltOutlined } from "@ant-design/icons";
import { adminGet, adminPost } from "@/lib/admin-api";

const { Title, Text } = Typography;
const { TextArea } = Input;

interface Passage { id?: number; text: string; translation?: string; explanation?: string; vocab_list?: string; }
interface TemplateInfo { id: number; title: string; level: string; category: string; }

export default function DokkaiEditorPage() {
  const params = useParams();
  const templateId = Number(params.id);
  const [template, setTemplate] = useState<TemplateInfo | null>(null);
  const [passage, setPassage] = useState<Passage>({ text: "" });
  const [loading, setLoading] = useState(true);
  const [aiLoading, setAiLoading] = useState<string | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [tab, setTab] = useState<"text" | "translation" | "explanation" | "vocab">("text");

  useEffect(() => {
    setLoading(true);
    Promise.all([
      adminGet<TemplateInfo>(`/crud/exam/templates/${templateId}/`).catch(() => null),
      adminGet<{ passage: Passage }>(`/crud/dokkai/load-passage/?template_id=${templateId}`).catch(() => ({ passage: { text: "" } })),
    ]).then(([t, p]) => { if (t) setTemplate(t); if (p?.passage) setPassage(p.passage); }).finally(() => setLoading(false));
  }, [templateId]);

  const aiAction = async (action: string) => {
    setAiLoading(action);
    try {
      let res: Record<string, string> = {};
      if (action === "ocr") res = await adminPost("/crud/dokkai/ocr/", { template_id: templateId });
      else if (action === "explain") res = await adminPost("/crud/dokkai/explain/", { text: passage.text, template_id: templateId });
      else if (action === "vocab") res = await adminPost("/crud/dokkai/vocab/", { text: passage.text });
      else if (action === "translate") res = await adminPost("/crud/dokkai/translate/", { text: passage.text });
      else if (action === "analyze-full") {
        res = await adminPost("/crud/dokkai/analyze-full/", { text: passage.text, template_id: templateId });
        if (res.translation) setPassage(prev => ({ ...prev, translation: res.translation }));
        if (res.explanation) setPassage(prev => ({ ...prev, explanation: res.explanation }));
        if (res.vocab_list) setPassage(prev => ({ ...prev, vocab_list: res.vocab_list }));
      }
      if (action === "ocr" && res.text) setPassage(prev => ({ ...prev, text: res.text }));
      if (action === "explain" && res.explanation) setPassage(prev => ({ ...prev, explanation: res.explanation }));
      if (action === "vocab" && res.vocab_list) setPassage(prev => ({ ...prev, vocab_list: res.vocab_list }));
      if (action === "translate" && res.translation) setPassage(prev => ({ ...prev, translation: res.translation }));
      setLogs(prev => [...prev, `✅ ${action}: OK`]);
    } catch (err) { setLogs(prev => [...prev, `❌ ${action}: ${String(err)}`]); }
    finally { setAiLoading(null); }
  };

  const savePassage = async () => {
    setAiLoading("save");
    try { await adminPost("/crud/dokkai/save-passage/", { template_id: templateId, ...passage }); setLogs(prev => [...prev, "💾 Passage saved"]); }
    catch (err) { setLogs(prev => [...prev, `❌ Save: ${String(err)}`]); } finally { setAiLoading(null); }
  };

  const saveAll = async () => {
    setAiLoading("save-all");
    try { await adminPost("/crud/dokkai/save-full/", { template_id: templateId, ...passage }); setLogs(prev => [...prev, "💾 All saved"]); }
    catch (err) { setLogs(prev => [...prev, `❌ Save all: ${String(err)}`]); } finally { setAiLoading(null); }
  };

  if (loading) return <div style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: 400 }}><Spin size="large" /></div>;

  const AI_TOOLS = [
    { key: "ocr", label: "OCR", icon: <CameraOutlined /> },
    { key: "explain", label: "Explain", icon: <ExperimentOutlined /> },
    { key: "vocab", label: "Vocab", icon: <BookOutlined /> },
    { key: "translate", label: "Translate", icon: <TranslationOutlined /> },
    { key: "analyze-full", label: "Full Analysis", icon: <ThunderboltOutlined /> },
  ];

  return (
    <div>
      <Space orientation="vertical" size="large" style={{ width: "100%" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div>
            <Title level={3} style={{ margin: 0 }}>📖 Dokkai Editor</Title>
            <Text type="secondary">{template ? `${template.title} — ${template.level} ${template.category}` : `Template #${templateId}`}</Text>
          </div>
          <Space>
            <Button icon={<SaveOutlined />} onClick={savePassage} loading={aiLoading === "save"} disabled={!!aiLoading}>Lưu passage</Button>
            <Button type="primary" icon={<SaveOutlined />} onClick={saveAll} loading={aiLoading === "save-all"} disabled={!!aiLoading}>Lưu tất cả</Button>
          </Space>
        </div>

        <Space wrap>
          {AI_TOOLS.map(a => (
            <Button key={a.key} icon={a.icon} onClick={() => aiAction(a.key)} loading={aiLoading === a.key} disabled={!!aiLoading}>{a.label}</Button>
          ))}
        </Space>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 300px", gap: 16 }}>
          <Card size="small">
            <Segmented value={tab} onChange={(v) => setTab(v as typeof tab)} block style={{ marginBottom: 12 }}
              options={[
                { label: "📝 Text", value: "text" },
                { label: "🌐 Dịch", value: "translation" },
                { label: "🧠 Giải thích", value: "explanation" },
                { label: "📚 Từ vựng", value: "vocab" },
              ]} />
            <TextArea
              value={tab === "text" ? passage.text : tab === "translation" ? (passage.translation || "") : tab === "explanation" ? (passage.explanation || "") : (passage.vocab_list || "")}
              onChange={e => {
                const val = e.target.value;
                if (tab === "text") setPassage(prev => ({ ...prev, text: val }));
                else if (tab === "translation") setPassage(prev => ({ ...prev, translation: val }));
                else if (tab === "explanation") setPassage(prev => ({ ...prev, explanation: val }));
                else setPassage(prev => ({ ...prev, vocab_list: val }));
              }}
              rows={18} style={{ fontSize: 14, lineHeight: 1.8, fontFamily: tab === "text" ? "'Noto Sans JP', sans-serif" : "inherit" }} />
          </Card>

          <Card title="📋 Activity Log" size="small" style={{ height: "fit-content" }}>
            <div style={{ maxHeight: 400, overflowY: "auto", fontSize: 11, fontFamily: "monospace", lineHeight: 1.6 }}>
              {logs.length === 0 ? <Text type="secondary">Dùng các nút AI ở bên trên</Text> : logs.map((l, i) => <div key={i}>{l}</div>)}
            </div>
          </Card>
        </div>
      </Space>
    </div>
  );
}
