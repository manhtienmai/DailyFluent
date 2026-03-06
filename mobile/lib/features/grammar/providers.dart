import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api/api_client.dart';
import 'data/grammar_repository.dart';
import 'domain/models.dart';

final grammarRepositoryProvider = Provider<GrammarRepository>((ref) {
  return GrammarRepository(api: ref.watch(apiClientProvider));
});

final grammarListProvider =
    FutureProvider.family<List<GrammarPoint>, String?>((ref, level) async {
  return ref.watch(grammarRepositoryProvider).getGrammarList(level: level);
});

final grammarBooksProvider =
    FutureProvider.family<List<GrammarBook>, String?>((ref, level) async {
  return ref.watch(grammarRepositoryProvider).getBooks(level: level);
});
