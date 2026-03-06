import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api/api_client.dart';
import 'data/exam_repository.dart';
import 'domain/models.dart';

final examRepositoryProvider = Provider<ExamRepository>((ref) {
  return ExamRepository(api: ref.watch(apiClientProvider));
});

final examHubProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  return ref.watch(examRepositoryProvider).getHub();
});

final examToeicListProvider = FutureProvider<List<ExamTemplate>>((ref) async {
  return ref.watch(examRepositoryProvider).getToeicList();
});

final examEnglishListProvider =
    FutureProvider<List<Map<String, dynamic>>>((ref) async {
  return ref.watch(examRepositoryProvider).getEnglishList();
});

final quizHistoryProvider = FutureProvider<List<QuizResult>>((ref) async {
  return ref.watch(examRepositoryProvider).getQuizHistory();
});
