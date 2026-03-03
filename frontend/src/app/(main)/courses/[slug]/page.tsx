"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";

interface Lesson { slug: string; title: string; order: number; is_completed: boolean; estimated_minutes: number; }
interface CourseData { slug: string; title: string; description: string; lessons: Lesson[]; enrolled: boolean; progress: number; }

export default function CourseDetailPage() {
  const params = useParams();
  const slug = params.slug as string;
  const [course, setCourse] = useState<CourseData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/v1/courses/${slug}`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((d: CourseData) => { setCourse(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, [slug]);

  if (loading) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Đang tải...</div>;
  if (!course) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Không tìm thấy khóa học.</div>;

  return (
    <div style={{ maxWidth: 800, margin: "0 auto", padding: "2rem 1rem" }}>
      <Link href="/courses" className="text-sm no-underline mb-4 inline-block" style={{ color: "var(--text-tertiary)" }}>← Tất cả khóa học</Link>

      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-2" style={{ color: "var(--text-primary)" }}>{course.title}</h1>
        <p className="text-sm mb-4" style={{ color: "var(--text-secondary)" }}>{course.description}</p>
        {course.enrolled && (
          <div className="flex items-center gap-3">
            <div className="flex-1 h-2 rounded-full overflow-hidden" style={{ background: "var(--border-default)" }}>
              <div className="h-full rounded-full" style={{ background: "#10b981", width: `${course.progress}%` }} />
            </div>
            <span className="text-sm font-semibold" style={{ color: "#10b981" }}>{course.progress}%</span>
          </div>
        )}
      </div>

      <div className="space-y-2">
        {course.lessons?.map((l) => (
          <Link key={l.slug} href={`/courses/${slug}/lessons/${l.slug}`} className="flex items-center gap-4 p-4 rounded-xl no-underline transition-all hover:translate-x-1" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
            <div className="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0" style={{
              background: l.is_completed ? "#10b981" : "var(--bg-interactive)",
              color: l.is_completed ? "white" : "var(--text-secondary)",
            }}>{l.is_completed ? "✓" : l.order}</div>
            <div className="flex-1">
              <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>{l.title}</span>
            </div>
            <span className="text-xs" style={{ color: "var(--text-tertiary)" }}>{l.estimated_minutes} phút</span>
          </Link>
        ))}
      </div>
    </div>
  );
}
