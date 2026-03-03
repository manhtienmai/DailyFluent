"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

interface SetWord {
  item_id: number;
  word: string;
  language: string;
  part_of_speech: string;
  ipa: string;
  audio_us?: string;
  audio_uk?: string;
  meaning: string;
  examples?: { sentence: string; translation: string }[];
}

interface SetInfo {
  id: number;
  title: string;
  description: string;
  word_count: number;
  language: string;
  toeic_level: number | null;
  set_number: number | null;
  course_title: string | null;
}

interface SetData {
  set: SetInfo;
  words: SetWord[];
}

export default function SetDetailPage() {
  const params = useParams();
  const slug = params.slug as string;
  const setNumber = params.setNumber as string;

  const [data, setData] = useState<SetData | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedWord, setExpandedWord] = useState<number | null>(null);

  useEffect(() => {
    fetch(`/api/v1/vocab/courses/${slug}/set/${setNumber}/learn`, {
      credentials: "include",
    })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d: SetData) => {
        setData(d);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [slug, setNumber]);

  if (loading) {
    return (
      <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>
        Đang tải...
      </div>
    );
  }

  if (!data) {
    return (
      <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>
        Không tìm thấy bộ từ này.
      </div>
    );
  }

  const { set: setInfo, words } = data;

  return (
    <div style={{ padding: "24px", minHeight: "100vh" }}>
      <div style={{ maxWidth: 720, margin: "0 auto" }}>
        {/* Breadcrumb */}
        <nav
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            fontSize: "0.82rem",
            color: "var(--text-tertiary, #9ca3af)",
            marginBottom: 20,
          }}
        >
          <Link href="/vocab/courses" style={{ color: "inherit", textDecoration: "none" }}>
            Khóa học
          </Link>
          <span>/</span>
          <Link
            href={`/vocab/courses/${slug}`}
            style={{ color: "inherit", textDecoration: "none" }}
          >
            {setInfo.course_title || slug}
          </Link>
          <span>/</span>
          <span style={{ color: "var(--text-primary, #111)" }}>{setInfo.title}</span>
        </nav>

        {/* Header */}
        <div style={{ marginBottom: 24 }}>
          <h1
            style={{
              fontSize: "1.5rem",
              fontWeight: 700,
              color: "var(--text-primary, #111)",
              margin: "0 0 4px",
            }}
          >
            {setInfo.title}
          </h1>
          {setInfo.description && (
            <p
              style={{
                fontSize: "0.85rem",
                color: "var(--text-secondary, #6b7280)",
                margin: "0 0 8px",
              }}
            >
              {setInfo.description}
            </p>
          )}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 12,
              fontSize: "0.78rem",
              color: "var(--text-tertiary, #9ca3af)",
            }}
          >
            <span>{words.length} từ</span>
            {setInfo.course_title && <span>• {setInfo.course_title}</span>}
          </div>
        </div>

        {/* Action buttons */}
        <div style={{ display: "flex", gap: 12, marginBottom: 28 }}>
          <Link
            href={`/vocab/courses/${slug}/set/${setNumber}/learn`}
            style={{
              flex: 1,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: 8,
              padding: "14px 20px",
              borderRadius: 14,
              background: "linear-gradient(135deg, #6366f1, #8b5cf6)",
              color: "#fff",
              textDecoration: "none",
              fontWeight: 600,
              fontSize: "0.9rem",
              border: "none",
              cursor: "pointer",
            }}
          >
            📖 Học từ mới
          </Link>
          <Link
            href={`/vocab/courses/${slug}/set/${setNumber}/quiz`}
            style={{
              flex: 1,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: 8,
              padding: "14px 20px",
              borderRadius: 14,
              background: "linear-gradient(135deg, #f59e0b, #d97706)",
              color: "#fff",
              textDecoration: "none",
              fontWeight: 600,
              fontSize: "0.9rem",
              border: "none",
              cursor: "pointer",
            }}
          >
            📝 Kiểm tra
          </Link>
        </div>

        {/* Word list */}
        <div>
          <h2
            style={{
              fontSize: "0.9rem",
              fontWeight: 700,
              color: "var(--text-primary, #111)",
              margin: "0 0 12px",
            }}
          >
            Danh sách từ vựng
          </h2>

          {words.length > 0 ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {words.map((w, i) => (
                <div
                  key={w.item_id}
                  onClick={() => setExpandedWord(expandedWord === w.item_id ? null : w.item_id)}
                  style={{
                    padding: "14px 16px",
                    borderRadius: 14,
                    background: "var(--bg-surface, #fff)",
                    border: "1px solid var(--border-default, #e5e7eb)",
                    cursor: "pointer",
                    transition: "border-color 0.15s",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                    <span
                      style={{
                        width: 32,
                        height: 32,
                        borderRadius: 10,
                        background: "var(--bg-interactive, #f3f4f6)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        fontSize: "0.75rem",
                        fontWeight: 600,
                        color: "var(--text-tertiary, #9ca3af)",
                        flexShrink: 0,
                      }}
                    >
                      {i + 1}
                    </span>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
                        <span
                          style={{
                            fontSize: "0.95rem",
                            fontWeight: 600,
                            color: "var(--text-primary, #111)",
                            fontFamily: w.language === "jp" ? "'Noto Sans JP', sans-serif" : "inherit",
                          }}
                        >
                          {w.word}
                        </span>
                        {w.ipa && (
                          <span
                            style={{
                              fontSize: "0.72rem",
                              color: "var(--text-tertiary, #9ca3af)",
                            }}
                          >
                            {w.ipa}
                          </span>
                        )}
                        {w.part_of_speech && (
                          <span
                            style={{
                              fontSize: "0.65rem",
                              color: "#8b5cf6",
                              background: "rgba(139,92,246,.08)",
                              padding: "1px 6px",
                              borderRadius: 4,
                              fontWeight: 500,
                            }}
                          >
                            {w.part_of_speech}
                          </span>
                        )}
                      </div>
                      <div
                        style={{
                          fontSize: "0.82rem",
                          color: "var(--text-secondary, #6b7280)",
                          marginTop: 2,
                        }}
                      >
                        {w.meaning}
                      </div>
                    </div>
                    <svg
                      width="16"
                      height="16"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      style={{
                        color: "var(--text-tertiary, #9ca3af)",
                        flexShrink: 0,
                        transform: expandedWord === w.item_id ? "rotate(180deg)" : "rotate(0deg)",
                        transition: "transform 0.2s",
                      }}
                    >
                      <path d="M6 9l6 6 6-6" />
                    </svg>
                  </div>

                  {/* Expanded content */}
                  {expandedWord === w.item_id && w.examples && w.examples.length > 0 && (
                    <div
                      style={{
                        marginTop: 12,
                        padding: "10px 14px",
                        borderRadius: 10,
                        background: "var(--bg-interactive, #f9fafb)",
                        border: "1px solid var(--border-subtle, #f3f4f6)",
                      }}
                    >
                      {w.examples.map((ex, ei) => (
                        <div key={ei} style={{ marginBottom: ei < w.examples!.length - 1 ? 8 : 0 }}>
                          <div
                            style={{
                              fontSize: "0.82rem",
                              color: "var(--text-primary, #111)",
                              fontFamily: w.language === "jp" ? "'Noto Sans JP', sans-serif" : "inherit",
                            }}
                          >
                            {ex.sentence}
                          </div>
                          {ex.translation && (
                            <div
                              style={{
                                fontSize: "0.75rem",
                                color: "var(--text-tertiary, #9ca3af)",
                                marginTop: 2,
                              }}
                            >
                              {ex.translation}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div
              style={{
                padding: "40px 0",
                textAlign: "center",
                color: "var(--text-tertiary, #9ca3af)",
                fontSize: "0.85rem",
              }}
            >
              Chưa có từ vựng trong bộ này.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
