"use client";

/**
 * useStudyTimer — tracks time spent on study pages (quiz, flashcard, etc.)
 * Automatically logs study time to the backend every 60 seconds.
 * Also logs remaining time on page unload.
 */

import { useEffect, useRef, useCallback } from "react";

const LOG_INTERVAL_MS = 60_000; // Log every 60 seconds

export function useStudyTimer() {
  const secondsRef = useRef(0);
  const lastLogRef = useRef(0);

  const flush = useCallback(() => {
    const elapsed = secondsRef.current - lastLogRef.current;
    if (elapsed <= 0) return;

    lastLogRef.current = secondsRef.current;

    // Use sendBeacon for reliability on page unload, otherwise fetch
    const payload = JSON.stringify({ seconds: elapsed });
    if (navigator.sendBeacon) {
      const blob = new Blob([payload], { type: "application/json" });
      navigator.sendBeacon("/api/v1/streak/log-minutes", blob);
    } else {
      fetch("/api/v1/streak/log-minutes", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: payload,
        keepalive: true,
      }).catch(() => {});
    }
  }, []);

  useEffect(() => {
    // Tick every second
    const ticker = setInterval(() => {
      secondsRef.current += 1;
    }, 1000);

    // Log to backend periodically
    const logger = setInterval(flush, LOG_INTERVAL_MS);

    // Flush on page unload / visibility change
    const handleUnload = () => flush();
    const handleVisibility = () => {
      if (document.visibilityState === "hidden") flush();
    };

    window.addEventListener("beforeunload", handleUnload);
    document.addEventListener("visibilitychange", handleVisibility);

    return () => {
      clearInterval(ticker);
      clearInterval(logger);
      flush(); // Flush remaining on unmount
      window.removeEventListener("beforeunload", handleUnload);
      document.removeEventListener("visibilitychange", handleVisibility);
    };
  }, [flush]);
}
