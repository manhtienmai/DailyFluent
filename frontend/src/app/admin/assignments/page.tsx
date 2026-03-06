"use client";

import { useState, useEffect } from "react";
import { apiFetch, apiUrl } from "@/lib/api";

interface UserInfo {
  id: number;
  username: string;
  email: string;
}

interface AssignmentOut {
  id: number;
  title: string;
  description: string;
  quiz_type: string;
  quiz_id: string;
  link: string;
  due_date: string | null;
  teacher_name: string;
  created_at: string;
}

const QUIZ_TYPE_OPTIONS = [
  { value: "grammar", label: "Grammar (EN)" },
  { value: "bunpou", label: "Bunpou (JP)" },
  { value: "vocab", label: "Vocabulary" },
  { value: "exam", label: "Exam / Test" },
  { value: "kanji", label: "Kanji" },
  { value: "dictation", label: "Dictation" },
  { value: "phrasal-verbs", label: "Phrasal Verbs" },
  { value: "usage", label: "Usage Quiz" },
];

export default function AssignmentsPage() {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [quizType, setQuizType] = useState("grammar");
  const [quizId, setQuizId] = useState("");
  const [link, setLink] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [studentIds, setStudentIds] = useState<number[]>([]);
  const [allStudents, setAllStudents] = useState<UserInfo[]>([]);
  const [assignments, setAssignments] = useState<AssignmentOut[]>([]);
  const [sending, setSending] = useState(false);
  const [message, setMessage] = useState("");
  const [selectAll, setSelectAll] = useState(true);

  // Fetch students list
  useEffect(() => {
    (async () => {
      try {
        const data = await apiFetch<{ results: UserInfo[] }>(
          apiUrl("/admin/crud/users?page_size=500")
        );
        setAllStudents(data.results || []);
      } catch {
        // ignore
      }
    })();
  }, []);

  // Fetch existing assignments
  useEffect(() => {
    (async () => {
      try {
        const data = await apiFetch<AssignmentOut[]>(
          apiUrl("/notifications/assignments")
        );
        setAssignments(data);
      } catch {
        // ignore
      }
    })();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !quizId.trim()) return;

    setSending(true);
    setMessage("");

    try {
      const payload = {
        title,
        description,
        quiz_type: quizType,
        quiz_id: quizId,
        link: link || `/${quizType === "grammar" ? "exam/english/grammar" : quizType}/${quizId}`,
        due_date: dueDate ? new Date(dueDate).toISOString() : null,
        student_ids: selectAll ? [] : studentIds,
      };

      const result = await apiFetch<{ success: boolean; message: string }>(
        apiUrl("/notifications/assignments"),
        { method: "POST", body: JSON.stringify(payload) }
      );

      setMessage(result.message);
      setTitle("");
      setDescription("");
      setQuizId("");
      setLink("");
      setDueDate("");

      // Refresh assignments
      const data = await apiFetch<AssignmentOut[]>(
        apiUrl("/notifications/assignments")
      );
      setAssignments(data);
    } catch (err: unknown) {
      setMessage((err as Error).message || "Có lỗi xảy ra.");
    } finally {
      setSending(false);
    }
  };

  return (
    <div style={{ maxWidth: 800, margin: "0 auto", padding: "24px 16px" }}>
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 24, color: "var(--text-primary)" }}>
        📝 Giao bài tập cho học sinh
      </h1>

      {/* Form */}
      <form
        onSubmit={handleSubmit}
        style={{
          background: "var(--bg-surface)",
          border: "1px solid var(--border-default)",
          borderRadius: "var(--radius-card)",
          padding: 24,
          marginBottom: 32,
          display: "flex",
          flexDirection: "column",
          gap: 16,
        }}
      >
        <div>
          <label style={{ fontSize: 13, fontWeight: 600, color: "var(--text-secondary)", marginBottom: 4, display: "block" }}>
            Tiêu đề bài tập *
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Ví dụ: Ôn tập ngữ pháp Present Simple"
            required
            style={{
              width: "100%",
              padding: "10px 14px",
              border: "1px solid var(--border-default)",
              borderRadius: "var(--radius-input)",
              background: "var(--bg-app)",
              color: "var(--text-primary)",
              fontSize: 14,
            }}
          />
        </div>

        <div>
          <label style={{ fontSize: 13, fontWeight: 600, color: "var(--text-secondary)", marginBottom: 4, display: "block" }}>
            Mô tả
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Mô tả chi tiết về bài tập..."
            rows={3}
            style={{
              width: "100%",
              padding: "10px 14px",
              border: "1px solid var(--border-default)",
              borderRadius: "var(--radius-input)",
              background: "var(--bg-app)",
              color: "var(--text-primary)",
              fontSize: 14,
              resize: "vertical",
            }}
          />
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          <div>
            <label style={{ fontSize: 13, fontWeight: 600, color: "var(--text-secondary)", marginBottom: 4, display: "block" }}>
              Loại bài tập *
            </label>
            <select
              value={quizType}
              onChange={(e) => setQuizType(e.target.value)}
              style={{
                width: "100%",
                padding: "10px 14px",
                border: "1px solid var(--border-default)",
                borderRadius: "var(--radius-input)",
                background: "var(--bg-app)",
                color: "var(--text-primary)",
                fontSize: 14,
              }}
            >
              {QUIZ_TYPE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ fontSize: 13, fontWeight: 600, color: "var(--text-secondary)", marginBottom: 4, display: "block" }}>
              Quiz ID / Topic *
            </label>
            <input
              type="text"
              value={quizId}
              onChange={(e) => setQuizId(e.target.value)}
              placeholder="present-simple, N3:day01..."
              required
              style={{
                width: "100%",
                padding: "10px 14px",
                border: "1px solid var(--border-default)",
                borderRadius: "var(--radius-input)",
                background: "var(--bg-app)",
                color: "var(--text-primary)",
                fontSize: 14,
              }}
            />
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          <div>
            <label style={{ fontSize: 13, fontWeight: 600, color: "var(--text-secondary)", marginBottom: 4, display: "block" }}>
              Link (auto-generated nếu để trống)
            </label>
            <input
              type="text"
              value={link}
              onChange={(e) => setLink(e.target.value)}
              placeholder="/exam/english/grammar/present-simple"
              style={{
                width: "100%",
                padding: "10px 14px",
                border: "1px solid var(--border-default)",
                borderRadius: "var(--radius-input)",
                background: "var(--bg-app)",
                color: "var(--text-primary)",
                fontSize: 14,
              }}
            />
          </div>

          <div>
            <label style={{ fontSize: 13, fontWeight: 600, color: "var(--text-secondary)", marginBottom: 4, display: "block" }}>
              Hạn nộp
            </label>
            <input
              type="datetime-local"
              value={dueDate}
              onChange={(e) => setDueDate(e.target.value)}
              style={{
                width: "100%",
                padding: "10px 14px",
                border: "1px solid var(--border-default)",
                borderRadius: "var(--radius-input)",
                background: "var(--bg-app)",
                color: "var(--text-primary)",
                fontSize: 14,
              }}
            />
          </div>
        </div>

        {/* Student Selection */}
        <div>
          <label style={{ fontSize: 13, fontWeight: 600, color: "var(--text-secondary)", marginBottom: 8, display: "block" }}>
            Giao cho
          </label>
          <div style={{ display: "flex", gap: 12, marginBottom: 8 }}>
            <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13, cursor: "pointer" }}>
              <input
                type="radio"
                checked={selectAll}
                onChange={() => setSelectAll(true)}
              />
              Tất cả học sinh
            </label>
            <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13, cursor: "pointer" }}>
              <input
                type="radio"
                checked={!selectAll}
                onChange={() => setSelectAll(false)}
              />
              Chọn học sinh cụ thể
            </label>
          </div>

          {!selectAll && (
            <div
              style={{
                maxHeight: 200,
                overflowY: "auto",
                border: "1px solid var(--border-default)",
                borderRadius: "var(--radius-input)",
                padding: 8,
              }}
            >
              {allStudents.map((s) => (
                <label
                  key={s.id}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                    padding: "6px 8px",
                    fontSize: 13,
                    cursor: "pointer",
                    borderRadius: 6,
                  }}
                >
                  <input
                    type="checkbox"
                    checked={studentIds.includes(s.id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setStudentIds((p) => [...p, s.id]);
                      } else {
                        setStudentIds((p) => p.filter((id) => id !== s.id));
                      }
                    }}
                  />
                  {s.username} ({s.email})
                </label>
              ))}
            </div>
          )}
        </div>

        <button
          type="submit"
          disabled={sending}
          style={{
            padding: "12px 24px",
            background: "var(--action-primary)",
            color: "var(--action-primary-text)",
            border: "none",
            borderRadius: "var(--radius-button)",
            fontSize: 14,
            fontWeight: 600,
            cursor: sending ? "not-allowed" : "pointer",
            opacity: sending ? 0.7 : 1,
            transition: "all 0.15s ease",
          }}
        >
          {sending ? "Đang gửi..." : "📤 Giao bài tập"}
        </button>

        {message && (
          <div
            style={{
              padding: "10px 14px",
              background: "var(--status-success-subtle)",
              color: "var(--status-success-text)",
              borderRadius: "var(--radius-input)",
              fontSize: 13,
              fontWeight: 500,
            }}
          >
            {message}
          </div>
        )}
      </form>

      {/* Assignments List */}
      <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 16, color: "var(--text-primary)" }}>
        Bài tập đã giao
      </h2>

      {assignments.length === 0 ? (
        <p style={{ color: "var(--text-tertiary)", fontSize: 14 }}>
          Chưa có bài tập nào được giao.
        </p>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {assignments.map((a) => (
            <div
              key={a.id}
              style={{
                padding: 16,
                background: "var(--bg-surface)",
                border: "1px solid var(--border-default)",
                borderRadius: "var(--radius-card)",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <div>
                  <h3 style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)", margin: 0 }}>
                    {a.title}
                  </h3>
                  {a.description && (
                    <p style={{ fontSize: 12, color: "var(--text-secondary)", margin: "4px 0 0" }}>
                      {a.description}
                    </p>
                  )}
                </div>
                <span
                  style={{
                    fontSize: 11,
                    padding: "4px 8px",
                    background: "var(--bg-interactive)",
                    borderRadius: 999,
                    color: "var(--text-secondary)",
                    fontWeight: 600,
                    whiteSpace: "nowrap",
                  }}
                >
                  {a.quiz_type}
                </span>
              </div>
              <div style={{ display: "flex", gap: 16, marginTop: 8, fontSize: 11, color: "var(--text-tertiary)" }}>
                <span>👤 {a.teacher_name}</span>
                <span>📅 {new Date(a.created_at).toLocaleDateString("vi-VN")}</span>
                {a.due_date && <span>⏰ Hạn: {new Date(a.due_date).toLocaleDateString("vi-VN")}</span>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
