"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import "./letters.css";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

interface LetterSummary {
  number: number;
  title: { vi: string; en: string; ja: string };
  tags: string[];
  mood: string;
}

export default function LettersPage() {
  const [letters, setLetters] = useState<LetterSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE}/api/v1/exam/letters/`)
      .then((r) => r.json())
      .then((data) => setLetters(data.letters || []))
      .catch(() => setLetters([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="letters-page">
      <div className="letters-header">
        <h1>💌 999 Lá thư gửi cho chính mình</h1>
        <p className="subtitle">
          Mỗi ngày một lá thư — nhẹ nhàng, chữa lành, và yêu thương
        </p>
        {!loading && (
          <span className="letters-count">{letters.length} lá thư</span>
        )}
      </div>

      {loading ? (
        <div style={{ textAlign: "center", padding: 40, color: "var(--text-tertiary)" }}>
          Đang tải...
        </div>
      ) : letters.length === 0 ? (
        <div style={{ textAlign: "center", padding: 40, color: "var(--text-tertiary)" }}>
          Chưa có lá thư nào
        </div>
      ) : (
        <div className="letters-grid">
          {letters.map((letter) => (
            <Link
              key={letter.number}
              href={`/letters/${letter.number}`}
              className="letter-card"
            >
              <div className={`letter-num ${letter.mood}`}>
                {letter.number}
              </div>
              <div className="letter-info">
                <h3 className="letter-title-vi">{letter.title.vi}</h3>
                <div className="letter-title-sub">
                  <span>{letter.title.en}</span>
                  <span>{letter.title.ja}</span>
                </div>
              </div>
              <div className="letter-arrow">→</div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
