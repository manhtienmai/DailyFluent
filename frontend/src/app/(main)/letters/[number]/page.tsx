"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import "../letters.css";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

interface JaParagraph {
  text: string;
  reading: string;
}

interface LetterData {
  number: number;
  title: { vi: string; en: string; ja: string };
  content: {
    vi: string;
    en: string;
    ja: JaParagraph[];
  };
  tags: string[];
  mood: string;
  prev: number | null;
  next: number | null;
  total: number;
}

type Lang = "vi" | "en" | "ja";

const LANG_LABELS: Record<Lang, string> = {
  vi: "🇻🇳 Tiếng Việt",
  en: "🇺🇸 English",
  ja: "🇯🇵 日本語",
};

export default function LetterDetailPage() {
  const params = useParams();
  const number = Number(params.number);
  const [letter, setLetter] = useState<LetterData | null>(null);
  const [loading, setLoading] = useState(true);
  const [lang, setLang] = useState<Lang>("vi");
  const [showReading, setShowReading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetch(`${API_BASE}/api/v1/exam/letters/${number}`)
      .then((r) => r.json())
      .then((data) => setLetter(data))
      .catch(() => setLetter(null))
      .finally(() => setLoading(false));
  }, [number]);

  if (loading) {
    return (
      <div className="letter-detail-page" style={{ textAlign: "center", padding: 60, color: "var(--text-tertiary)" }}>
        Đang tải...
      </div>
    );
  }

  if (!letter) {
    return (
      <div className="letter-detail-page" style={{ textAlign: "center", padding: 60 }}>
        <p style={{ color: "var(--text-tertiary)" }}>Không tìm thấy lá thư này</p>
        <Link href="/letters" style={{ color: "#6366f1" }}>← Về danh sách</Link>
      </div>
    );
  }

  return (
    <div className="letter-detail-page">
      {/* Header */}
      <div className="letter-detail-header">
        <div className={`letter-detail-number ${letter.mood}`}>
          {letter.number}
        </div>
        <h1 className="letter-detail-title">{letter.title.vi}</h1>
        <p className="letter-detail-title-en">{letter.title.en}</p>
        <p className="letter-detail-title-ja">{letter.title.ja}</p>
        {letter.tags.length > 0 && (
          <div className="letter-tags">
            {letter.tags.map((tag, i) => (
              <span key={i} className="letter-tag">{tag}</span>
            ))}
          </div>
        )}
      </div>

      {/* Language tabs */}
      <div className="letter-lang-tabs">
        {(["vi", "en", "ja"] as Lang[]).map((l) => (
          <button
            key={l}
            className={`letter-lang-tab ${lang === l ? "active" : ""}`}
            onClick={() => setLang(l)}
          >
            {LANG_LABELS[l]}
          </button>
        ))}
      </div>

      {/* Japanese reading toggle */}
      {lang === "ja" && (
        <div style={{ textAlign: "center", marginBottom: 16 }}>
          <button
            onClick={() => setShowReading(!showReading)}
            style={{
              padding: "5px 14px",
              borderRadius: 8,
              border: "1px solid var(--border-light, rgba(0,0,0,0.1))",
              background: showReading ? "rgba(99,102,241,0.1)" : "transparent",
              color: showReading ? "#6366f1" : "var(--text-tertiary)",
              fontSize: "0.8rem",
              fontWeight: 500,
              cursor: "pointer",
              transition: "all 0.2s",
            }}
          >
            {showReading ? "Ẩn furigana" : "Hiện furigana"}
          </button>
        </div>
      )}

      {/* Content */}
      {lang === "ja" ? (
        <div className="letter-content-box ja">
          {letter.content.ja.map((p, i) => (
            <div key={i} className="ja-paragraph">
              <div style={{ whiteSpace: "pre-wrap" }}>{p.text}</div>
              {showReading && p.reading && (
                <span className="ja-reading">{p.reading}</span>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="letter-content-box">
          {letter.content[lang]}
        </div>
      )}

      {/* Navigation */}
      <div className="letter-nav">
        {letter.prev ? (
          <Link href={`/letters/${letter.prev}`} className="letter-nav-btn">
            ← Thư #{letter.prev}
          </Link>
        ) : (
          <span className="letter-nav-btn disabled">← Đầu</span>
        )}

        <Link href="/letters" className="letter-nav-btn" style={{ fontSize: "0.85rem" }}>
          📋 Danh sách
        </Link>

        {letter.next ? (
          <Link href={`/letters/${letter.next}`} className="letter-nav-btn">
            Thư #{letter.next} →
          </Link>
        ) : (
          <span className="letter-nav-btn disabled">Cuối →</span>
        )}
      </div>
    </div>
  );
}
