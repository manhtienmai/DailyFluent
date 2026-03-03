"use client";

import { useState, useRef } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";

const TEMPLATES = {
  en: `{
  "language": "en",
  "words": [
    {
      "word": "achieve",
      "part_of_speech": "verb",
      "ipa": "/əˈtʃiːv/",
      "meaning": "đạt được",
      "example": "She worked hard to achieve her goals.",
      "example_trans": "Cô ấy làm việc chăm chỉ để đạt được mục tiêu."
    }
  ]
}`,
  jp: `{
  "language": "jp",
  "words": [
    {
      "word": "食べる",
      "part_of_speech": "verb",
      "reading": "たべる",
      "romaji": "taberu",
      "han_viet": "THỰC",
      "meaning": "ăn",
      "example": "私は寿司を食べる。",
      "example_trans": "Tôi ăn sushi."
    }
  ]
}`,
};

export default function VocabSetImportPage() {
  const params = useParams();
  const pk = params.pk as string;
  const fileRef = useRef<HTMLInputElement>(null);

  const [mode, setMode] = useState<"file" | "text">("file");
  const [fileName, setFileName] = useState("");
  const [jsonText, setJsonText] = useState("");
  const [guide, setGuide] = useState<"en" | "jp">("en");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<{ success?: boolean; message?: string; count?: number } | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setResult(null);
    try {
      const formData = new FormData();
      if (mode === "file" && fileRef.current?.files?.[0]) {
        formData.append("json_file", fileRef.current.files[0]);
      } else {
        formData.append("json_text", jsonText);
      }
      const r = await fetch(`/api/v1/vocab/sets/${pk}/import`, {
        method: "POST", credentials: "include", body: formData,
      });
      const d = await r.json();
      setResult(d);
    } catch { setResult({ success: false, message: "Lỗi kết nối" }); }
    setSubmitting(false);
  };

  return (
    <div style={{ maxWidth: 800, margin: "0 auto", padding: "2rem 1rem" }}>
      <Link href={`/vocab/sets/${pk}`} className="text-sm no-underline mb-6 inline-block" style={{ color: "var(--text-tertiary)" }}>← Quay lại bộ từ</Link>

      <div className="rounded-2xl overflow-hidden" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)" }}>
        <div className="p-6 md:p-8">
          <div className="text-center mb-8">
            <h1 className="text-2xl font-bold mb-2" style={{ color: "var(--text-primary)" }}>Nhập từ vựng</h1>
            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>Tải file JSON hoặc nhập trực tiếp</p>
          </div>

          {result && (
            <div className="p-4 rounded-xl mb-6 text-sm" style={{ background: result.success ? "rgba(220,252,231,.7)" : "rgba(254,226,226,.7)", color: result.success ? "#16a34a" : "#dc2626" }}>
              {result.message || (result.success ? `Đã nhập ${result.count} từ!` : "Lỗi xảy ra")}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            {/* Mode tabs */}
            <div className="flex justify-center mb-6">
              <div className="p-1 rounded-lg" style={{ background: "var(--bg-interactive)" }}>
                {(["file", "text"] as const).map((m) => (
                  <button key={m} type="button" onClick={() => setMode(m)} className="px-6 py-2 rounded-md text-sm font-medium transition-all" style={{
                    background: mode === m ? "var(--bg-surface)" : "transparent",
                    color: mode === m ? "var(--text-primary)" : "var(--text-secondary)",
                    border: "none", cursor: "pointer", boxShadow: mode === m ? "0 1px 3px rgba(0,0,0,.1)" : "none",
                  }}>{m === "file" ? "Tải file lên" : "Nhập trực tiếp"}</button>
                ))}
              </div>
            </div>

            {mode === "file" ? (
              <div className="border-2 border-dashed rounded-xl p-12 text-center transition-all" style={{ borderColor: "var(--border-default)" }}>
                <input type="file" ref={fileRef} accept=".json" className="hidden" onChange={(e) => setFileName(e.target.files?.[0]?.name || "")} />
                <button type="button" onClick={() => fileRef.current?.click()} className="text-4xl mb-4 block mx-auto" style={{ background: "none", border: "none", cursor: "pointer" }}>📄</button>
                <p className="font-medium" style={{ color: "var(--text-primary)" }}>{fileName || "Nhấn để tải lên"}</p>
                <p className="text-xs mt-1" style={{ color: "var(--text-tertiary)" }}>Chỉ chấp nhận file JSON (tối đa 5MB)</p>
              </div>
            ) : (
              <div className="relative">
                <textarea value={jsonText} onChange={(e) => setJsonText(e.target.value)} rows={12} placeholder="Dán JSON của bạn vào đây..." className="w-full p-4 rounded-xl font-mono text-sm border resize-y" style={{ background: "var(--bg-interactive)", borderColor: "var(--border-default)", color: "var(--text-primary)" }} />
                <div className="absolute top-2 right-2 flex gap-2">
                  <button type="button" onClick={() => setJsonText(TEMPLATES[guide])} className="px-2 py-1 text-xs font-semibold rounded" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)", color: "var(--text-secondary)", cursor: "pointer" }}>Dán mẫu</button>
                  <button type="button" onClick={() => setJsonText("")} className="px-2 py-1 text-xs font-semibold rounded" style={{ background: "var(--bg-surface)", border: "1px solid var(--border-default)", color: "var(--text-secondary)", cursor: "pointer" }}>Xóa</button>
                </div>
              </div>
            )}

            {/* Format guide */}
            <div className="mt-8 pt-8" style={{ borderTop: "1px solid var(--border-default)" }}>
              <h2 className="font-bold mb-4" style={{ color: "var(--text-primary)" }}>📖 Hướng dẫn định dạng JSON</h2>
              <div className="flex gap-1 p-1 rounded-lg mb-4 w-fit" style={{ background: "var(--bg-interactive)" }}>
                {(["en", "jp"] as const).map((g) => (
                  <button key={g} type="button" onClick={() => setGuide(g)} className="px-4 py-2 rounded-md text-sm font-medium transition-all" style={{
                    background: guide === g ? "var(--bg-surface)" : "transparent",
                    color: guide === g ? "var(--text-primary)" : "var(--text-secondary)",
                    border: "none", cursor: "pointer",
                  }}>{g === "en" ? "🇺🇸 English" : "🇯🇵 Japanese"}</button>
                ))}
              </div>
              <pre className="p-4 rounded-lg text-sm font-mono overflow-x-auto" style={{ background: "#1e1e1e", color: "#d4d4d4" }}>{TEMPLATES[guide]}</pre>
            </div>

            <div className="mt-8 flex justify-end gap-3 pt-6" style={{ borderTop: "1px solid var(--border-default)" }}>
              <Link href={`/vocab/sets/${pk}`} className="px-5 py-2.5 text-sm font-semibold no-underline" style={{ color: "var(--text-secondary)" }}>Hủy</Link>
              <button type="submit" disabled={submitting || (mode === "file" ? !fileName : !jsonText.trim())} className="px-6 py-2.5 rounded-xl text-sm font-semibold text-white" style={{ background: "#6366f1", opacity: submitting || (mode === "file" ? !fileName : !jsonText.trim()) ? 0.5 : 1, border: "none", cursor: "pointer" }}>
                {submitting ? "Đang nhập..." : "Nhập từ"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
