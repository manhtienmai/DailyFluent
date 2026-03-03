"use client";
import { useState, useEffect, useRef } from "react";
import { Table, Button, Card, Input, Modal, Typography, Space, Spin, Popconfirm, Alert, Progress } from "antd";
import { PlusOutlined, DeleteOutlined, UploadOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import axios from "axios";
import { apiUrl } from "@/lib/api";
import InlineEditCell from "@/components/admin/InlineEditCell";

const { Title, Text } = Typography;
const { TextArea } = Input;

interface Book { id: number; title: string; author: string; cover_image: string | null; pdf_file: string; description: string; created_at: string; }

const API_BASE = apiUrl("/ebooks");

export default function AdminBooksPage() {
  const [books, setBooks] = useState<Book[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState("");
  const formRef = useRef<HTMLFormElement>(null);

  const fetchBooks = () => {
    setLoading(true);
    axios.get(`${API_BASE}/`, { withCredentials: true })
      .then((res) => { setBooks(res.data); setError(""); })
      .catch((err) => { setBooks([]); setError(err?.response?.data?.detail || err?.response?.data?.message || `Lỗi tải danh sách sách (${err?.response?.status || "network"}).`); })
      .finally(() => setLoading(false));
  };
  useEffect(() => { fetchBooks(); }, []);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault(); setError(""); setSubmitting(true);
    const form = formRef.current; if (!form) return;
    const formData = new FormData();
    const title = (form.elements.namedItem("title") as HTMLInputElement).value;
    const author = (form.elements.namedItem("author") as HTMLInputElement).value;
    const description = (form.elements.namedItem("description") as HTMLTextAreaElement).value;
    const coverInput = form.elements.namedItem("cover_image") as HTMLInputElement;
    const pdfInput = form.elements.namedItem("pdf_file") as HTMLInputElement;
    if (!title.trim()) { setError("Vui lòng nhập tên sách."); setSubmitting(false); return; }
    if (!pdfInput.files?.[0]) { setError("Vui lòng chọn file PDF."); setSubmitting(false); return; }
    formData.append("title", title); formData.append("author", author); formData.append("description", description);
    if (coverInput.files?.[0]) formData.append("cover_image", coverInput.files[0]);
    formData.append("pdf_file", pdfInput.files[0]);
    try {
      await axios.post(`${API_BASE}/`, formData, { withCredentials: true, headers: { "Content-Type": "multipart/form-data" } });
      setShowForm(false); form.reset(); fetchBooks();
    } catch (err: any) { setError(err?.response?.data?.detail || err?.response?.data?.message || err?.message || "Có lỗi xảy ra khi tạo sách."); }
    finally { setSubmitting(false); }
  };

  const columns: ColumnsType<Book> = [
    { title: "ID", dataIndex: "id", width: 50, render: (id) => <Text type="secondary" style={{ fontSize: 12, fontFamily: "monospace" }}>{id}</Text> },
    {
      title: "Bìa", dataIndex: "cover_image", width: 70,
      render: (img, book) => img ? (
        <img src={img} alt={book.title} style={{ width: 44, height: 60, objectFit: "cover", borderRadius: 6, border: "1px solid var(--border-subtle)" }} />
      ) : (
        <div style={{ width: 44, height: 60, borderRadius: 6, background: "linear-gradient(135deg, #667eea, #764ba2)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18 }}>📕</div>
      ),
    },
    { title: "Tên sách", dataIndex: "title", render: (_, book) => <InlineEditCell value={book.title} style={{ fontWeight: 600 }} onSave={async (v) => { await axios.patch(`${API_BASE}/${book.id}/`, { title: v }, { withCredentials: true }); fetchBooks(); }} /> },
    { title: "Tác giả", dataIndex: "author", render: (_, book) => <InlineEditCell value={book.author || ""} style={{ color: "var(--text-secondary)" }} onSave={async (v) => { await axios.patch(`${API_BASE}/${book.id}/`, { author: v }, { withCredentials: true }); fetchBooks(); }} /> },
    { title: "Ngày tạo", dataIndex: "created_at", width: 120, render: (d) => <Text style={{ fontSize: 12 }}>{d ? new Date(d).toLocaleDateString("vi-VN") : "—"}</Text> },
    {
      title: "", key: "actions", width: 90, align: "center",
      render: (_, book) => (
        <Popconfirm title={`Xóa sách "${book.title}"?`} onConfirm={async () => { try { await axios.delete(`${API_BASE}/${book.id}`, { withCredentials: true }); fetchBooks(); } catch { /* ignore */ } }} okText="Xoá" cancelText="Huỷ" okButtonProps={{ danger: true }}>
          <Button size="small" danger icon={<DeleteOutlined />}>Xóa</Button>
        </Popconfirm>
      ),
    },
  ];

  return (
    <div>
      <Space orientation="vertical" size="large" style={{ width: "100%" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div><Title level={3} style={{ margin: 0 }}>📕 Thư viện Ebook</Title><Text type="secondary">{books.length} cuốn</Text></div>
          <Button type={showForm ? "default" : "primary"} danger={showForm} icon={showForm ? undefined : <PlusOutlined />} onClick={() => setShowForm(!showForm)}>
            {showForm ? "✕ Đóng" : "Thêm sách mới"}
          </Button>
        </div>

        {showForm && (
          <Card title="📝 Thêm sách mới">
            {error && <Alert type="error" showIcon message={error} style={{ marginBottom: 16 }} />}
            <form ref={formRef} onSubmit={handleSubmit}>
              <Space orientation="vertical" style={{ width: "100%" }} size="middle">
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                  <div><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Tên sách *</Text><Input name="title" placeholder="VD: Minna no Nihongo N4..." required /></div>
                  <div><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Tác giả</Text><Input name="author" placeholder="VD: Sokunbihari Press..." /></div>
                </div>
                <div><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>Mô tả</Text><TextArea name="description" placeholder="Mô tả ngắn..." rows={3} /></div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                  <div><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>🖼️ Ảnh bìa (JPG/PNG)</Text><input name="cover_image" type="file" accept="image/*" style={{ width: "100%", marginTop: 4 }} /></div>
                  <div><Text type="secondary" style={{ fontSize: 11, fontWeight: 600 }}>📄 File PDF *</Text><input name="pdf_file" type="file" accept=".pdf" required style={{ width: "100%", marginTop: 4 }} /></div>
                </div>
                <Button type="primary" htmlType="submit" icon={<UploadOutlined />} loading={submitting} disabled={submitting}>
                  {submitting ? "Đang upload..." : "Upload sách"}
                </Button>
              </Space>
            </form>
          </Card>
        )}

        <Table<Book> columns={columns} dataSource={books} rowKey="id" loading={loading} size="middle" pagination={false} />
      </Space>
    </div>
  );
}
