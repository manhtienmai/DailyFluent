"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

interface CourseSet {
  id: number;
  set_number: number;
  title: string;
  word_count: number;
  status: string;
  chapter: number | null;
  chapter_name: string;
}

interface CourseDetail {
  id: number;
  slug: string;
  title: string;
  description: string;
  language: string;
  cover_image: string | null;
  sets: CourseSet[];
}

interface ChapterGroup {
  chapter: number | null;
  chapter_name: string;
  sets: CourseSet[];
}

/* Doc icon */
const DocIcon = () => (
  <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="1.5" style={{ opacity: 0.4, flexShrink: 0 }}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
  </svg>
);

const ChevronDown = ({ open }: { open: boolean }) => (
  <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2"
    style={{ transition: "transform .2s", transform: open ? "rotate(0deg)" : "rotate(-90deg)", opacity: 0.4, flexShrink: 0 }}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
  </svg>
);

function groupByChapter(sets: CourseSet[]): ChapterGroup[] {
  const groups: ChapterGroup[] = [];
  const map = new Map<string, ChapterGroup>();

  for (const s of sets) {
    const key = s.chapter != null ? String(s.chapter) : "__none__";
    if (!map.has(key)) {
      const g: ChapterGroup = { chapter: s.chapter, chapter_name: s.chapter_name || "", sets: [] };
      map.set(key, g);
      groups.push(g);
    }
    map.get(key)!.sets.push(s);
  }
  return groups;
}

export default function CourseDetailPage() {
  const params = useParams();
  const slug = params.slug as string;

  const [data, setData] = useState<CourseDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [openChapters, setOpenChapters] = useState<Set<string>>(new Set());

  useEffect(() => {
    fetch(`/api/v1/vocab/courses/${slug}`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d: CourseDetail) => {
        setData(d);
        // Auto-open first chapter
        const groups = groupByChapter(d.sets || []);
        if (groups.length > 0) {
          setOpenChapters(new Set([String(groups[0].chapter)]));
        }
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [slug]);

  if (loading) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Đang tải...</div>;
  if (!data) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Không tìm thấy khóa học.</div>;

  const groups = groupByChapter(data.sets || []);
  const hasChapters = groups.some(g => g.chapter != null);

  const toggleChapter = (key: string) => {
    setOpenChapters(prev => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  return (
    <div style={{ padding: "24px", minHeight: "100vh" }}>
      <div style={{ maxWidth: 720, margin: "0 auto" }}>

        {/* Back */}
        <Link href="/vocab/courses" style={{
          display: "inline-flex", alignItems: "center", gap: 6,
          fontSize: 13, color: "var(--text-secondary)", textDecoration: "none", marginBottom: 16,
        }}>
          <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
          Quay lại
        </Link>

        {/* Title */}
        <div style={{ marginBottom: 24 }}>
          <h1 style={{ fontSize: 26, fontWeight: 800, color: "var(--text-primary)", margin: 0, lineHeight: 1.2 }}>
            {data.title}
          </h1>
          <div style={{ fontSize: 13, color: "var(--text-secondary)", marginTop: 4 }}>
            {hasChapters ? `${groups.length} chủ đề` : `${data.sets?.length ?? 0} bài học`}
          </div>
        </div>

        {/* Content */}
        {hasChapters ? (
          /* ─── Grouped by chapter (accordion) ─── */
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {groups.map((g) => {
              const key = String(g.chapter);
              const isOpen = openChapters.has(key);
              return (
                <div key={key} style={{
                  borderRadius: 14, overflow: "hidden",
                  background: "var(--bg-surface)",
                  border: "1px solid var(--border-subtle)",
                }}>
                  {/* Chapter header */}
                  <button
                    onClick={() => toggleChapter(key)}
                    style={{
                      width: "100%", display: "flex", alignItems: "center", gap: 12,
                      padding: "16px 18px", border: "none", cursor: "pointer",
                      background: "transparent", textAlign: "left",
                      borderBottom: isOpen ? "1px solid var(--border-subtle)" : "none",
                    }}
                  >
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <span style={{
                        fontSize: 16, fontWeight: 700, color: "var(--text-primary)",
                        fontFamily: "'Noto Sans JP', sans-serif",
                      }}>
                        {g.chapter_name}
                      </span>
                      <span style={{ fontSize: 12, color: "var(--text-tertiary)", marginLeft: 10 }}>
                        ({g.sets.length} bài)
                      </span>
                    </div>
                    <ChevronDown open={isOpen} />
                  </button>

                  {/* Set list (collapsible) */}
                  {isOpen && (
                    <div>
                      {g.sets.map((s, idx) => (
                        <Link
                          key={s.set_number}
                          href={`/vocab/courses/${slug}/set/${s.set_number}`}
                          style={{
                            display: "flex", alignItems: "center", gap: 12,
                            padding: "12px 18px", textDecoration: "none",
                            borderBottom: idx < g.sets.length - 1 ? "1px solid var(--border-subtle)" : "none",
                            transition: "background .1s",
                          }}
                        >
                          <DocIcon />
                          <div style={{
                            flex: 1, fontSize: 14, fontWeight: 500,
                            color: "var(--text-primary)", lineHeight: 1.4,
                            overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
                          }}>
                            Bài {s.set_number} – {s.title.replace(/^Chủ đề\s*/i, "")}
                          </div>
                          <div style={{ fontSize: 12, color: "var(--text-tertiary)", fontWeight: 500, whiteSpace: "nowrap", flexShrink: 0 }}>
                            {s.word_count} từ
                          </div>
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          /* ─── Flat list (no chapters) ─── */
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {data.sets?.map((s) => (
              <Link
                key={s.set_number}
                href={`/vocab/courses/${slug}/set/${s.set_number}`}
                style={{
                  display: "flex", alignItems: "center", gap: 12,
                  padding: "14px 16px", borderRadius: 12,
                  background: "var(--bg-surface)", border: "1px solid var(--border-subtle)",
                  textDecoration: "none", transition: "background .15s",
                }}
              >
                <DocIcon />
                <div style={{
                  flex: 1, fontSize: 14, fontWeight: 600,
                  color: "var(--text-primary)", lineHeight: 1.4,
                  overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
                }}>
                  Bài {s.set_number} – {s.title.replace(/^Chủ đề\s*/i, "")}
                </div>
                <div style={{ fontSize: 12, color: "var(--text-tertiary)", fontWeight: 500, whiteSpace: "nowrap", flexShrink: 0 }}>
                  {s.word_count} từ
                </div>
              </Link>
            ))}
            {(!data.sets || data.sets.length === 0) && (
              <div style={{ textAlign: "center", padding: "48px 0", color: "var(--text-tertiary)" }}>Chưa có bài học nào.</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
