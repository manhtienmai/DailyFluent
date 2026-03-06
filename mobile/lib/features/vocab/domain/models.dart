/// Vocabulary domain models.

class VocabSet {
  final int id;
  final String title;
  final String description;
  final String language;
  final int wordCount;

  const VocabSet({
    required this.id,
    required this.title,
    this.description = '',
    this.language = 'en',
    this.wordCount = 0,
  });

  factory VocabSet.fromJson(Map<String, dynamic> json) => VocabSet(
        id: json['id'],
        title: json['title'] ?? '',
        description: json['description'] ?? '',
        language: json['language'] ?? 'en',
        wordCount: json['word_count'] ?? json['total_words'] ?? 0,
      );
}

class VocabCourse {
  final int id;
  final String title;
  final String slug;
  final String description;
  final String language;
  final int totalSets;
  final int totalWords;
  final String? coverImage;

  const VocabCourse({
    required this.id,
    required this.title,
    required this.slug,
    this.description = '',
    this.language = 'en',
    this.totalSets = 0,
    this.totalWords = 0,
    this.coverImage,
  });

  factory VocabCourse.fromJson(Map<String, dynamic> json) => VocabCourse(
        id: json['id'],
        title: json['title'] ?? '',
        slug: json['slug'] ?? '',
        description: json['description'] ?? '',
        language: json['language'] ?? 'en',
        totalSets: json['total_sets'] ?? 0,
        totalWords: json['total_words'] ?? 0,
        coverImage: json['cover_image'],
      );
}

class VocabWord {
  final int id;
  final String word;
  final String reading;
  final String meaning;
  final String? example;
  final String? audio;

  const VocabWord({
    required this.id,
    required this.word,
    this.reading = '',
    required this.meaning,
    this.example,
    this.audio,
  });

  factory VocabWord.fromJson(Map<String, dynamic> json) => VocabWord(
        id: json['id'] ?? 0,
        word: json['word'] ?? json['term'] ?? '',
        reading: json['reading'] ?? json['pronunciation'] ?? '',
        meaning: json['meaning'] ?? json['definition'] ?? '',
        example: json['example'],
        audio: json['audio'],
      );
}

class FlashcardItem {
  final int id;
  final String word;
  final String reading;
  final String meaning;
  final String? example;
  final String state;
  final double? difficulty;

  const FlashcardItem({
    required this.id,
    required this.word,
    this.reading = '',
    required this.meaning,
    this.example,
    this.state = 'new',
    this.difficulty,
  });

  factory FlashcardItem.fromJson(Map<String, dynamic> json) => FlashcardItem(
        id: json['id'] ?? 0,
        word: json['word'] ?? json['front'] ?? '',
        reading: json['reading'] ?? '',
        meaning: json['meaning'] ?? json['back'] ?? '',
        example: json['example'],
        state: json['state'] ?? 'new',
        difficulty: (json['difficulty'] as num?)?.toDouble(),
      );
}

class VocabGame {
  final String slug;
  final String title;
  final String description;
  final String icon;

  const VocabGame({
    required this.slug,
    required this.title,
    this.description = '',
    this.icon = '🎮',
  });

  factory VocabGame.fromJson(Map<String, dynamic> json) => VocabGame(
        slug: json['slug'] ?? '',
        title: json['title'] ?? '',
        description: json['description'] ?? '',
        icon: json['icon'] ?? '🎮',
      );
}
