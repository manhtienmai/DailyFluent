import '../../../core/api/api_client.dart';
import '../../../core/api/api_endpoints.dart';
import '../domain/models.dart';

class KanjiRepository {
  final ApiClient _api;
  KanjiRepository({required ApiClient api}) : _api = api;

  Future<List<JlptGroup>> getLevels() async {
    final res = await _api.get(ApiConstants.kanjiLevels);
    return (res.data as List).map((e) => JlptGroup.fromJson(e)).toList();
  }

  Future<KanjiDetail> getDetail(String char) async {
    final res = await _api.get(ApiConstants.kanjiDetail(char));
    return KanjiDetail.fromJson(res.data);
  }

  Future<Map<int, Map<String, dynamic>>> getMyProgress() async {
    final res = await _api.get(ApiConstants.kanjiMyProgress);
    final list = res.data as List;
    return {for (var p in list) p['kanji_id'] as int: p};
  }

  Future<void> updateProgress(int kanjiId, bool passed) async {
    await _api.post(ApiConstants.kanjiProgress, data: {
      'kanji_id': kanjiId,
      'passed': passed,
    });
  }

  Future<List<QuizQuestion>> getQuiz(int lessonId) async {
    final res = await _api.get(ApiConstants.kanjiQuiz(lessonId));
    final questions = res.data['questions'] as List? ?? [];
    return questions.map((e) => QuizQuestion.fromJson(e)).toList();
  }
}
