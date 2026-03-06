"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useNotifications } from "@/hooks/useNotifications";

export default function NotificationToast() {
  const { latestToast, clearToast, markAsRead } = useNotifications();
  const [visible, setVisible] = useState(false);
  const [exiting, setExiting] = useState(false);
  const router = useRouter();

  // Show toast when latestToast changes
  useEffect(() => {
    if (!latestToast) return;
    setVisible(true);
    setExiting(false);

    const timer = setTimeout(() => {
      dismiss();
    }, 5000);

    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [latestToast]);

  const dismiss = useCallback(() => {
    setExiting(true);
    setTimeout(() => {
      setVisible(false);
      setExiting(false);
      clearToast();
    }, 300);
  }, [clearToast]);

  const handleClick = async () => {
    if (latestToast) {
      if (!latestToast.is_read) {
        await markAsRead(latestToast.id);
      }
      if (latestToast.link) {
        router.push(latestToast.link);
      }
    }
    dismiss();
  };

  // Touch swipe to dismiss
  const [touchStartX, setTouchStartX] = useState(0);

  if (!visible || !latestToast) return null;

  return (
    <div
      className={`df-notif-toast ${exiting ? "df-notif-toast-exit" : "df-notif-toast-enter"}`}
      onClick={handleClick}
      onTouchStart={(e) => setTouchStartX(e.touches[0].clientX)}
      onTouchEnd={(e) => {
        const diff = e.changedTouches[0].clientX - touchStartX;
        if (Math.abs(diff) > 80) dismiss();
      }}
      role="alert"
    >
      <div className="df-notif-toast-content">
        <span className="df-notif-toast-icon">🔔</span>
        <div className="df-notif-toast-text">
          <span className="df-notif-toast-title">{latestToast.title}</span>
          {latestToast.message && (
            <span className="df-notif-toast-msg">{latestToast.message}</span>
          )}
        </div>
        <button
          className="df-notif-toast-close"
          onClick={(e) => {
            e.stopPropagation();
            dismiss();
          }}
          title="Đóng"
        >
          ×
        </button>
      </div>
    </div>
  );
}
