"use client";

/**
 * Bunpou Question Page — thin wrapper using shared QuizQuestionPage.
 *
 * SOLID: Open/Closed — adding a new quiz type only requires a new config object,
 * not duplicating 100 lines of page logic.
 */

import QuizQuestionPage from "@/components/quiz/QuizQuestionPage";

const CONFIG = {
  quizType: "bunpou",
  apiUrl: "/api/v1/exam/bunpou/all-questions",
  basePath: "/exam/bunpou/q",
  gridUrl: "/exam/bunpou",
};

export default function BunpouQuestionPage() {
  return <QuizQuestionPage config={CONFIG} />;
}
