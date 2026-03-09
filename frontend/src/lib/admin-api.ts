/**
 * Admin API client for DailyFluent Admin Dashboard.
 *
 * Extends the base apiFetch with admin-specific helpers.
 */

import { apiFetch, apiUrl } from "./api";

// ── Types ──────────────────────────────────────────────────

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface AdminStats {
  today_visitors: number;
  today_views: number;
  users_today: number;
  total_users: number;
  active_now: number;
  peak_hour: string;
  user_growth: number;
  users_month: number;
  users_week: number;
  users_yesterday: number;
  today_users: number;
  total_views: number;
  total_views_week: number;
  total_views_month: number;
  hourly_labels: string[];
  hourly_data: number[];
  user_labels: string[];
  user_data: number[];
  views_labels: string[];
  views_data: number[];
  recent_users: { username: string; email: string; date_joined: string }[];
  top_pages_today: { path: string; views: number }[];
  top_pages_week: { path: string; views: number }[];
  total_vocab?: number;
  total_vocab_sets?: number;
  total_exams?: number;
  total_feedback?: number;
  vocab_today?: number;
  gemini_tokens_today: number;
  gemini_tokens_month: number;
  gemini_calls_today: number;
  gemini_calls_month: number;
  gemini_input_today: number;
  gemini_input_month: number;
  gemini_output_today: number;
  gemini_output_month: number;
  gemini_by_model: { model: string; calls: number; input: number; output: number; total: number }[];
}

// ── Admin API helpers ──────────────────────────────────────

export function adminUrl(path: string): string {
  return apiUrl(`/admin${path.startsWith("/") ? path : `/${path}`}`);
}

export async function adminFetch<T = unknown>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  return apiFetch<T>(adminUrl(path), options);
}

export async function adminGet<T = unknown>(path: string): Promise<T> {
  return adminFetch<T>(path);
}

export async function adminPost<T = unknown>(
  path: string,
  body: unknown
): Promise<T> {
  return adminFetch<T>(path, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function adminPut<T = unknown>(
  path: string,
  body: unknown
): Promise<T> {
  return adminFetch<T>(path, {
    method: "PUT",
    body: JSON.stringify(body),
  });
}

export async function adminPatch<T = unknown>(
  path: string,
  body: unknown
): Promise<T> {
  return adminFetch<T>(path, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export async function adminDelete<T = unknown>(path: string): Promise<T> {
  return adminFetch<T>(path, { method: "DELETE" });
}

/** Upload file(s) via FormData — uses fetch directly to avoid apiFetch's Content-Type: application/json default. */
export async function adminUpload<T = unknown>(
  path: string,
  formData: FormData
): Promise<T> {
  const url = adminUrl(path);
  const res = await fetch(url, {
    method: "POST",
    body: formData,
    credentials: "include",
    // Do NOT set Content-Type — browser auto-sets multipart/form-data with boundary
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API POST ${url} failed (${res.status}): ${text}`);
  }
  return res.json();
}
