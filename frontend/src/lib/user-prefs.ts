/**
 * User Preferences — syncs to server API with localStorage as cache/fallback.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";
const LS_PREFIX = "pref:";

/** Get a single preference. Tries API first, falls back to localStorage. */
export async function getUserPref<T = unknown>(key: string): Promise<T | null> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/user-prefs`, { credentials: "include" });
    if (res.ok) {
      const all = await res.json();
      if (key in all) {
        // Cache to localStorage
        localStorage.setItem(LS_PREFIX + key, JSON.stringify(all[key]));
        return all[key] as T;
      }
      return null;
    }
  } catch {}
  // Fallback to localStorage
  try {
    const raw = localStorage.getItem(LS_PREFIX + key);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

/** Get all preferences. Tries API first, falls back to localStorage scan. */
export async function getAllPrefs(): Promise<Record<string, unknown>> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/user-prefs`, { credentials: "include" });
    if (res.ok) {
      const all = await res.json();
      // Cache all to localStorage
      for (const [k, v] of Object.entries(all)) {
        localStorage.setItem(LS_PREFIX + k, JSON.stringify(v));
      }
      return all;
    }
  } catch {}
  // Fallback: scan localStorage
  const result: Record<string, unknown> = {};
  for (let i = 0; i < localStorage.length; i++) {
    const lsKey = localStorage.key(i);
    if (lsKey?.startsWith(LS_PREFIX)) {
      try {
        result[lsKey.slice(LS_PREFIX.length)] = JSON.parse(localStorage.getItem(lsKey) || "null");
      } catch {}
    }
  }
  return result;
}

/** Set a preference. Writes to API + localStorage cache. */
export async function setUserPref(key: string, value: unknown): Promise<void> {
  // Optimistic: update localStorage immediately
  localStorage.setItem(LS_PREFIX + key, JSON.stringify(value));
  try {
    await fetch(`${API_BASE}/api/v1/user-prefs/${encodeURIComponent(key)}`, {
      method: "PUT",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ value }),
    });
  } catch {
    // API failed, localStorage still has the value
  }
}

/** Delete a preference. */
export async function deleteUserPref(key: string): Promise<void> {
  localStorage.removeItem(LS_PREFIX + key);
  try {
    await fetch(`${API_BASE}/api/v1/user-prefs/${encodeURIComponent(key)}`, {
      method: "DELETE",
      credentials: "include",
    });
  } catch {}
}

// ── Convenience: sync-only helpers (for non-async contexts) ──

/** Read from localStorage cache only (no API call). Use for initial render. */
export function getUserPrefSync<T = unknown>(key: string): T | null {
  try {
    const raw = localStorage.getItem(LS_PREFIX + key);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

// ── Migration helper: move old localStorage keys to new prefixed format ──

const MIGRATION_MAP: Record<string, string> = {
  "grammar_visited": "grammar_visited",
  "saved-grammar": "saved-grammar",
  "saved-grammar-dismissed": "saved-grammar-dismissed",
  "df_study_lang": "study_lang",
  "df-jp-font": "jp_font",
  "theme": "theme",
};

/** One-time migration: copy old localStorage keys to new pref: prefix and sync to server. */
export async function migrateLocalStorage(): Promise<void> {
  const migrated = localStorage.getItem("pref:_migrated");
  if (migrated) return;

  for (const [oldKey, newKey] of Object.entries(MIGRATION_MAP)) {
    const raw = localStorage.getItem(oldKey);
    if (raw !== null) {
      try {
        const value = JSON.parse(raw);
        await setUserPref(newKey, value);
      } catch {
        // Not JSON, store as string
        await setUserPref(newKey, raw);
      }
    }
  }

  // Migrate quiz-progress-* and review-progress-* keys
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (!key) continue;
    if (key.startsWith("quiz-progress-")) {
      try {
        const value = JSON.parse(localStorage.getItem(key) || "null");
        if (value) await setUserPref(key, value);
      } catch {}
    }
    if (key.startsWith("review-progress-")) {
      try {
        const value = JSON.parse(localStorage.getItem(key) || "null");
        if (value) await setUserPref(key, value);
      } catch {}
    }
  }

  localStorage.setItem("pref:_migrated", "1");
}
