/**
 * Vocab progress — API-backed utility for tracking learned words per topic.
 *
 * Primary: syncs with server via /api/v1/exam/english/vocab-progress
 * Fallback: localStorage for non-authenticated users
 *
 * Key format: `vocab_learned_{topicSlug}` → string[] of word strings
 */

const PREFIX = "vocab_learned_";
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

/** Get learned words for a topic (localStorage) */
export function getLearnedWords(topicSlug: string): string[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(`${PREFIX}${topicSlug}`);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

/** Set learned words for a topic (localStorage) */
export function setLearnedWords(topicSlug: string, words: string[]): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(`${PREFIX}${topicSlug}`, JSON.stringify(words));
}

/** Toggle a word's learned status for a topic (localStorage). Returns updated list. */
export function toggleLearnedWord(topicSlug: string, word: string): string[] {
  const current = getLearnedWords(topicSlug);
  const idx = current.indexOf(word);
  if (idx >= 0) {
    current.splice(idx, 1);
  } else {
    current.push(word);
  }
  setLearnedWords(topicSlug, current);
  return current;
}

/** Get learned count for all topic slugs at once (localStorage) */
export function getAllLearnedCounts(topicSlugs: string[]): Record<string, number> {
  const result: Record<string, number> = {};
  for (const slug of topicSlugs) {
    result[slug] = getLearnedWords(slug).length;
  }
  return result;
}

// ── API-backed functions ──────────────────────────────────

/** Fetch all learned words from server for all topics. Returns {slug: [words]}. */
export async function fetchAllLearnedWordsAPI(): Promise<Record<string, string[]>> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/exam/english/vocab-progress`, {
      credentials: "include",
    });
    if (!res.ok) return {};
    const data = await res.json();
    // Also sync to localStorage as cache
    for (const [slug, words] of Object.entries(data)) {
      setLearnedWords(slug, words as string[]);
    }
    return data;
  } catch {
    return {};
  }
}

/** Toggle a word via API. Returns updated word list for the topic. */
export async function toggleLearnedWordAPI(
  topicSlug: string,
  word: string
): Promise<string[]> {
  // Optimistic: update localStorage immediately
  const updated = toggleLearnedWord(topicSlug, word);

  try {
    const res = await fetch(
      `${API_BASE}/api/v1/exam/english/vocab-progress/${topicSlug}`,
      {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ word }),
      }
    );
    if (res.ok) {
      const data = await res.json();
      // Sync server response back to localStorage
      setLearnedWords(topicSlug, data.learned_words);
      return data.learned_words;
    }
  } catch {
    // API failed, localStorage still has the optimistic update
  }
  return updated;
}

/** Fetch learned counts from API, returns {slug: count}. Falls back to localStorage. */
export async function fetchLearnedCountsAPI(
  topicSlugs: string[]
): Promise<Record<string, number>> {
  try {
    const allWords = await fetchAllLearnedWordsAPI();
    const result: Record<string, number> = {};
    for (const slug of topicSlugs) {
      result[slug] = (allWords[slug] || []).length;
    }
    return result;
  } catch {
    // Fallback to localStorage
    return getAllLearnedCounts(topicSlugs);
  }
}
