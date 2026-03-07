/**
 * Quiz Progress — persists quiz state to server API with localStorage cache.
 * Reusable for any quiz type (usage, grammar, etc.)
 */

import { getUserPrefSync, setUserPref, deleteUserPref } from "@/lib/user-prefs";

export interface QuizProgress {
  answers: Record<string, string>;   // questionId → selected key
  revealed: number[];                // question nums that have been revealed
  bookmarked: number[];              // question nums bookmarked
  lastQuestion: number | null;       // last viewed question num
}

const EMPTY: QuizProgress = { answers: {}, revealed: [], bookmarked: [], lastQuestion: null };

export function getQuizProgress(quizType: string, level: string = ""): QuizProgress {
  const key = `quiz-progress-${quizType}_${level || "all"}`;
  return getUserPrefSync<QuizProgress>(key) || { ...EMPTY };
}

export function saveQuizProgress(quizType: string, level: string, progress: QuizProgress) {
  const key = `quiz-progress-${quizType}_${level || "all"}`;
  setUserPref(key, progress).catch(() => {});
}

export function resetQuizProgress(quizType: string, level: string = "") {
  const key = `quiz-progress-${quizType}_${level || "all"}`;
  deleteUserPref(key).catch(() => {});
}
