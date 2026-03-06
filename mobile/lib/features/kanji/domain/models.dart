/// Kanji domain models.

class KanjiSummary {
  final int id;
  final String char;
  final String keyword;
  final String sinoVi;
  final int order;

  const KanjiSummary({
    required this.id,
    required this.char,
    required this.keyword,
    required this.sinoVi,
    required this.order,
  });

  factory KanjiSummary.fromJson(Map<String, dynamic> json) => KanjiSummary(
        id: json['id'],
        char: json['char'],
        keyword: json['keyword'] ?? '',
        sinoVi: json['sino_vi'] ?? '',
        order: json['order'] ?? 0,
      );
}

class KanjiLesson {
  final int id;
  final String jlptLevel;
  final int lessonNumber;
  final String topic;
  final int order;
  final List<KanjiSummary> kanjis;

  const KanjiLesson({
    required this.id,
    required this.jlptLevel,
    required this.lessonNumber,
    required this.topic,
    required this.order,
    required this.kanjis,
  });

  factory KanjiLesson.fromJson(Map<String, dynamic> json) => KanjiLesson(
        id: json['id'],
        jlptLevel: json['jlpt_level'] ?? '',
        lessonNumber: json['lesson_number'] ?? 0,
        topic: json['topic'] ?? '',
        order: json['order'] ?? 0,
        kanjis: (json['kanjis'] as List? ?? [])
            .map((e) => KanjiSummary.fromJson(e))
            .toList(),
      );
}

class JlptGroup {
  final String level;
  final List<KanjiLesson> lessons;
  final int totalKanji;

  const JlptGroup({
    required this.level,
    required this.lessons,
    required this.totalKanji,
  });

  factory JlptGroup.fromJson(Map<String, dynamic> json) => JlptGroup(
        level: json['level'] ?? '',
        lessons: (json['lessons'] as List? ?? [])
            .map((e) => KanjiLesson.fromJson(e))
            .toList(),
        totalKanji: json['total_kanji'] ?? 0,
      );
}

class KanjiVocab {
  final int id;
  final String word;
  final String reading;
  final String meaning;
  final int priority;

  const KanjiVocab({
    required this.id,
    required this.word,
    required this.reading,
    required this.meaning,
    required this.priority,
  });

  factory KanjiVocab.fromJson(Map<String, dynamic> json) => KanjiVocab(
        id: json['id'],
        word: json['word'] ?? '',
        reading: json['reading'] ?? '',
        meaning: json['meaning'] ?? '',
        priority: json['priority'] ?? 0,
      );
}

class KanjiDetail {
  final int id;
  final String char;
  final String sinoVi;
  final String keyword;
  final String onyomi;
  final String kunyomi;
  final String meaningVi;
  final int? strokes;
  final String note;
  final String formation;
  final String jlptLevel;
  final List<KanjiVocab> vocab;
  final String lessonLabel;
  final int kanjiIndex;
  final int kanjiTotal;
  final KanjiProgress? progress;

  const KanjiDetail({
    required this.id,
    required this.char,
    required this.sinoVi,
    required this.keyword,
    required this.onyomi,
    required this.kunyomi,
    required this.meaningVi,
    this.strokes,
    required this.note,
    this.formation = '',
    required this.jlptLevel,
    required this.vocab,
    this.lessonLabel = '',
    this.kanjiIndex = 0,
    this.kanjiTotal = 0,
    this.progress,
  });

  factory KanjiDetail.fromJson(Map<String, dynamic> json) {
    final kanji = json['kanji'] ?? json;
    return KanjiDetail(
      id: kanji['id'],
      char: kanji['char'],
      sinoVi: kanji['sino_vi'] ?? '',
      keyword: kanji['keyword'] ?? '',
      onyomi: kanji['onyomi'] ?? '',
      kunyomi: kanji['kunyomi'] ?? '',
      meaningVi: kanji['meaning_vi'] ?? '',
      strokes: kanji['strokes'],
      note: kanji['note'] ?? '',
      formation: kanji['formation'] ?? '',
      jlptLevel: kanji['jlpt_level'] ?? '',
      vocab: (json['vocab'] as List? ?? [])
          .map((e) => KanjiVocab.fromJson(e))
          .toList(),
      lessonLabel: json['lesson_label'] ?? '',
      kanjiIndex: json['kanji_index'] ?? 0,
      kanjiTotal: json['kanji_total'] ?? 0,
      progress: json['progress'] != null
          ? KanjiProgress.fromJson(json['progress'])
          : null,
    );
  }
}

class KanjiProgress {
  final String status;
  final int correctStreak;
  final bool mastered;

  const KanjiProgress({
    required this.status,
    required this.correctStreak,
    required this.mastered,
  });

  factory KanjiProgress.fromJson(Map<String, dynamic> json) => KanjiProgress(
        status: json['status'] ?? 'new',
        correctStreak: json['correct_streak'] ?? 0,
        mastered: json['mastered'] ?? false,
      );
}

class QuizQuestion {
  final int kanjiId;
  final String char;
  final String sinoVi;
  final String questionType;
  final List<QuizOption> options;

  const QuizQuestion({
    required this.kanjiId,
    required this.char,
    required this.sinoVi,
    required this.questionType,
    required this.options,
  });

  factory QuizQuestion.fromJson(Map<String, dynamic> json) => QuizQuestion(
        kanjiId: json['kanji_id'],
        char: json['char'] ?? '',
        sinoVi: json['sino_vi'] ?? '',
        questionType: json['question_type'] ?? '',
        options: (json['options'] as List? ?? [])
            .map((e) => QuizOption.fromJson(e))
            .toList(),
      );
}

class QuizOption {
  final String text;
  final bool isCorrect;

  const QuizOption({required this.text, required this.isCorrect});

  factory QuizOption.fromJson(Map<String, dynamic> json) => QuizOption(
        text: json['text'] ?? '',
        isCorrect: json['is_correct'] ?? false,
      );
}
