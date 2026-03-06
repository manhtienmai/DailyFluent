import '../../../core/api/api_client.dart';
import '../../../core/api/api_endpoints.dart';
import '../domain/models.dart';

class ExamRepository {
  final ApiClient _api;
  ExamRepository({required ApiClient api}) : _api = api;

  Future<Map<String, dynamic>> getHub() async {
    final res = await _api.get(ApiConstants.examHub);
    return res.data;
  }

  Future<List<ExamTemplate>> getToeicList() async {
    final res = await _api.get(ApiConstants.examToeic);
    return (res.data as List).map((e) => ExamTemplate.fromJson(e)).toList();
  }

  Future<List<ExamTemplate>> getChoukaiList() async {
    final res = await _api.get(ApiConstants.examChoukai);
    return (res.data as List).map((e) => ExamTemplate.fromJson(e)).toList();
  }

  Future<List<ExamTemplate>> getDokkaiList() async {
    final res = await _api.get(ApiConstants.examDokkai);
    return (res.data as List).map((e) => ExamTemplate.fromJson(e)).toList();
  }

  Future<Map<String, dynamic>> getUsageList({String level = ''}) async {
    final res = await _api.get(ApiConstants.examUsage,
        queryParameters: level.isNotEmpty ? {'level': level} : null);
    return res.data;
  }

  Future<Map<String, dynamic>> getBunpouList({String level = ''}) async {
    final res = await _api.get(ApiConstants.examBunpou,
        queryParameters: level.isNotEmpty ? {'level': level} : null);
    return res.data;
  }

  Future<List<Map<String, dynamic>>> getEnglishList() async {
    final res = await _api.get(ApiConstants.examEnglish);
    return (res.data as List).cast<Map<String, dynamic>>();
  }

  Future<Map<String, dynamic>> getExamDetail(String slug) async {
    final res = await _api.get(ApiConstants.examDetail(slug));
    return res.data;
  }

  Future<QuizResult> submitQuizResult({
    required String quizType,
    required String quizId,
    required int totalQuestions,
    required int correctCount,
    required double score,
    required List<Map<String, dynamic>> answersDetail,
  }) async {
    final res = await _api.post(ApiConstants.quizResults, data: {
      'quiz_type': quizType,
      'quiz_id': quizId,
      'total_questions': totalQuestions,
      'correct_count': correctCount,
      'score': score,
      'answers_detail': answersDetail,
    });
    return QuizResult.fromJson(res.data);
  }

  Future<List<QuizResult>> getQuizHistory({
    String? quizType,
    String? quizId,
  }) async {
    final params = <String, dynamic>{};
    if (quizType != null) params['quiz_type'] = quizType;
    if (quizId != null) params['quiz_id'] = quizId;
    final res =
        await _api.get(ApiConstants.quizResults, queryParameters: params);
    return (res.data as List).map((e) => QuizResult.fromJson(e)).toList();
  }
}
