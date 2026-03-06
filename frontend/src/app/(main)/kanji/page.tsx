"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import "./kanji.css";

interface KanjiSummary {
  id: number;
  char: string;
  keyword: string;
  sino_vi: string;
  order: number;
}

interface KanjiLesson {
  id: number;
  jlpt_level: string;
  lesson_number: number;
  topic: string;
  order: number;
  kanjis: KanjiSummary[];
}

interface JLPTGroup {
  level: string;
  lessons: KanjiLesson[];
  total_kanji: number;
}

interface KanjiProgressItem {
  kanji_id: number;
  status: string;       // "learning" | "mastered"
  correct_streak: number; // 0–5
}

const MASTERY_THRESHOLD = 5;

export default function KanjiLevelsPage() {
  const [groups, setGroups] = useState<JLPTGroup[]>([]);
  const [activeLevel, setActiveLevel] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [progressMap, setProgressMap] = useState<Record<number, KanjiProgressItem>>({});

  useEffect(() => {
    fetch("/api/v1/kanji/levels", { credentials: "include" })
      .then((res) => res.json())
      .then((data: JLPTGroup[]) => {
        setGroups(data);
        const params = new URLSearchParams(window.location.search);
        const urlLevel = params.get("level");
        if (urlLevel && data.some((g) => g.level === urlLevel)) {
          setActiveLevel(urlLevel);
        } else if (data.length > 0) {
          setActiveLevel(data[0].level);
        }
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to fetch kanji levels:", err);
        setLoading(false);
      });

    // Fetch user progress (non-blocking, graceful on auth errors)
    fetch("/api/v1/kanji/my-progress", { credentials: "include" })
      .then((res) => (res.ok ? res.json() : []))
      .then((items: KanjiProgressItem[]) => {
        const map: Record<number, KanjiProgressItem> = {};
        for (const item of items) {
          map[item.kanji_id] = item;
        }
        setProgressMap(map);
      })
      .catch(() => {
        // Not logged in or error — no progress to show
      });
  }, []);

  const switchLevel = useCallback((level: string) => {
    setActiveLevel(level);
    const url = new URL(window.location.href);
    url.searchParams.set("level", level);
    history.replaceState({}, "", url.toString());
  }, []);

  const [addingVocab, setAddingVocab] = useState(false);
  const [studyMsg, setStudyMsg] = useState("");

  const handleAddAllVocab = useCallback(async () => {
    if (!activeLevel || addingVocab) return;
    setAddingVocab(true);
    setStudyMsg("");
    try {
      const res = await apiFetch<{ added: number; already: number; total: number }>(
        "/api/v1/kanji/vocab/add-all-by-level",
        { method: "POST", body: JSON.stringify({ jlpt_level: activeLevel }) }
      );
      if (res.added > 0) {
        setStudyMsg(`✅ Đã thêm ${res.added} từ vào bộ học (${res.already} từ đã có)`);
      } else {
        setStudyMsg(`📋 Tất cả ${res.total} từ đã có trong bộ học`);
      }
    } catch {
      setStudyMsg("❌ Cần đăng nhập để sử dụng tính năng này");
    } finally {
      setAddingVocab(false);
      setTimeout(() => setStudyMsg(""), 5000);
    }
  }, [activeLevel, addingVocab]);

  const activeGroup = groups.find((g) => g.level === activeLevel);

  if (loading) {
    return (
      <div className="kj-loading">
        <span>Đang tải...</span>
      </div>
    );
  }

  return (
    <div className="kj-page">
      {groups.length > 0 ? (
        <>
          {/* Page Title */}
          <div className="kj-title-row">
            <h1 className="kj-title">
              {activeLevel === "BT" ? "214 Bộ thủ" : `Kanji ${activeLevel}`}
            </h1>
            {activeLevel !== "BT" && (
              <button
                className={`kj-add-all-btn ${addingVocab ? "kj-add-all-btn--loading" : ""}`}
                onClick={handleAddAllVocab}
                disabled={addingVocab}
              >
                {addingVocab ? "⏳ Đang thêm..." : "📚 Học tất cả từ vựng"}
              </button>
            )}
          </div>
          {studyMsg && <div className="kj-study-msg">{studyMsg}</div>}

          {/* Tab bar */}
          <div className="kj-tabs">
            {groups.map((group) => (
              <button
                key={group.level}
                onClick={() => switchLevel(group.level)}
                className={`kj-tab ${group.level === activeLevel ? "kj-tab--active" : ""}`}
              >
                {group.level === "BT" ? "214 Bộ thủ" : group.level}
                <span className="kj-tab-count">{group.total_kanji}</span>
              </button>
            ))}
          </div>

          {/* Lessons */}
          {activeGroup && (
            <div className="kj-lessons">
              {activeGroup.lessons.length > 0 ? (
                activeGroup.lessons.map((lesson) => (
                  <div key={lesson.id} className="kj-lesson">
                    <div className="kj-lesson-header">
                      <h3 className="kj-lesson-title">
                        Bài {lesson.lesson_number}
                      </h3>
                      {lesson.kanjis.length > 0 && (
                        <Link href={`/kanji/quiz/${lesson.id}`} className="kj-quiz-link">
                          🧩 Quiz
                        </Link>
                      )}
                    </div>
                    <p className="kj-lesson-topic">
                      {lesson.jlpt_level === "BT" ? "214 Bộ thủ" : `Kanji ${lesson.jlpt_level}`} - Bài {lesson.lesson_number}: {lesson.topic}
                    </p>

                    {lesson.kanjis.length > 0 ? (
                      <div className="kj-grid">
                        {lesson.kanjis.map((k) => {
                          const prog = progressMap[k.id];
                          const streak = prog?.correct_streak ?? 0;
                          const isMastered = prog?.status === "mastered";
                          const isLearning = streak > 0 && !isMastered;
                          const progressPct = Math.min((streak / MASTERY_THRESHOLD) * 100, 100);

                          let cardClass = "kj-card";
                          if (isMastered) cardClass += " kj-card--learned";
                          else if (isLearning) cardClass += " kj-card--in-progress";

                          return (
                            <Link
                              key={k.id}
                              href={`/kanji/${encodeURIComponent(k.char)}`}
                              className={cardClass}
                            >
                              <span className="kj-char">{k.char}</span>
                              {k.sino_vi && <span className="kj-sino">{k.sino_vi}</span>}
                              <div className="kj-progress-bar">
                                  <div
                                    className={`kj-progress-fill ${isMastered ? "kj-progress-fill--mastered" : ""}`}
                                    style={{ width: `${progressPct}%` }}
                                  />
                                </div>
                            </Link>
                          );
                        })}
                      </div>
                    ) : (
                      <p className="kj-empty-lesson">
                        Chưa có Hán tự nào trong bài này.
                      </p>
                    )}
                  </div>
                ))
              ) : (
                <div className="kj-empty">
                  <p>Chưa có bài học nào cho cấp {activeLevel}.</p>
                </div>
              )}
            </div>
          )}
        </>
      ) : (
        <div className="kj-empty">
          <p>Chưa có dữ liệu Hán tự.</p>
        </div>
      )}
    </div>
  );
}
