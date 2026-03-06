import '../../../core/api/api_client.dart';
import '../../../core/api/api_endpoints.dart';

class StreakRepository {
  final ApiClient _api;
  StreakRepository({required ApiClient api}) : _api = api;

  Future<Map<String, dynamic>> getStatus() async {
    final res = await _api.get(ApiConstants.streakStatus);
    return res.data;
  }

  Future<Map<String, dynamic>> logTime({int seconds = 0, int minutes = 0}) async {
    final res = await _api.post(ApiConstants.streakLogMinutes,
        data: {'seconds': seconds, 'minutes': minutes});
    return res.data;
  }

  Future<Map<String, dynamic>> getHeatmap() async {
    final res = await _api.get(ApiConstants.streakHeatmap);
    return res.data;
  }

  Future<List<Map<String, dynamic>>> getLeaderboard() async {
    final res = await _api.get(ApiConstants.streakLeaderboard);
    return (res.data as List).cast<Map<String, dynamic>>();
  }
}
