/// API base URL and endpoint constants.

class ApiConstants {
  ApiConstants._();

  // ── Base URL ─────────────────────────────────────────────
  // Change this to your production URL
  static const String baseUrl = 'https://dailyfluent.app';
  static const String apiPrefix = '/api/v1';

  // ── Auth ─────────────────────────────────────────────────
  static const String login = '$apiPrefix/auth/login';
  static const String signup = '$apiPrefix/auth/signup';
  static const String refreshToken = '$apiPrefix/auth/refresh';
  static const String logout = '$apiPrefix/auth/logout';
  static const String me = '$apiPrefix/auth/me';

  // ── Kanji ────────────────────────────────────────────────
  static const String kanjiLevels = '$apiPrefix/kanji/levels';
  static const String kanjiMyProgress = '$apiPrefix/kanji/my-progress';
  static String kanjiDetail(String char) => '$apiPrefix/kanji/$char';
  static const String kanjiProgress = '$apiPrefix/kanji/progress';
  static const String kanjiAddToStudy = '$apiPrefix/kanji/add-to-study';
  static String kanjiQuizStatus(int lessonId) =>
      '$apiPrefix/kanji/quiz-status/$lessonId';
  static const String kanjiQuizGenerateOne =
      '$apiPrefix/kanji/quiz-generate-one';
  static String kanjiQuiz(int lessonId) => '$apiPrefix/kanji/quiz/$lessonId';

  // ── Vocab ────────────────────────────────────────────────
  static const String vocabSets = '$apiPrefix/vocab/sets';
  static String vocabSetDetail(int id) => '$apiPrefix/vocab/sets/$id';
  static const String vocabCourses = '$apiPrefix/vocab/courses';
  static String vocabCourseDetail(String slug) =>
      '$apiPrefix/vocab/courses/$slug';
  static String vocabLearnSet(String slug, int setNum) =>
      '$apiPrefix/vocab/courses/$slug/learn/$setNum';
  static String vocabQuizSet(String slug, int setNum) =>
      '$apiPrefix/vocab/courses/$slug/quiz/$setNum';
  static const String vocabFlashcards = '$apiPrefix/vocab/flashcards';
  static const String vocabFlashcardGrade = '$apiPrefix/vocab/flashcards/grade';
  static const String vocabGames = '$apiPrefix/vocab/games';
  static String vocabGameData(String slug) => '$apiPrefix/vocab/games/$slug';
  static String vocabWordDetail(String word) => '$apiPrefix/vocab/words/$word';
  static const String vocabMyWords = '$apiPrefix/vocab/my-words';
  static const String vocabProgress = '$apiPrefix/vocab/progress';
  static const String vocabReviewDue = '$apiPrefix/vocab/review-due';

  // ── Grammar ──────────────────────────────────────────────
  static const String grammarList = '$apiPrefix/grammar/';
  static const String grammarBooks = '$apiPrefix/grammar/books';
  static String grammarBookDetail(String slug) =>
      '$apiPrefix/grammar/books/$slug';
  static String grammarPointDetail(String slug) =>
      '$apiPrefix/grammar/points/$slug';
  static String grammarExercise(String slug) =>
      '$apiPrefix/grammar/exercises/$slug';
  static String grammarExerciseSubmit(String slug) =>
      '$apiPrefix/grammar/exercises/$slug/submit';
  static const String grammarFlashcards = '$apiPrefix/grammar/flashcards';
  static const String grammarFlashcardGrade =
      '$apiPrefix/grammar/flashcards/grade';

  // ── Exam ─────────────────────────────────────────────────
  static const String examHub = '$apiPrefix/exam/hub';
  static const String examToeic = '$apiPrefix/exam/toeic';
  static const String examBooks = '$apiPrefix/exam/books';
  static const String examChoukai = '$apiPrefix/exam/choukai';
  static const String examDokkai = '$apiPrefix/exam/dokkai';
  static const String examUsage = '$apiPrefix/exam/usage';
  static const String examBunpou = '$apiPrefix/exam/bunpou';
  static const String examEnglish = '$apiPrefix/exam/english';
  static String examDetail(String slug) => '$apiPrefix/exam/$slug';

  // ── Streak ───────────────────────────────────────────────
  static const String streakStatus = '$apiPrefix/streak/status';
  static const String streakLogMinutes = '$apiPrefix/streak/log-minutes';
  static const String streakHeatmap = '$apiPrefix/streak/heatmap';
  static const String streakLeaderboard = '$apiPrefix/streak/leaderboard';

  // ── Quiz Results ─────────────────────────────────────────
  static const String quizResults = '$apiPrefix/quiz-results';
  static const String quizResultsLatest = '$apiPrefix/quiz-results/latest';

  // ── Videos ───────────────────────────────────────────────
  static const String videos = '$apiPrefix/videos/';
  static const String videoCategories = '$apiPrefix/videos/categories';
  static String videoDetail(String slug) => '$apiPrefix/videos/$slug';

  // ── Ebooks ───────────────────────────────────────────────
  static const String ebooks = '$apiPrefix/ebooks/';
  static String ebookDetail(String slug) => '$apiPrefix/ebooks/$slug';

  // ── Placement ────────────────────────────────────────────
  static const String placementHome = '$apiPrefix/placement/';
  static const String placementStart = '$apiPrefix/placement/start';
  static String placementNextQuestion(int testId) =>
      '$apiPrefix/placement/test/$testId/next';
  static String placementSubmitAnswer(int testId, int questionId) =>
      '$apiPrefix/placement/test/$testId/answer/$questionId';
  static String placementResult(int testId) =>
      '$apiPrefix/placement/test/$testId/result';
  static const String placementDashboard = '$apiPrefix/placement/dashboard';
  static const String placementLearningPath =
      '$apiPrefix/placement/learning-path';

  // ── Shop & Wallet ────────────────────────────────────────
  static const String walletBalance = '$apiPrefix/wallet/balance';
  static const String shopItems = '$apiPrefix/shop/items';
  static const String shopPurchase = '$apiPrefix/shop/purchase';
  static const String paymentCreate = '$apiPrefix/payment/create';

  // ── Notifications ────────────────────────────────────────
  static const String notifications = '$apiPrefix/notifications/';
  static String notificationRead(int id) =>
      '$apiPrefix/notifications/$id/read';

  // ── Feedback ─────────────────────────────────────────────
  static const String feedback = '$apiPrefix/feedback/';
}
