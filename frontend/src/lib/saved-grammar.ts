/**
 * Saved Grammar — persists grammar patterns to server API with localStorage cache.
 */

import { getUserPrefSync, setUserPref } from "@/lib/user-prefs";

export interface SavedGrammar {
  id: string;               // unique key (grammar_point text)
  grammar_point: string;     // e.g. "〜にもかかわらず"
  grammar_structure: string; // e.g. "N/Na + にもかかわらず"
  grammar_meaning: string;   // e.g. "Mặc dù ~"
  grammar_note: string;      // additional note
  grammar_furigana: string;  // furigana reading
  level: string;             // JLPT level: N1, N2, N3, N4, N5
  savedAt: string;           // ISO datetime
}

function readList(): SavedGrammar[] {
  return getUserPrefSync<SavedGrammar[]>("saved-grammar") || [];
}

function writeList(list: SavedGrammar[]) {
  setUserPref("saved-grammar", list).catch(() => {});
}

export function getSavedGrammarList(): SavedGrammar[] {
  return readList();
}

export function getSavedGrammarCount(): number {
  return readList().length;
}

export function isGrammarSaved(grammarPoint: string): boolean {
  return readList().some((g) => g.grammar_point === grammarPoint);
}

export function saveGrammar(item: Omit<SavedGrammar, "id" | "savedAt">): SavedGrammar {
  const list = readList();
  const existing = list.find((g) => g.grammar_point === item.grammar_point);
  if (existing) return existing;

  const newItem: SavedGrammar = {
    ...item,
    id: item.grammar_point,
    savedAt: new Date().toISOString(),
  };
  list.unshift(newItem);
  writeList(list);
  return newItem;
}

export function removeGrammar(grammarPoint: string) {
  const list = readList().filter((g) => g.grammar_point !== grammarPoint);
  writeList(list);
}

export function clearAllGrammar() {
  setUserPref("saved-grammar", []).catch(() => {});
}

/** Returns count of saved grammar per JLPT level */
export function getSavedGrammarStats(): Record<string, number> {
  const list = readList();
  const stats: Record<string, number> = {};
  for (const g of list) {
    const lvl = g.level || "?";
    stats[lvl] = (stats[lvl] || 0) + 1;
  }
  return stats;
}

// ── Dismissed grammar ──────────────────────────────────────

function readDismissed(): Set<string> {
  const arr = getUserPrefSync<string[]>("saved-grammar-dismissed");
  return new Set(arr || []);
}

function writeDismissed(set: Set<string>) {
  setUserPref("saved-grammar-dismissed", [...set]).catch(() => {});
}

export function dismissGrammar(grammarPoint: string) {
  const set = readDismissed();
  set.add(grammarPoint);
  writeDismissed(set);
}

export function undismissGrammar(grammarPoint: string) {
  const set = readDismissed();
  set.delete(grammarPoint);
  writeDismissed(set);
}

export function isDismissed(grammarPoint: string): boolean {
  return readDismissed().has(grammarPoint);
}

export function getDismissedSet(): Set<string> {
  return readDismissed();
}

/** Get active (non-dismissed) grammar list */
export function getActiveGrammarList(): SavedGrammar[] {
  const list = readList();
  const dismissed = readDismissed();
  return list.filter((g) => !dismissed.has(g.grammar_point));
}
