"use client";

/**
 * Usage Question Page — thin wrapper using shared QuizQuestionPage.
 *
 * SOLID: Open/Closed — adding a new quiz type only requires a new config object,
 * not duplicating 100 lines of page logic.
 */

import QuizQuestionPage from "@/components/quiz/QuizQuestionPage";

const CONFIG = {
  quizType: "usage",
  apiUrl: "/api/v1/exam/usage/all-questions",
  basePath: "/exam/usage/q",
  gridUrl: "/exam/usage",
};

export default function UsageQuestionPage() {
  return <QuizQuestionPage config={CONFIG} />;
}
