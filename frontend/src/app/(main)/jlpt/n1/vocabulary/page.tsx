"use client";

import { useState, useEffect, useMemo } from "react";
import "./n1-vocab.css";

interface VocabItem {
  id: number;
  stt: number;
  char: string;
  onyomi: string;
  kunyomi: string;
  sino_vi: string;
  meaning_vi: string;
  lesson_number: number;
  lesson_topic: string;
}

export default function N1VocabularyPage() {
  const [items, setItems] = useState<VocabItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filterLesson, setFilterLesson] = useState<number | null>(null);

  useEffect(() => {
    fetch("/api/v1/kanji/n1-vocab", { credentials: "include" })
      .then((r) => r.json())
      .then((data: VocabItem[]) => {
        setItems(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  // Unique lessons for filter
  const lessons = useMemo(() => {
    const map = new Map<number, string>();
    items.forEach((i) => map.set(i.lesson_number, i.lesson_topic));
    return Array.from(map.entries()).sort((a, b) => a[0] - b[0]);
  }, [items]);

  // Filtered items
  const filtered = useMemo(() => {
    let result = items;
    if (filterLesson !== null) {
      result = result.filter((i) => i.lesson_number === filterLesson);
    }
    if (search.trim()) {
      const q = search.trim().toLowerCase();
      result = result.filter(
        (i) =>
          i.char.includes(q) ||
          i.onyomi.toLowerCase().includes(q) ||
          i.sino_vi.toLowerCase().includes(q) ||
          i.meaning_vi.toLowerCase().includes(q)
      );
    }
    return result;
  }, [items, filterLesson, search]);

  if (loading) {
    return (
      <div className="n1v-loading">
        <div className="n1v-spinner" />
        <p>Đang tải từ vựng N1...</p>
      </div>
    );
  }

  return (
    <div className="n1v-page">
      {/* Header */}
      <div className="n1v-header">
        <div className="n1v-header-left">
          <h1 className="n1v-title">
            <span className="n1v-badge">N1</span>
            Từ vựng JLPT N1
          </h1>
          <p className="n1v-subtitle">
            {items.length} từ vựng · {lessons.length} bài
          </p>
        </div>
      </div>

      {/* Toolbar */}
      <div className="n1v-toolbar">
        <div className="n1v-search-wrap">
          <svg className="n1v-search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8" />
            <path d="M21 21l-4.35-4.35" />
          </svg>
          <input
            className="n1v-search"
            placeholder="Tìm kiếm từ vựng, cách đọc, Hán Việt..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          {search && (
            <button className="n1v-search-clear" onClick={() => setSearch("")}>
              ✕
            </button>
          )}
        </div>
        <div className="n1v-filters">
          <button
            className={`n1v-filter-btn ${filterLesson === null ? "active" : ""}`}
            onClick={() => setFilterLesson(null)}
          >
            Tất cả
          </button>
          {lessons.map(([num, topic]) => (
            <button
              key={num}
              className={`n1v-filter-btn ${filterLesson === num ? "active" : ""}`}
              onClick={() => setFilterLesson(filterLesson === num ? null : num)}
              title={topic}
            >
              Bài {num}
            </button>
          ))}
        </div>
      </div>

      {/* Results count */}
      <div className="n1v-results-info">
        Hiển thị <strong>{filtered.length}</strong> / {items.length} từ vựng
      </div>

      {/* Table */}
      <div className="n1v-table-wrap">
        <table className="n1v-table">
          <thead>
            <tr>
              <th className="n1v-th-stt">STT</th>
              <th className="n1v-th-char">Từ vựng</th>
              <th className="n1v-th-reading">Cách đọc</th>
              <th className="n1v-th-hanviet">Hán Việt</th>
              <th className="n1v-th-meaning">Nghĩa tiếng Việt</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((item) => (
              <tr key={item.id} className="n1v-row">
                <td className="n1v-td-stt">{item.stt}</td>
                <td className="n1v-td-char">{item.char}</td>
                <td className="n1v-td-reading">{item.onyomi || item.kunyomi}</td>
                <td className="n1v-td-hanviet">{item.sino_vi}</td>
                <td className="n1v-td-meaning">{item.meaning_vi}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {filtered.length === 0 && (
        <div className="n1v-empty">
          <p>Không tìm thấy từ vựng phù hợp.</p>
        </div>
      )}
    </div>
  );
}
