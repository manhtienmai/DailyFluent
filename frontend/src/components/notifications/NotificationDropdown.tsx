"use client";

import { useRouter } from "next/navigation";
import { useNotifications, type Notification } from "@/hooks/useNotifications";

// Category icons & colors
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

interface Props {
  onClose: () => void;
}

export default function NotificationDropdown({ onClose }: Props) {
  const { notifications, loading, hasMore, markAsRead, markAllRead, loadMore } =
    useNotifications();
  const router = useRouter();

  const handleItemClick = async (n: Notification) => {
    if (!n.is_read) {
      await markAsRead(n.id);
    }
    if (n.link) {
      router.push(n.link);
    }
    onClose();
  };

  const handleMarkAll = async () => {
    await markAllRead();
  };

  return (
    <div className="df-notif-dropdown" id="notification-dropdown">
      {/* Header */}
      <div className="df-notif-dropdown-header">
        <h3>Thông báo</h3>
        <button
          className="df-notif-mark-all-btn"
          onClick={handleMarkAll}
          title="Đánh dấu tất cả đã đọc"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
            <polyline points="20 6 9 17 4 12" />
          </svg>
          Đọc tất cả
        </button>
      </div>

      {/* List */}
      <div className="df-notif-dropdown-list">
        {loading && notifications.length === 0 ? (
          <div className="df-notif-empty">Đang tải...</div>
        ) : notifications.length === 0 ? (
          <div className="df-notif-empty">
            <span className="df-notif-empty-icon">🔔</span>
            <span>Không có thông báo nào</span>
          </div>
        ) : (
          <>
            {notifications.map((n) => {
              const cat = CATEGORY_CONFIG[n.category] || CATEGORY_CONFIG.system;
              return (
                <button
                  key={n.id}
                  className={`df-notif-item ${n.is_read ? "df-notif-read" : "df-notif-unread"}`}
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

            {hasMore && (
              <button className="df-notif-load-more" onClick={loadMore}>
                Xem thêm
              </button>
            )}
          </>
        )}
      </div>

      {/* Footer */}
      <div className="df-notif-dropdown-footer">
        <button
          className="df-notif-see-all"
          onClick={() => {
            router.push("/notifications");
            onClose();
          }}
        >
          Xem tất cả thông báo
        </button>
      </div>
    </div>
  );
}
