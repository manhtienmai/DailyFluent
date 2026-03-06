import '../../../core/api/api_client.dart';
import '../../../core/api/api_endpoints.dart';

class PlacementRepository {
  final ApiClient _api;
  PlacementRepository({required ApiClient api}) : _api = api;

  Future<Map<String, dynamic>> checkStatus() async {
    final res = await _api.get(ApiConstants.placementHome);
    return res.data;
  }

  Future<Map<String, dynamic>> startTest() async {
    final res = await _api.post(ApiConstants.placementStart);
    return res.data;
  }

  Future<Map<String, dynamic>> getNextQuestion(int testId) async {
    final res = await _api.get(ApiConstants.placementNextQuestion(testId));
    return res.data;
  }

  Future<Map<String, dynamic>> submitAnswer(
      int testId, int questionId, String answer) async {
    final res = await _api.post(
      ApiConstants.placementSubmitAnswer(testId, questionId),
      data: {'answer': answer},
    );
    return res.data;
  }

  Future<Map<String, dynamic>> getResult(int testId) async {
    final res = await _api.get(ApiConstants.placementResult(testId));
    return res.data;
  }

  Future<Map<String, dynamic>> getDashboard() async {
    final res = await _api.get(ApiConstants.placementDashboard);
    return res.data;
  }

  Future<Map<String, dynamic>> getLearningPath() async {
    final res = await _api.get(ApiConstants.placementLearningPath);
    return res.data;
  }
}
