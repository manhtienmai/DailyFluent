/// Grammar domain models.

class GrammarPoint {
  final int id;
  final String title;
  final String slug;
  final String level;
  final String meaning;
  final String structure;
  final String? explanation;
  final List<String> examples;

  const GrammarPoint({
    required this.id,
    required this.title,
    required this.slug,
    this.level = '',
    this.meaning = '',
    this.structure = '',
    this.explanation,
    this.examples = const [],
  });

  factory GrammarPoint.fromJson(Map<String, dynamic> json) => GrammarPoint(
        id: json['id'],
        title: json['title'] ?? json['pattern'] ?? '',
        slug: json['slug'] ?? '',
        level: json['level'] ?? '',
        meaning: json['meaning'] ?? json['meaning_vi'] ?? '',
        structure: json['structure'] ?? '',
        explanation: json['explanation'],
        examples: (json['examples'] as List?)?.cast<String>() ?? [],
      );
}

class GrammarBook {
  final int id;
  final String title;
  final String slug;
  final String level;
  final int pointCount;

  const GrammarBook({
    required this.id,
    required this.title,
    required this.slug,
    this.level = '',
    this.pointCount = 0,
  });

  factory GrammarBook.fromJson(Map<String, dynamic> json) => GrammarBook(
        id: json['id'],
        title: json['title'] ?? '',
        slug: json['slug'] ?? '',
        level: json['level'] ?? '',
        pointCount: json['point_count'] ?? json['total_points'] ?? 0,
      );
}

class ExerciseQuestion {
  final int id;
  final String question;
  final List<String> options;
  final int correctIndex;
  final String? explanation;

  const ExerciseQuestion({
    required this.id,
    required this.question,
    required this.options,
    required this.correctIndex,
    this.explanation,
  });

  factory ExerciseQuestion.fromJson(Map<String, dynamic> json) =>
      ExerciseQuestion(
        id: json['id'] ?? 0,
        question: json['question'] ?? json['text'] ?? '',
        options: (json['options'] as List?)?.cast<String>() ??
            (json['choices'] as List?)
                ?.map((c) => c is String ? c : c['text'].toString())
                .toList() ??
            [],
        correctIndex: json['correct_index'] ?? json['answer'] ?? 0,
        explanation: json['explanation'],
      );
}
