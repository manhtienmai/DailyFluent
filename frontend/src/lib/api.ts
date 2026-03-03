/**
 * Centralized API client for DailyFluent.
 *
 * Uses JWT tokens in httpOnly cookies (sent automatically).
 * Handles 401 → auto-refresh → retry.
 */

/**
 * Base URL for API calls.
 * Uses NEXT_PUBLIC_API_URL when set (direct Django calls via CORS),
 * otherwise falls back to relative path (Next.js rewrite proxy).
 */
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

let isRefreshing = false;
let refreshQueue: (() => void)[] = [];

/**
 * Attempt to refresh the access token.
 * Returns true if refresh succeeded.
 */
async function refreshAccessToken(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/auth/refresh`, {
      method: "POST",
      credentials: "include",
    });
    return res.ok;
  } catch {
    return false;
  }
}

/**
 * Wrapper around fetch with automatic JWT refresh on 401.
 */
export async function apiFetch<T = unknown>(
  url: string,
  options: RequestInit = {}
): Promise<T> {
  const doFetch = async (): Promise<Response> => {
    return fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(options.headers as Record<string, string>),
      },
      credentials: "include",
    });
  };

  let res = await doFetch();

  // If 401, try refreshing the token
  if (res.status === 401) {
    if (!isRefreshing) {
      isRefreshing = true;
      const refreshed = await refreshAccessToken();
      isRefreshing = false;

      // Resolve queued requests
      refreshQueue.forEach((cb) => cb());
      refreshQueue = [];

      if (refreshed) {
        res = await doFetch();
      } else {
        // Refresh failed — redirect to login
        if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
          window.location.href = "/login";
        }
        throw new Error("Session expired");
      }
    } else {
      // Wait for ongoing refresh
      await new Promise<void>((resolve) => refreshQueue.push(resolve));
      res = await doFetch();
    }
  }

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${options.method || "GET"} ${url} failed (${res.status}): ${text}`);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

/**
 * Helper to build API URLs.
 */

export function apiUrl(path: string): string {
  return `${API_BASE}/api/v1${path.startsWith("/") ? path : `/${path}`}`;
}
