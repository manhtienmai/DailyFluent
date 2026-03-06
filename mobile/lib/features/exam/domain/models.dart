/// Exam domain models.

class ExamCategory {
  final String slug;
  final String title;
  final String icon;
  final int count;

  const ExamCategory({
    required this.slug,
    required this.title,
    this.icon = '📝',
    this.count = 0,
  });

  factory ExamCategory.fromJson(Map<String, dynamic> json) => ExamCategory(
        slug: json['slug'] ?? '',
        title: json['title'] ?? '',
        icon: json['icon'] ?? '📝',
        count: json['count'] ?? 0,
      );
}

class ExamTemplate {
  final int id;
  final String title;
  final String slug;
  final String description;
  final int timeLimitMinutes;
  final int questionCount;
  final String? category;

  const ExamTemplate({
    required this.id,
    required this.title,
    required this.slug,
    this.description = '',
    this.timeLimitMinutes = 60,
    this.questionCount = 0,
    this.category,
  });

  factory ExamTemplate.fromJson(Map<String, dynamic> json) => ExamTemplate(
        id: json['id'] ?? 0,
        title: json['title'] ?? '',
        slug: json['slug'] ?? '',
        description: json['description'] ?? '',
        timeLimitMinutes: json['time_limit_minutes'] ?? json['time_limit'] ?? 60,
        questionCount: json['question_count'] ?? json['total_questions'] ?? 0,
        category: json['category'],
      );
}

class ExamQuestion {
  final int id;
  final String text;
  final String? passage;
  final List<ExamChoice> choices;
  final String correctKey;
  final String? explanation;
  final String? audioUrl;
  final String? imageUrl;

  const ExamQuestion({
    required this.id,
    required this.text,
    this.passage,
    required this.choices,
    required this.correctKey,
    this.explanation,
    this.audioUrl,
    this.imageUrl,
  });

  factory ExamQuestion.fromJson(Map<String, dynamic> json) => ExamQuestion(
        id: json['id'] ?? 0,
        text: json['text'] ?? json['question'] ?? '',
        passage: json['passage'],
        choices: (json['choices'] as List? ?? json['options'] as List? ?? [])
            .map((e) => ExamChoice.fromJson(e is Map<String, dynamic>
                ? e
                : {'text': e.toString()}))
            .toList(),
        correctKey: json['correct_key'] ?? json['answer'] ?? '',
        explanation: json['explanation'],
        audioUrl: json['audio_url'],
        imageUrl: json['image_url'],
      );
}

class ExamChoice {
  final String key;
  final String text;

  const ExamChoice({required this.key, required this.text});

  factory ExamChoice.fromJson(Map<String, dynamic> json) => ExamChoice(
        key: json['key'] ?? json['label'] ?? '',
        text: json['text'] ?? json['content'] ?? '',
      );
}

class QuizResult {
  final int id;
  final String quizType;
  final String quizId;
  final int totalQuestions;
  final int correctCount;
  final double score;
  final String completedAt;

  const QuizResult({
    required this.id,
    required this.quizType,
    required this.quizId,
    required this.totalQuestions,
    required this.correctCount,
    required this.score,
    required this.completedAt,
  });

  factory QuizResult.fromJson(Map<String, dynamic> json) => QuizResult(
        id: json['id'],
        quizType: json['quiz_type'] ?? '',
        quizId: json['quiz_id'] ?? '',
        totalQuestions: json['total_questions'] ?? 0,
        correctCount: json['correct_count'] ?? 0,
        score: (json['score'] as num?)?.toDouble() ?? 0,
        completedAt: json['completed_at'] ?? '',
      );
}
