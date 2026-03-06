import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api/api_client.dart';
import 'data/vocab_repository.dart';
import 'domain/models.dart';

final vocabRepositoryProvider = Provider<VocabRepository>((ref) {
  return VocabRepository(api: ref.watch(apiClientProvider));
});

final vocabCoursesProvider = FutureProvider<List<VocabCourse>>((ref) async {
  return ref.watch(vocabRepositoryProvider).getCourses();
});

final vocabUserSetsProvider = FutureProvider<List<VocabSet>>((ref) async {
  return ref.watch(vocabRepositoryProvider).getUserSets();
});

final vocabFlashcardsProvider =
    FutureProvider<List<FlashcardItem>>((ref) async {
  return ref.watch(vocabRepositoryProvider).getFlashcards();
});

final vocabGamesProvider = FutureProvider<List<VocabGame>>((ref) async {
  return ref.watch(vocabRepositoryProvider).getGames();
});
