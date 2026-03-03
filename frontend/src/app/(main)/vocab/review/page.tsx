"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

/**
 * Vocab Review — redirects to the FSRS-powered flashcard page.
 * The old /vocab/review used a non-existent API endpoint.
 */
export default function VocabReviewPage() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/vocab/flashcards");
  }, [router]);
  return (
    <div style={{ padding: "60px 24px", textAlign: "center", color: "var(--text-tertiary)" }}>
      Đang chuyển hướng...
    </div>
  );
}
