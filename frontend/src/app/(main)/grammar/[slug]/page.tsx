"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import s from "./detail.module.css";

interface GrammarExample {
  sentence_jp: string;
  highlighted_jp: string;
  sentence_vi: string;
}

interface ExerciseSet {
  id: number;
  slug: string;
  title: string;
  question_count: number;
}

interface RelatedPoint {
  slug: string;
  title: string;
  meaning_vi: string;
}

interface PointData {
  id: number;
  slug: string;
  title: string;
  reading: string;
  level: string;
  meaning_vi: string;
  formation: string;
  summary: string;
  explanation: string;
  details: string;
  notes: string;
  book_title: string;
  book_slug: string;
  examples: GrammarExample[];
  old_examples: string[];
  exercise_sets: ExerciseSet[];
  related: RelatedPoint[];
  prev_slug: string | null;
  prev_title: string | null;
  next_slug: string | null;
  next_title: string | null;
  best_score: number | null;
}

const levelGradient: Record<string, string> = {
  N5: "linear-gradient(135deg, #34d399, #10b981)",
  N4: "linear-gradient(135deg, #2dd4bf, #14b8a6)",
  N3: "linear-gradient(135deg, #60a5fa, #3b82f6)",
  N2: "linear-gradient(135deg, #a78bfa, #8b5cf6)",
  N1: "linear-gradient(135deg, #fbbf24, #f59e0b)",
};

/**
 * Convert inline furigana 漢字（かな） to <ruby> HTML
 */
function toRubyHtml(text: string): string {
  if (!text) return "";
  let result = text.replace(
    /\{([^}]+)\}\(([^)]+)\)/g,
    "<ruby>$1<rp>(</rp><rt>$2</rt><rp>)</rp></ruby>"
  );
  result = result.replace(
    /([\u4e00-\u9faf\u3400-\u4dbf]+)（([ぁ-ゖァ-ヶー]+)）/g,
    "<ruby>$1<rp>（</rp><rt>$2</rt><rp>）</rp></ruby>"
  );
  return result;
}

export default function GrammarPointDetailPage() {
  const params = useParams();
  const slug = params.slug as string;

  const [data, setData] = useState<PointData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/v1/grammar/points/${slug}`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d: PointData) => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, [slug]);

  if (loading) {
    return (
      <div className={s.loadingWrap}>
        <div className={s.spinner} />
      </div>
    );
  }
  if (!data) {
    return (
      <div className={s.loadingWrap}>
        <p style={{ fontSize: 16, fontWeight: 600 }}>Không tìm thấy</p>
        <Link href="/grammar" style={{ fontSize: 13, color: "var(--action-primary)" }}>← Quay lại</Link>
      </div>
    );
  }

  const gradient = levelGradient[data.level] || levelGradient.N3;
  const hasExamples = (data.examples?.length > 0) || (data.old_examples?.length > 0);

  return (
    <div className={s.page}>
      {/* Breadcrumb */}
      <nav className={s.breadcrumb}>
        <Link href="/grammar">Ngữ pháp</Link>
        <span className={s.breadcrumbSep}>/</span>
        <span className={s.breadcrumbCurrent}>{data.title}</span>
      </nav>

      <div className={s.layout}>
        {/* Main */}
        <main className={s.main}>
          {/* Header Card */}
          <div className={s.header}>
            <div className={s.headerAccent} style={{ background: gradient }} />
            <div className={s.headerBody}>
              <span className={s.level} style={{ background: gradient }}>{data.level}</span>
              <h1 className={s.title}>{data.title}</h1>
              {data.reading && <p className={s.reading}>{data.reading}</p>}
              {data.meaning_vi && <p className={s.meaning}>{data.meaning_vi}</p>}
            </div>
          </div>

          {/* Formation */}
          {data.formation && (
            <div className={s.section}>
              <div className={s.sectionLabel}>📐 Cấu trúc</div>
              <div className={s.formation} dangerouslySetInnerHTML={{ __html: toRubyHtml(data.formation) }} />
            </div>
          )}

          {/* Summary */}
          {data.summary && (
            <div className={s.section}>
              <p className={s.summary}>{data.summary}</p>
            </div>
          )}

          {/* Explanation */}
          {(data.explanation || data.details) && (
            <div className={s.section}>
              <div className={s.sectionLabel}>📖 Giải thích</div>
              <div className={s.text} dangerouslySetInnerHTML={{ __html: toRubyHtml(data.explanation || data.details || "") }} />
            </div>
          )}

          {/* Notes */}
          {data.notes && (
            <div className={s.note}>
              <div className={s.noteIcon}>💡</div>
              <div>
                <div className={s.noteTitle}>Lưu ý</div>
                <div className={s.noteText} dangerouslySetInnerHTML={{ __html: toRubyHtml(data.notes) }} />
              </div>
            </div>
          )}

          {/* Examples */}
          {hasExamples && (
            <div className={s.section}>
              <div className={s.sectionLabel}>✏️ Ví dụ</div>
              <div className={s.examples}>
                {data.examples?.map((ex, i) => (
                  <div key={i} className={s.ex}>
                    <div className={s.exNum}>{i + 1}</div>
                    <div className={s.exContent}>
                      <div className={s.exJp} dangerouslySetInnerHTML={{ __html: toRubyHtml(ex.highlighted_jp || ex.sentence_jp) }} />
                      {ex.sentence_vi && <div className={s.exVi}>{ex.sentence_vi}</div>}
                    </div>
                  </div>
                ))}
                {data.old_examples?.map((ex, i) => {
                  const lines = ex.split("\n").filter(Boolean);
                  return lines.map((line, j) => {
                    const isJp = /[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]/.test(line);
                    return isJp ? (
                      <div key={`old-${i}-${j}`} className={s.ex}>
                        <div className={s.exNum}>{(data.examples?.length || 0) + i + 1}</div>
                        <div className={s.exContent}>
                          <div className={s.exJp} dangerouslySetInnerHTML={{ __html: toRubyHtml(line) }} />
                        </div>
                      </div>
                    ) : (
                      <div key={`old-vi-${i}-${j}`} className={s.exViStandalone}>{line}</div>
                    );
                  });
                })}
              </div>
            </div>
          )}

          {/* Exercises */}
          {data.exercise_sets?.length > 0 && (
            <div className={s.section}>
              <div className={s.sectionLabel}>🎯 Bài tập</div>
              <div className={s.exercises}>
                {data.exercise_sets.map((es) => (
                  <Link key={es.id} href={`/grammar/exercise/${es.slug}`} className={s.exerciseCard}>
                    <div>
                      <div className={s.exerciseTitle}>{es.title}</div>
                      <div className={s.exerciseCount}>{es.question_count} câu hỏi</div>
                    </div>
                    <span className={s.exerciseArrow}>→</span>
                  </Link>
                ))}
              </div>
            </div>
          )}

          {/* Prev / Next */}
          <div className={s.nav}>
            {data.prev_slug ? (
              <Link href={`/grammar/${data.prev_slug}`} className={s.navBtn}>
                <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M15 18l-6-6 6-6" /></svg>
                <span>{data.prev_title}</span>
              </Link>
            ) : <div />}
            {data.next_slug ? (
              <Link href={`/grammar/${data.next_slug}`} className={s.navBtn}>
                <span>{data.next_title}</span>
                <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M9 18l6-6-6-6" /></svg>
              </Link>
            ) : null}
          </div>
        </main>

        {/* Sidebar */}
        <aside className={s.sidebar}>
          {data.best_score != null && (
            <div className={s.sbCard}>
              <div className={s.sbLabel}>Tiến độ</div>
              <div className={s.sbScore}>{data.best_score}%</div>
              <div className={s.sbSub}>Điểm cao nhất</div>
            </div>
          )}
          {data.related?.length > 0 && (
            <div className={s.sbCard}>
              <div className={s.sbLabel}>Liên quan</div>
              <div className={s.sbRelated}>
                {data.related.map((rp, i) => (
                  <Link key={i} href={`/grammar/${rp.slug}`} className={s.sbLink}>
                    <span className={s.sbLinkTitle}>{rp.title}</span>
                    {rp.meaning_vi && <span className={s.sbLinkMeaning}>{rp.meaning_vi}</span>}
                  </Link>
                ))}
              </div>
            </div>
          )}
          {data.book_slug && (
            <Link href={`/grammar/books/${data.book_slug}`} className={s.sbBook}>
              📖 {data.book_title}
            </Link>
          )}
        </aside>
      </div>
    </div>
  );
}
