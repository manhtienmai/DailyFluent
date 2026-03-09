/**
 * EN9 Vocab progress — API-backed utility for tracking learned words per topic.
 *
 * Primary: syncs with server via /api/v1/exam/english/en9-vocab-progress
 * Fallback: localStorage for non-authenticated users
 */

const PREFIX = "en9_vocab_learned_";
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

export function getLearnedWords(topicSlug: string): string[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(`${PREFIX}${topicSlug}`);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export function setLearnedWords(topicSlug: string, words: string[]): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(`${PREFIX}${topicSlug}`, JSON.stringify(words));
}

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

export function getAllLearnedCounts(topicSlugs: string[]): Record<string, number> {
  const result: Record<string, number> = {};
  for (const slug of topicSlugs) {
    result[slug] = getLearnedWords(slug).length;
  }
  return result;
}

export async function fetchAllLearnedWordsAPI(): Promise<Record<string, string[]>> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/exam/english/en9-vocab-progress`, {
      credentials: "include",
    });
    if (!res.ok) return {};
    const data = await res.json();
    for (const [slug, words] of Object.entries(data)) {
      setLearnedWords(slug, words as string[]);
    }
    return data;
  } catch {
    return {};
  }
}

export async function toggleLearnedWordAPI(
  topicSlug: string,
  word: string
): Promise<string[]> {
  const updated = toggleLearnedWord(topicSlug, word);
  try {
    const res = await fetch(
      `${API_BASE}/api/v1/exam/english/en9-vocab-progress/${topicSlug}`,
      {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ word }),
      }
    );
    if (res.ok) {
      const data = await res.json();
      setLearnedWords(topicSlug, data.learned_words);
      return data.learned_words;
    }
  } catch {
    // API failed, localStorage still has optimistic update
  }
  return updated;
}

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
    return getAllLearnedCounts(topicSlugs);
  }
}
