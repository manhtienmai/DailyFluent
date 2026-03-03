"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

interface Course { slug: string; title: string; description: string; lessons_count: number; enrolled: boolean; progress: number; }

export default function CourseListPage() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/v1/courses", { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((d: Course[]) => { setCourses(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>Đang tải...</div>;

  return (
    <div style={{ maxWidth: 900, margin: "0 auto", padding: "2rem 1rem" }}>
      <h1 className="text-2xl font-bold mb-6" style={{ color: "var(--text-primary)" }}>📚 Khóa học</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {courses.map((c) => (
          <Link key={c.slug} href={`/courses/${c.slug}`} className="p-5 rounded-2xl no-underline transition-all hover:translate-y-[-2px]" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-xl flex items-center justify-center text-lg font-bold text-white flex-shrink-0" style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6)" }}>
                {c.title.slice(0, 2).toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="font-semibold mb-1 truncate" style={{ color: "var(--text-primary)" }}>{c.title}</h3>
                <p className="text-xs mb-2 line-clamp-2" style={{ color: "var(--text-tertiary)" }}>{c.description}</p>
                <div className="flex items-center gap-3 text-xs" style={{ color: "var(--text-tertiary)" }}>
                  <span>📖 {c.lessons_count} bài học</span>
                  {c.enrolled && <span className="font-medium" style={{ color: "#10b981" }}>{c.progress}% hoàn thành</span>}
                </div>
                {c.enrolled && c.progress > 0 && (
                  <div className="mt-2 h-1.5 rounded-full overflow-hidden" style={{ background: "var(--border-default)" }}>
                    <div className="h-full rounded-full" style={{ background: "#10b981", width: `${c.progress}%` }} />
                  </div>
                )}
              </div>
            </div>
          </Link>
        ))}
        {!courses.length && <p className="col-span-2 text-center py-8" style={{ color: "var(--text-tertiary)" }}>Chưa có khóa học nào.</p>}
      </div>
    </div>
  );
}
