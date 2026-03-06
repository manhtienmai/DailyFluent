import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_client.dart';
import 'data/kanji_repository.dart';
import 'domain/models.dart';

final kanjiRepositoryProvider = Provider<KanjiRepository>((ref) {
  return KanjiRepository(api: ref.watch(apiClientProvider));
});

final kanjiLevelsProvider = FutureProvider<List<JlptGroup>>((ref) async {
  return ref.watch(kanjiRepositoryProvider).getLevels();
});

final kanjiDetailProvider =
    FutureProvider.family<KanjiDetail, String>((ref, char) async {
  return ref.watch(kanjiRepositoryProvider).getDetail(char);
});

final kanjiQuizProvider =
    FutureProvider.family<List<QuizQuestion>, int>((ref, lessonId) async {
  return ref.watch(kanjiRepositoryProvider).getQuiz(lessonId);
});
