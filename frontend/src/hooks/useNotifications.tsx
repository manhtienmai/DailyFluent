"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useRef,
  type ReactNode,
} from "react";
import { apiFetch, apiUrl } from "@/lib/api";

// ── Types ──────────────────────────────────────────────────

export interface Notification {
  id: number;
  category: string;
  title: string;
  message: string;
  link: string;
  is_read: boolean;
  created_at: string;
}

interface NotificationListResponse {
  items: Notification[];
  total: number;
  page: number;
  has_more: boolean;
}

interface NotificationContextType {
  notifications: Notification[];
  unreadCount: number;
  loading: boolean;
  hasMore: boolean;
  latestToast: Notification | null;
  clearToast: () => void;
  fetchNotifications: (page?: number, append?: boolean) => Promise<void>;
  markAsRead: (id: number) => Promise<void>;
  markAllRead: () => Promise<void>;
  loadMore: () => Promise<void>;
}

// ── Context ────────────────────────────────────────────────

const NotificationContext = createContext<NotificationContextType>({
  notifications: [],
  unreadCount: 0,
  loading: true,
  hasMore: false,
  latestToast: null,
  clearToast: () => {},
  fetchNotifications: async () => {},
  markAsRead: async () => {},
  markAllRead: async () => {},
  loadMore: async () => {},
});

export function useNotifications() {
  return useContext(NotificationContext);
}

// ── Provider ───────────────────────────────────────────────

const POLL_INTERVAL = 30_000; // 30 seconds

export function NotificationProvider({ children }: { children: ReactNode }) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [hasMore, setHasMore] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [latestToast, setLatestToast] = useState<Notification | null>(null);
  const prevUnreadRef = useRef<number>(0);

  // Fetch unread count (lightweight poll)
  const fetchUnreadCount = useCallback(async () => {
    try {
      const data = await apiFetch<{ count: number }>(
        apiUrl("/notifications/unread-count")
      );
      const newCount = data.count;

      // If count increased, show toast for the newest notification
      if (newCount > prevUnreadRef.current && prevUnreadRef.current >= 0) {
        try {
          const list = await apiFetch<NotificationListResponse>(
            apiUrl("/notifications/?page=1")
          );
          if (list.items.length > 0 && !list.items[0].is_read) {
            setLatestToast(list.items[0]);
          }
          // Update the main list too
          setNotifications(list.items);
          setHasMore(list.has_more);
          setCurrentPage(1);
        } catch {
          // ignore
        }
      }

      prevUnreadRef.current = newCount;
      setUnreadCount(newCount);
    } catch {
      // Not logged in or network error
    }
  }, []);

  // Fetch notifications list
  const fetchNotifications = useCallback(
    async (page: number = 1, append: boolean = false) => {
      setLoading(true);
      try {
        const data = await apiFetch<NotificationListResponse>(
          apiUrl(`/notifications/?page=${page}`)
        );
        if (append) {
          setNotifications((prev) => [...prev, ...data.items]);
        } else {
          setNotifications(data.items);
        }
        setHasMore(data.has_more);
        setCurrentPage(page);
      } catch {
        // ignore
      } finally {
        setLoading(false);
      }
    },
    []
  );

  // Load more (pagination)
  const loadMore = useCallback(async () => {
    if (hasMore) {
      await fetchNotifications(currentPage + 1, true);
    }
  }, [hasMore, currentPage, fetchNotifications]);

  // Mark single as read
  const markAsRead = useCallback(
    async (id: number) => {
      try {
        await apiFetch(apiUrl(`/notifications/${id}/read`), { method: "POST" });
        setNotifications((prev) =>
          prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
        );
        setUnreadCount((c) => Math.max(0, c - 1));
      } catch {
        // ignore
      }
    },
    []
  );

  // Mark all as read
  const markAllRead = useCallback(async () => {
    try {
      await apiFetch(apiUrl("/notifications/read-all"), { method: "POST" });
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch {
      // ignore
    }
  }, []);

  // Clear toast
  const clearToast = useCallback(() => setLatestToast(null), []);

  // Initial load + polling
  useEffect(() => {
    fetchNotifications();
    fetchUnreadCount();

    const interval = setInterval(fetchUnreadCount, POLL_INTERVAL);
    return () => clearInterval(interval);
  }, [fetchNotifications, fetchUnreadCount]);

  return (
    <NotificationContext.Provider
      value={{
        notifications,
        unreadCount,
        loading,
        hasMore,
        latestToast,
        clearToast,
        fetchNotifications,
        markAsRead,
        markAllRead,
        loadMore,
      }}
    >
      {children}
    </NotificationContext.Provider>
  );
}
