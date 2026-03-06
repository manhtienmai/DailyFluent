/**
 * Vocab progress — localStorage utility for tracking learned words per topic.
 *
 * Key format: `vocab_learned_{topicSlug}` → string[] of word strings
 */

const PREFIX = "vocab_learned_";

/** Get learned words for a topic */
export function getLearnedWords(topicSlug: string): string[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(`${PREFIX}${topicSlug}`);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

/** Set learned words for a topic */
export function setLearnedWords(topicSlug: string, words: string[]): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(`${PREFIX}${topicSlug}`, JSON.stringify(words));
}

/** Toggle a word's learned status for a topic. Returns updated list. */
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

/** Get learned count for all topic slugs at once */
export function getAllLearnedCounts(topicSlugs: string[]): Record<string, number> {
  const result: Record<string, number> = {};
  for (const slug of topicSlugs) {
    result[slug] = getLearnedWords(slug).length;
  }
  return result;
}
