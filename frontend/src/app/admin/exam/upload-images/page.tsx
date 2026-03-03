"use client";
import { useState, useEffect, useRef } from "react";
import { Card, Button, Select, Tag, Typography, Space, Spin, Badge, Upload } from "antd";
import { UploadOutlined, PictureOutlined, CheckCircleOutlined, CloseCircleOutlined } from "@ant-design/icons";
import { adminGet, adminUpload } from "@/lib/admin-api";

const { Title, Text } = Typography;

interface Template { id: number; title: string; question_count: number; category: string; }
interface Question { id: number; order: number; text: string; question_type: string; toeic_part: string | null; image_url?: string; }

export default function UploadImagesPage() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<number | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<Record<number, string>>({});

  useEffect(() => { adminGet<{ items: Template[] }>("/crud/exam/templates/").then(d => setTemplates(d.items || [])).catch(() => setTemplates([])); }, []);

  const loadQuestions = (templateId: number) => {
    setSelectedTemplate(templateId); setLoading(true);
    adminGet<{ items: Question[] }>(`/crud/exam/questions/?template_id=${templateId}`)
      .then(d => setQuestions(d.items || [])).catch(() => setQuestions([])).finally(() => setLoading(false));
  };

  const handleImageUpload = async (questionId: number, file: File) => {
    setUploadStatus(prev => ({ ...prev, [questionId]: "uploading" }));
    try {
      const formData = new FormData();
      formData.append("image", file); formData.append("question_id", String(questionId));
      await adminUpload("/crud/exam/upload-image/", formData);
      setUploadStatus(prev => ({ ...prev, [questionId]: "success" }));
    } catch { setUploadStatus(prev => ({ ...prev, [questionId]: "error" })); }
  };

  return (
    <div>
      <Space orientation="vertical" size="large" style={{ width: "100%" }}>
        <div><Title level={3} style={{ margin: 0 }}>🖼️ Upload Images</Title><Text type="secondary">Upload ảnh cho câu hỏi thi</Text></div>
        <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: 20 }}>
          <Card title="Chọn đề thi" size="small" style={{ height: "fit-content" }}>
            <div style={{ maxHeight: 500, overflowY: "auto" }}>
              {templates.map(t => (
                <div key={t.id} onClick={() => loadQuestions(t.id)}
                  style={{ padding: "8px 12px", cursor: "pointer", borderRadius: 8, marginBottom: 2,
                    background: selectedTemplate === t.id ? "var(--ant-color-primary, #1677ff)" : "transparent",
                    color: selectedTemplate === t.id ? "white" : "inherit", fontSize: 12, transition: "all 0.15s" }}>
                  <div style={{ fontWeight: 600 }}>{t.title}</div>
                  <div style={{ fontSize: 10, opacity: 0.7 }}>{t.category} · {t.question_count} câu</div>
                </div>
              ))}
            </div>
          </Card>
          <Card title={selectedTemplate ? `Câu hỏi (${questions.length})` : "Câu hỏi"} size="small">
            {!selectedTemplate ? (
              <div style={{ textAlign: "center", padding: 40 }}><Text type="secondary">👈 Chọn đề thi bên trái</Text></div>
            ) : loading ? (
              <div style={{ textAlign: "center", padding: 40 }}><Spin size="large" /></div>
            ) : questions.length === 0 ? (
              <div style={{ textAlign: "center", padding: 40 }}><Text type="secondary">Không có câu hỏi</Text></div>
            ) : (
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(140px, 1fr))", gap: 12 }}>
                {questions.map(q => (
                  <Card key={q.id} size="small" style={{
                    textAlign: "center",
                    borderColor: uploadStatus[q.id] === "success" ? "#52c41a" : uploadStatus[q.id] === "error" ? "#ff4d4f" : undefined,
                  }}>
                    <Text strong style={{ fontSize: 12 }}>Q{q.order}</Text>
                    <div><Tag style={{ fontSize: 10 }}>{q.toeic_part || q.question_type}</Tag></div>
                    {q.image_url && <img src={q.image_url} alt="" style={{ width: "100%", height: 60, objectFit: "cover", borderRadius: 6, margin: "4px 0" }} />}
                    <label style={{ display: "block", marginTop: 4 }}>
                      <Button size="small" icon={uploadStatus[q.id] === "uploading" ? <Spin size="small" /> : uploadStatus[q.id] === "success" ? <CheckCircleOutlined /> : <PictureOutlined />}
                        type={uploadStatus[q.id] === "success" ? "default" : "primary"} block>
                        {uploadStatus[q.id] === "uploading" ? "..." : uploadStatus[q.id] === "success" ? "✅" : "Upload"}
                      </Button>
                      <input type="file" accept="image/*" hidden onChange={(e) => { const f = e.target.files?.[0]; if (f) handleImageUpload(q.id, f); }} />
                    </label>
                  </Card>
                ))}
              </div>
            )}
          </Card>
        </div>
      </Space>
    </div>
  );
}
