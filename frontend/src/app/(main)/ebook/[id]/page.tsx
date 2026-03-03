"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useParams } from "next/navigation";
import { Document, Page, pdfjs } from "react-pdf";
import axios from "axios";
import "./ebook-reader.css";
// CSS imports removed — rendering as canvas-only (no text/annotation layers) for PDF protection

// Configure PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

interface Book {
  id: number;
  title: string;
  author: string;
  cover_image: string | null;
  pdf_file: string;
  description: string;
}

export default function EbookReaderPage() {
  const params = useParams();
  const bookId = params.id as string;

  const [book, setBook] = useState<Book | null>(null);
  const [loading, setLoading] = useState(true);
  const [numPages, setNumPages] = useState(0);
  const [pageNumber, setPageNumber] = useState(1);
  const [scale, setScale] = useState(1.2);
  const [pageInput, setPageInput] = useState("1");
  const [pdfError, setPdfError] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    axios
      .get(`/api/v1/ebooks/${bookId}`, { withCredentials: true })
      .then((res) => setBook(res.data))
      .catch(() => setBook(null))
      .finally(() => setLoading(false));
  }, [bookId]);

  const onDocumentLoadSuccess = useCallback(
    ({ numPages: total }: { numPages: number }) => {
      setNumPages(total);
      setPdfError(false);
    },
    []
  );

  const goToPage = (page: number) => {
    const p = Math.max(1, Math.min(page, numPages));
    setPageNumber(p);
    setPageInput(String(p));
  };

  const prevPage = () => goToPage(pageNumber - 1);
  const nextPage = () => goToPage(pageNumber + 1);

  const handlePageInput = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      const val = parseInt(pageInput, 10);
      if (!isNaN(val)) goToPage(val);
    }
  };

  const zoomIn = () => setScale((s) => Math.min(s + 0.2, 3));
  const zoomOut = () => setScale((s) => Math.max(s - 0.2, 0.5));

  // Keyboard navigation
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
        e.preventDefault();
        prevPage();
      } else if (e.key === "ArrowRight" || e.key === "ArrowDown") {
        e.preventDefault();
        nextPage();
      }
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pageNumber, numPages]);

  if (loading) {
    return (
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          minHeight: "80vh",
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
    );
  }

  if (!book) {
    return (
      <div
        style={{
          textAlign: "center",
          padding: "4rem",
          color: "var(--text-tertiary)",
        }}
      >
        <div style={{ fontSize: "3rem", marginBottom: "1rem" }}>😵</div>
        <p>Không tìm thấy sách.</p>
      </div>
    );
  }

  return (
    <div className="reader-root">
      {/* Control Bar */}
      <div className="reader-controls">
        <div className="reader-controls-inner">
          {/* Book title */}
          <div className="reader-title">{book.title}</div>

          {/* Navigation */}
          <div className="reader-nav">
            <button
              onClick={prevPage}
              disabled={pageNumber <= 1}
              className="reader-btn"
              title="Trang trước (←)"
            >
              ◀
            </button>

            <div className="reader-page-info">
              <input
                type="text"
                value={pageInput}
                onChange={(e) => setPageInput(e.target.value)}
                onKeyDown={handlePageInput}
                onBlur={() => {
                  const val = parseInt(pageInput, 10);
                  if (!isNaN(val)) goToPage(val);
                  else setPageInput(String(pageNumber));
                }}
                className="reader-page-input"
                title="Nhập số trang và nhấn Enter"
              />
              <span className="reader-page-total">/ {numPages}</span>
            </div>

            <button
              onClick={nextPage}
              disabled={pageNumber >= numPages}
              className="reader-btn"
              title="Trang sau (→)"
            >
              ▶
            </button>
          </div>

          {/* Zoom */}
          <div className="reader-zoom">
            <button
              onClick={zoomOut}
              className="reader-btn"
              title="Thu nhỏ"
              disabled={scale <= 0.5}
            >
              −
            </button>
            <span className="reader-zoom-label">
              {Math.round(scale * 100)}%
            </span>
            <button
              onClick={zoomIn}
              className="reader-btn"
              title="Phóng to"
              disabled={scale >= 3}
            >
              +
            </button>
          </div>
        </div>
      </div>

      {/* PDF Viewer */}
      <div className="reader-document" ref={containerRef}>
        {pdfError ? (
          <div
            style={{
              textAlign: "center",
              padding: "4rem",
              color: "var(--text-tertiary)",
            }}
          >
            <div style={{ fontSize: "3rem", marginBottom: "1rem" }}>❌</div>
            <p>Không thể tải file PDF.</p>
          </div>
        ) : (
          <Document
            file={book.pdf_file}
            onLoadSuccess={onDocumentLoadSuccess}
            onLoadError={() => setPdfError(true)}
            loading={
              <div
                style={{
                  display: "flex",
                  justifyContent: "center",
                  alignItems: "center",
                  minHeight: 400,
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
            }
          >
            <Page
              pageNumber={pageNumber}
              scale={scale}
              renderTextLayer={false}
              renderAnnotationLayer={false}
            />
          </Document>
        )}
      </div>

      {/* Styles */}
      
    </div>
  );
}
