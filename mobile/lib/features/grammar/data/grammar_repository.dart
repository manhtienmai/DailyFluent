import '../../../core/api/api_client.dart';
import '../../../core/api/api_endpoints.dart';
import '../domain/models.dart';

class GrammarRepository {
  final ApiClient _api;
  GrammarRepository({required ApiClient api}) : _api = api;

  Future<List<GrammarPoint>> getGrammarList({String? level}) async {
    final res = await _api.get(ApiConstants.grammarList,
        queryParameters: level != null ? {'level': level} : null);
    return (res.data as List).map((e) => GrammarPoint.fromJson(e)).toList();
  }

  Future<List<GrammarBook>> getBooks({String? level}) async {
    final res = await _api.get(ApiConstants.grammarBooks,
        queryParameters: level != null ? {'level': level} : null);
    return (res.data as List).map((e) => GrammarBook.fromJson(e)).toList();
  }

  Future<Map<String, dynamic>> getBookDetail(String slug) async {
    final res = await _api.get(ApiConstants.grammarBookDetail(slug));
    return res.data;
  }

  Future<Map<String, dynamic>> getPointDetail(String slug) async {
    final res = await _api.get(ApiConstants.grammarPointDetail(slug));
    return res.data;
  }

  Future<List<ExerciseQuestion>> getExercise(String slug) async {
    final res = await _api.get(ApiConstants.grammarExercise(slug));
    final questions = res.data['questions'] as List? ?? res.data as List;
    return questions.map((e) => ExerciseQuestion.fromJson(e)).toList();
  }

  Future<Map<String, dynamic>> submitExercise(
      String slug, Map<String, String> answers) async {
    final res = await _api
        .post(ApiConstants.grammarExerciseSubmit(slug), data: answers);
    return res.data;
  }

  Future<List<Map<String, dynamic>>> getFlashcards({String? level}) async {
    final res = await _api.get(ApiConstants.grammarFlashcards,
        queryParameters: level != null ? {'level': level} : null);
    return (res.data['cards'] as List? ?? res.data as List)
        .cast<Map<String, dynamic>>();
  }

  Future<void> gradeFlashcard(int grammarPointId, String rating) async {
    await _api.post(ApiConstants.grammarFlashcardGrade,
        data: {'grammar_point_id': grammarPointId, 'rating': rating});
  }
}
