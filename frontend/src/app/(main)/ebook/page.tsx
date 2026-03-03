"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import axios from "axios";
import "./ebook.css";

interface Book {
  id: number;
  title: string;
  author: string;
  cover_image: string | null;
  pdf_file: string;
  description: string;
  created_at: string;
}

export default function EbookLibraryPage() {
  const [books, setBooks] = useState<Book[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios
      .get("/api/v1/ebooks/", { withCredentials: true })
      .then((res) => setBooks(res.data))
      .catch(() => setBooks([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div style={{ maxWidth: 1200, margin: "0 auto", padding: "2rem 1rem" }}>
      {/* Header */}
      <div style={{ marginBottom: "2rem" }}>
        <h1
          style={{
            fontSize: "2rem",
            fontWeight: 800,
            color: "var(--text-primary)",
            marginBottom: "0.5rem",
            display: "flex",
            alignItems: "center",
            gap: "0.75rem",
          }}
        >
          📚 Thư viện Ebook
        </h1>
        <p style={{ color: "var(--text-tertiary)", fontSize: "0.95rem" }}>
          Khám phá và đọc ngay các tài liệu học tiếng Nhật
        </p>
      </div>

      {/* Loading */}
      {loading ? (
        <div
          style={{
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            minHeight: 300,
            color: "var(--text-tertiary)",
          }}
        >
          <div
            style={{
              width: 40,
              height: 40,
              border: "3px solid var(--border-default)",
              borderTopColor: "#6366f1",
              borderRadius: "50%",
              animation: "spin 0.8s linear infinite",
            }}
          />
        </div>
      ) : books.length === 0 ? (
        <div
          style={{
            textAlign: "center",
            padding: "4rem 2rem",
            color: "var(--text-tertiary)",
          }}
        >
          <div style={{ fontSize: "3rem", marginBottom: "1rem" }}>📖</div>
          <p style={{ fontSize: "1.1rem" }}>Chưa có sách nào trong thư viện.</p>
        </div>
      ) : (
        /* Book Grid */
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))",
            gap: "1.5rem",
          }}
        >
          {books.map((book) => (
            <div key={book.id} className="ebook-card">
              {/* Cover Image */}
              <div className="ebook-card-cover">
                {book.cover_image ? (
                  <img
                    src={book.cover_image}
                    alt={book.title}
                    style={{
                      width: "100%",
                      height: "100%",
                      objectFit: "cover",
                    }}
                  />
                ) : (
                  <div
                    style={{
                      width: "100%",
                      height: "100%",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontSize: "3rem",
                      background:
                        "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                      color: "rgba(255,255,255,0.6)",
                    }}
                  >
                    📕
                  </div>
                )}
              </div>

              {/* Info */}
              <div className="ebook-card-body">
                <h3 className="ebook-card-title">{book.title}</h3>
                {book.author && (
                  <p className="ebook-card-author">{book.author}</p>
                )}
                {book.description && (
                  <p className="ebook-card-desc">{book.description}</p>
                )}
                <Link href={`/ebook/${book.id}`} className="ebook-card-btn">
                  📖 Đọc ngay
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Scoped styles */}
      
    </div>
  );
}
