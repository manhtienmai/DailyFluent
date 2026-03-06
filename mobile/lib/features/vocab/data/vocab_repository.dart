import '../../../core/api/api_client.dart';
import '../../../core/api/api_endpoints.dart';
import '../domain/models.dart';

class VocabRepository {
  final ApiClient _api;
  VocabRepository({required ApiClient api}) : _api = api;

  Future<List<VocabCourse>> getCourses({String? language}) async {
    final res = await _api.get(ApiConstants.vocabCourses,
        queryParameters: language != null ? {'language': language} : null);
    return (res.data as List).map((e) => VocabCourse.fromJson(e)).toList();
  }

  Future<Map<String, dynamic>> getCourseDetail(String slug) async {
    final res = await _api.get(ApiConstants.vocabCourseDetail(slug));
    return res.data;
  }

  Future<List<VocabWord>> getLearnSet(String slug, int setNum) async {
    final res = await _api.get(ApiConstants.vocabLearnSet(slug, setNum));
    return (res.data['words'] as List? ?? res.data as List)
        .map((e) => VocabWord.fromJson(e))
        .toList();
  }

  Future<List<VocabSet>> getUserSets({String? language}) async {
    final res = await _api.get(ApiConstants.vocabSets,
        queryParameters: language != null ? {'language': language} : null);
    return (res.data as List).map((e) => VocabSet.fromJson(e)).toList();
  }

  Future<List<FlashcardItem>> getFlashcards({String language = 'en'}) async {
    final res = await _api.get(ApiConstants.vocabFlashcards,
        queryParameters: {'language': language});
    return (res.data['cards'] as List? ?? res.data as List)
        .map((e) => FlashcardItem.fromJson(e))
        .toList();
  }

  Future<void> gradeFlashcard(int cardId, String rating) async {
    await _api.post(ApiConstants.vocabFlashcardGrade,
        data: {'card_id': cardId, 'rating': rating});
  }

  Future<List<VocabGame>> getGames() async {
    final res = await _api.get(ApiConstants.vocabGames);
    return (res.data as List).map((e) => VocabGame.fromJson(e)).toList();
  }

  Future<Map<String, dynamic>> getProgress({String language = 'en'}) async {
    final res = await _api.get(ApiConstants.vocabProgress,
        queryParameters: {'language': language});
    return res.data;
  }

  Future<int> getReviewDueCount({String language = 'en'}) async {
    final res = await _api.get(ApiConstants.vocabReviewDue,
        queryParameters: {'language': language});
    return res.data['count'] ?? 0;
  }
}
