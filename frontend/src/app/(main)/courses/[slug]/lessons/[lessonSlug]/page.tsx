"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";

interface LessonData { title: string; course_title: string; course_slug: string; content_html: string; order: number; next_lesson_slug?: string; prev_lesson_slug?: string; }

export default function LessonDetailPage() {
  const params = useParams();
  const courseSlug = params.slug as string;
  const lessonSlug = params.lessonSlug as string;
  const [lesson, setLesson] = useState<LessonData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/v1/courses/${courseSlug}/lessons/${lessonSlug}`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((d: LessonData) => { setLesson(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, [courseSlug, lessonSlug]);

  if (loading) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Đang tải...</div>;
  if (!lesson) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Không tìm thấy bài học.</div>;

  return (
    <div style={{ maxWidth: 800, margin: "0 auto", padding: "2rem 1rem" }}>
      <Link href={`/courses/${courseSlug}`} className="text-sm no-underline mb-4 inline-block" style={{ color: "var(--text-tertiary)" }}>← {lesson.course_title}</Link>

      <h1 className="text-2xl font-bold mb-6" style={{ color: "var(--text-primary)" }}>{lesson.title}</h1>

      <div className="p-6 rounded-2xl mb-8" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
        <div className="prose max-w-none" style={{ color: "var(--text-primary)" }} dangerouslySetInnerHTML={{ __html: lesson.content_html || "<p>Nội dung đang được cập nhật...</p>" }} />
      </div>

      {/* Navigation */}
      <div className="flex justify-between">
        {lesson.prev_lesson_slug ? (
          <Link href={`/courses/${courseSlug}/lessons/${lesson.prev_lesson_slug}`} className="px-5 py-2 rounded-xl text-sm font-semibold no-underline" style={{ background: "var(--bg-interactive)", color: "var(--text-primary)", border: "1px solid var(--border-default)" }}>← Bài trước</Link>
        ) : <div />}
        {lesson.next_lesson_slug ? (
          <Link href={`/courses/${courseSlug}/lessons/${lesson.next_lesson_slug}`} className="px-5 py-2 rounded-xl text-sm font-semibold no-underline text-white" style={{ background: "#6366f1" }}>Bài tiếp →</Link>
        ) : (
          <Link href={`/courses/${courseSlug}`} className="px-5 py-2 rounded-xl text-sm font-semibold no-underline text-white" style={{ background: "#10b981" }}>Hoàn thành ✓</Link>
        )}
      </div>
    </div>
  );
}
