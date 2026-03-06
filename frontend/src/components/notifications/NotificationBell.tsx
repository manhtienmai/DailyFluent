"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useNotifications } from "@/hooks/useNotifications";
import NotificationDropdown from "./NotificationDropdown";

export default function NotificationBell() {
  const { unreadCount } = useNotifications();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const bellRef = useRef<HTMLButtonElement>(null);
  const router = useRouter();

  // Detect mobile
  useEffect(() => {
    const check = () => setIsMobile(window.innerWidth < 768);
    check();
    window.addEventListener("resize", check);
    return () => window.removeEventListener("resize", check);
  }, []);

  // Close dropdown on click outside
  useEffect(() => {
    if (!dropdownOpen) return;
    const handler = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (!target.closest(".df-notif-bell-wrap")) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [dropdownOpen]);

  const handleClick = () => {
    if (isMobile) {
      router.push("/notifications");
    } else {
      setDropdownOpen((prev) => !prev);
    }
  };

  return (
    <div className="df-notif-bell-wrap">
      <button
        ref={bellRef}
        className="df-topbar-btn df-notif-bell"
        onClick={handleClick}
        title="Thông báo"
        id="notification-bell"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
          <path d="M13.73 21a2 2 0 0 1-3.46 0" />
        </svg>
        {unreadCount > 0 && (
          <span className="df-notif-badge">
            {unreadCount > 99 ? "99+" : unreadCount}
          </span>
        )}
      </button>

      {dropdownOpen && !isMobile && (
        <NotificationDropdown onClose={() => setDropdownOpen(false)} />
      )}
    </div>
  );
}
