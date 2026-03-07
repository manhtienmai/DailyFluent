"use client";

import Link from "next/link";
import { useSidebar } from "@/hooks/useSidebar";
import { useAuth } from "@/lib/auth";
import { useState, useEffect, useCallback } from "react";

export default function UserModal() {
  const { userModalOpen, closeUserModal } = useSidebar();
  const { user, logout } = useAuth();

  const userName = user?.first_name || user?.username || "Khách";
  const userEmail = user?.email;
  const userAvatar = user?.avatar_url;

  const handleLogout = async () => {
    closeUserModal();
    await logout();
  };

  // Language switcher
  const [lang, setLang] = useState<"jp" | "en">("jp");
  useEffect(() => {
    const saved = localStorage.getItem("df_study_lang");
    if (saved === "en" || saved === "jp") setLang(saved);
  }, []);

  const handleLangToggle = useCallback(async (newLang: "jp" | "en") => {
    setLang(newLang);
    localStorage.setItem("df_study_lang", newLang);
    // Sync to server
    const { setUserPref } = await import("@/lib/user-prefs");
    setUserPref("study_lang", newLang).catch(() => {});
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
  }, []);

  return (
    <>
      {/* Overlay */}
      <div
        className={`df-user-modal-overlay ${userModalOpen ? "active" : ""}`}
        onClick={closeUserModal}
      />

      {/* Modal */}
      <div className={`df-user-modal ${userModalOpen ? "active" : ""}`}>
        {/* Close button */}
        <button className="df-user-modal-close" onClick={closeUserModal}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>

        {/* Avatar */}
        <div className="df-user-modal-avatar">
          {userAvatar ? (
            <img src={userAvatar} alt={userName} />
          ) : (
            <div
              style={{
                width: "100%",
                height: "100%",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                background: "linear-gradient(135deg, var(--action-primary), var(--action-primary-hover))",
              }}
            >
              <svg width="50" height="50" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
                <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" />
                <circle cx="12" cy="7" r="4" />
              </svg>
            </div>
          )}
        </div>

        {/* Name */}
        <h2 className="df-user-modal-name">{userName}</h2>

        {/* Actions */}
        <div className="df-user-modal-actions">
          <Link href="/profile" className="df-user-modal-btn" onClick={closeUserModal}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" />
              <circle cx="12" cy="7" r="4" />
            </svg>
            Hồ sơ cá nhân
          </Link>
          <Link href="/settings" className="df-user-modal-btn" onClick={closeUserModal}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="3" />
              <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z" />
            </svg>
            Cài đặt
          </Link>
        </div>

        {/* Language Setting */}
        <div style={{ marginBottom: '16px' }}>
          <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px' }}>Ngôn ngữ học</div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={() => handleLangToggle("jp")}
              style={{
                flex: 1, padding: '10px', borderRadius: '10px', border: `2px solid ${lang === 'jp' ? 'var(--text-primary)' : 'var(--border-default)'}`,
                background: lang === 'jp' ? 'var(--text-primary)' : 'var(--bg-surface)',
                color: lang === 'jp' ? 'white' : 'var(--text-secondary)',
                fontWeight: 700, fontSize: '13px', cursor: 'pointer', transition: 'all 0.2s'
              }}
            >
              🇯🇵 JLPT
            </button>
            <button
              onClick={() => handleLangToggle("en")}
              style={{
                flex: 1, padding: '10px', borderRadius: '10px', border: `2px solid ${lang === 'en' ? 'var(--text-primary)' : 'var(--border-default)'}`,
                background: lang === 'en' ? 'var(--text-primary)' : 'var(--bg-surface)',
                color: lang === 'en' ? 'white' : 'var(--text-secondary)',
                fontWeight: 700, fontSize: '13px', cursor: 'pointer', transition: 'all 0.2s'
              }}
            >
              🇺🇸 TOEIC
            </button>
          </div>
        </div>

        {/* Logout */}
        <div className="df-user-modal-logout">
          <button onClick={handleLogout} className="df-user-modal-logout-btn" style={{ background: "none", border: "none", cursor: "pointer", width: "100%" }}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4" />
              <polyline points="16 17 21 12 16 7" />
              <line x1="21" y1="12" x2="9" y2="12" />
            </svg>
            Đăng xuất
          </button>
        </div>
      </div>
    </>
  );
}
