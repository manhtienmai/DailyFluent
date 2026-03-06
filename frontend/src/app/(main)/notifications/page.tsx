"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useNotifications, type Notification } from "@/hooks/useNotifications";

const CATEGORIES = [
  { key: "", label: "Tất cả" },
  { key: "study", label: "📚 Học tập" },
  { key: "assignment", label: "📝 Bài tập" },
  { key: "system", label: "⚙️ Hệ thống" },
  { key: "social", label: "💬 Tương tác" },
];

const CATEGORY_CONFIG: Record<string, { icon: string; color: string }> = {
  study: { icon: "📚", color: "var(--notif-study)" },
  system: { icon: "⚙️", color: "var(--notif-system)" },
  social: { icon: "💬", color: "var(--notif-social)" },
  assignment: { icon: "📝", color: "var(--notif-assignment)" },
};

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "Vừa xong";
  if (mins < 60) return `${mins} phút trước`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours} giờ trước`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days} ngày trước`;
  return new Date(dateStr).toLocaleDateString("vi-VN");
}

export default function NotificationsPage() {
  const {
    notifications,
    loading,
    hasMore,
    markAsRead,
    markAllRead,
    loadMore,
  } = useNotifications();
  const router = useRouter();
  const [activeCategory, setActiveCategory] = useState("");

  const filtered = activeCategory
    ? notifications.filter((n) => n.category === activeCategory)
    : notifications;

  const handleItemClick = async (n: Notification) => {
    if (!n.is_read) {
      await markAsRead(n.id);
    }
    if (n.link) {
      router.push(n.link);
    }
  };

  return (
    <div className="df-notif-page">
      {/* Page Header */}
      <div className="df-notif-page-header">
        <h1>🔔 Thông báo</h1>
        <button className="df-notif-mark-all-btn" onClick={markAllRead}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
            <polyline points="20 6 9 17 4 12" />
          </svg>
          Đọc tất cả
        </button>
      </div>

      {/* Category Tabs */}
      <div className="df-notif-tabs">
        {CATEGORIES.map((cat) => (
          <button
            key={cat.key}
            className={`df-notif-tab ${activeCategory === cat.key ? "df-notif-tab-active" : ""}`}
            onClick={() => setActiveCategory(cat.key)}
          >
            {cat.label}
          </button>
        ))}
      </div>

      {/* Notification List */}
      <div className="df-notif-page-list">
        {loading && filtered.length === 0 ? (
          <div className="df-notif-empty">Đang tải...</div>
        ) : filtered.length === 0 ? (
          <div className="df-notif-empty">
            <span className="df-notif-empty-icon">🔔</span>
            <span>Không có thông báo nào</span>
          </div>
        ) : (
          <>
            {filtered.map((n) => {
              const cat = CATEGORY_CONFIG[n.category] || CATEGORY_CONFIG.system;
              return (
                <button
                  key={n.id}
                  className={`df-notif-item df-notif-item-full ${n.is_read ? "df-notif-read" : "df-notif-unread"}`}
                  onClick={() => handleItemClick(n)}
                >
                  <span className="df-notif-item-icon" style={{ background: cat.color }}>
                    {cat.icon}
                  </span>
                  <div className="df-notif-item-content">
                    <span className="df-notif-item-title">{n.title}</span>
                    {n.message && (
                      <span className="df-notif-item-msg">{n.message}</span>
                    )}
                    <span className="df-notif-item-time">{timeAgo(n.created_at)}</span>
                  </div>
                  {!n.is_read && <span className="df-notif-item-dot" />}
                </button>
              );
            })}

            {hasMore && !activeCategory && (
              <button className="df-notif-load-more" onClick={loadMore}>
                Xem thêm thông báo
              </button>
            )}
          </>
        )}
      </div>
    </div>
  );
}
