"use client";

import Link from "next/link";
import { useSidebar } from "@/hooks/useSidebar";
import { useAuth } from "@/lib/auth";
import { useState, useEffect, useCallback } from "react";

export default function Topbar() {
  const { toggleMobile, openUserModal, toggleTheme, theme } = useSidebar();
  const { user } = useAuth();

  const userName = user?.first_name || user?.username || "Khách";
  const userAvatar = user?.avatar_url;

  // Language switcher
  const [lang, setLang] = useState<"jp" | "en">("jp");
  useEffect(() => {
    const saved = localStorage.getItem("df_study_lang");
    if (saved === "en" || saved === "jp") setLang(saved);
  }, []);

  const handleLangToggle = useCallback(async () => {
    const newLang = lang === "jp" ? "en" : "jp";
    setLang(newLang);
    localStorage.setItem("df_study_lang", newLang);
    try {
      await fetch("/api/set-language/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ language: newLang }),
      });
    } catch (e) {
      console.warn("Failed to save language:", e);
    }
    window.location.reload();
  }, [lang]);

  // Countdown timer
  const [countdown, setCountdown] = useState({ d: "00", h: "00", m: "00", s: "00" });
  useEffect(() => {
    const targetStr =
      typeof window !== "undefined"
        ? (window as unknown as Record<string, unknown>).EXAM_TARGET_DATE as string | undefined
        : undefined;
    if (!targetStr) return;

    const targetDate = new Date(targetStr + "T00:00:00");
    const update = () => {
      const diff = targetDate.getTime() - Date.now();
      if (diff <= 0) {
        setCountdown({ d: "00", h: "00", m: "00", s: "00" });
        return;
      }
      const days = Math.floor(diff / (1000 * 60 * 60 * 24));
      const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
      const mins = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
      const secs = Math.floor((diff % (1000 * 60)) / 1000);
      setCountdown({
        d: String(days).padStart(2, "0"),
        h: String(hours).padStart(2, "0"),
        m: String(mins).padStart(2, "0"),
        s: String(secs).padStart(2, "0"),
      });
    };
    update();
    const id = setInterval(update, 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <header className="df-topbar">
      {/* Mobile menu toggle */}
      <button className="df-topbar-menu-btn" onClick={toggleMobile}>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <line x1="3" y1="12" x2="21" y2="12" />
          <line x1="3" y1="6" x2="21" y2="6" />
          <line x1="3" y1="18" x2="21" y2="18" />
        </svg>
      </button>

      {/* Brand */}
      <Link href="/" className="df-topbar-brand">
        <span className="df-topbar-logo-text">DailyFluent</span>
      </Link>

      {/* Spacer */}
      <div className="df-topbar-spacer" />

      {/* Right side */}
      <div className="df-topbar-right">
        {/* Countdown */}
        <div className="df-topbar-countdown" title="Thời gian đến kỳ thi">
          <span className="df-countdown-value">{countdown.d}</span>
          <span className="df-countdown-unit">d</span>
          <span className="df-countdown-sep">:</span>
          <span className="df-countdown-value">{countdown.h}</span>
          <span className="df-countdown-unit">h</span>
          <span className="df-countdown-sep">:</span>
          <span className="df-countdown-value">{countdown.m}</span>
          <span className="df-countdown-unit">m</span>
          <span className="df-countdown-sep">:</span>
          <span className="df-countdown-value">{countdown.s}</span>
          <span className="df-countdown-unit">s</span>
        </div>

        {/* Language Switcher */}
        <div className="df-lang-switcher" title="Chuyển ngôn ngữ học">
          <button
            onClick={handleLangToggle}
            className={`df-lang-toggle ${lang === "jp" ? "df-lang-jp-active" : "df-lang-en-active"}`}
          >
            <span className={`df-lang-opt df-lang-opt-jp ${lang === "jp" ? "df-lang-opt-active" : ""}`}>
              <span className="df-lang-label">JLPT</span>
            </span>
            <span className={`df-lang-opt df-lang-opt-en ${lang === "en" ? "df-lang-opt-active" : ""}`}>
              <span className="df-lang-label">TOEIC</span>
            </span>
          </button>
        </div>

        {/* Streak */}
        <div className="df-topbar-stat df-topbar-streak" title="Chuỗi ngày học">
          <svg viewBox="0 0 24 24" fill="currentColor" className="df-stat-icon df-streak-icon">
            <path d="M12 23a7.5 7.5 0 0 1-5.138-12.963C8.204 8.774 11.5 6.5 11 1.5c6 4 9 8 3 14 1 0 2.5 0 5-2.47.27.773.5 1.604.5 2.47A7.5 7.5 0 0 1 12 23z" />
          </svg>
          <span className="df-stat-value">0</span>
        </div>

        {/* User Profile */}
        <div className="df-topbar-user" onClick={openUserModal} title="Hồ sơ cá nhân">
          <div className="df-topbar-user-avatar">
            {userAvatar ? (
              <img src={userAvatar} alt="Avatar" />
            ) : (
              <span className="df-topbar-user-initials">
                {userName.slice(0, 2).toUpperCase()}
              </span>
            )}
          </div>
          <div className="df-topbar-user-info">
            <span className="df-topbar-user-name">{userName}</span>
          </div>
        </div>

        {/* Theme Toggle */}
        <button
          className="df-topbar-btn df-theme-toggle"
          onClick={toggleTheme}
          title="Đổi giao diện"
        >
          <svg className="df-theme-icon-light" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="5" />
            <line x1="12" y1="1" x2="12" y2="3" />
            <line x1="12" y1="21" x2="12" y2="23" />
            <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
            <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
            <line x1="1" y1="12" x2="3" y2="12" />
            <line x1="21" y1="12" x2="23" y2="12" />
            <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
            <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
          </svg>
          <svg className="df-theme-icon-dark" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
          </svg>
        </button>
      </div>
    </header>
  );
}
