/**
 * Quiz Progress — localStorage helper for persisting quiz state.
 * Reusable for any quiz type (usage, grammar, etc.)
 */

export interface QuizProgress {
  answers: Record<string, string>;   // questionId → selected key
  revealed: number[];                // question nums that have been revealed
  bookmarked: number[];              // question nums bookmarked
  lastQuestion: number | null;       // last viewed question num
}

const EMPTY: QuizProgress = { answers: {}, revealed: [], bookmarked: [], lastQuestion: null };

export function getQuizProgress(quizType: string, level: string = ""): QuizProgress {
  try {
    const key = `quiz_${quizType}_${level || "all"}`;
    const raw = localStorage.getItem(key);
    if (!raw) return { ...EMPTY };
    return JSON.parse(raw);
  } catch {
    return { ...EMPTY };
  }
}

export function saveQuizProgress(quizType: string, level: string, progress: QuizProgress) {
  try {
    const key = `quiz_${quizType}_${level || "all"}`;
    localStorage.setItem(key, JSON.stringify(progress));
  } catch { /* ignore */ }
}

export function resetQuizProgress(quizType: string, level: string = "") {
  try {
    const key = `quiz_${quizType}_${level || "all"}`;
    localStorage.removeItem(key);
  } catch { /* ignore */ }
}
