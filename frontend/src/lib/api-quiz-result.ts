/**
 * API client for quiz results (exercise progress persistence).
 * Works with the QuizResult model on Django backend.
 */

import { apiFetch, apiUrl } from "./api";

export interface AnswerDetail {
  q: number;
  selected: number;
  correct: number;
  is_correct: boolean;
}

export interface QuizResultPayload {
  quiz_type: string;
  quiz_id: string;
  total_questions: number;
  correct_count: number;
  score: number;
  answers_detail: AnswerDetail[];
}

export interface QuizResultResponse {
  id: number;
  quiz_type: string;
  quiz_id: string;
  total_questions: number;
  correct_count: number;
  score: number;
  answers_detail: AnswerDetail[];
  completed_at: string;
}

/**
 * Submit quiz result to backend. Fails silently if not authenticated.
 */
export async function submitQuizResult(
  data: QuizResultPayload
): Promise<QuizResultResponse | null> {
  try {
    return await apiFetch<QuizResultResponse>(apiUrl("/quiz-results"), {
      method: "POST",
      body: JSON.stringify(data),
    });
  } catch {
    return null;
  }
}

/**
 * Get quiz history for a specific quiz type + id.
 */
export async function getQuizHistory(
  quizType: string,
  quizId: string
): Promise<QuizResultResponse[]> {
  try {
    const params = new URLSearchParams({ quiz_type: quizType, quiz_id: quizId });
    return await apiFetch<QuizResultResponse[]>(
      apiUrl(`/quiz-results?${params}`)
    );
  } catch {
    return [];
  }
}

/**
 * Get the latest result for a specific quiz.
 */
export async function getLatestResult(
  quizType: string,
  quizId: string
): Promise<QuizResultResponse | null> {
  try {
    const params = new URLSearchParams({ quiz_type: quizType, quiz_id: quizId });
    return await apiFetch<QuizResultResponse>(
      apiUrl(`/quiz-results/latest?${params}`)
    );
  } catch {
    return null;
  }
}
