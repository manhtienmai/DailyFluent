import '../../../core/api/api_client.dart';
import '../../../core/api/api_endpoints.dart';

class VideoRepository {
  final ApiClient _api;
  VideoRepository({required ApiClient api}) : _api = api;

  Future<List<Map<String, dynamic>>> getVideos({String? category}) async {
    final res = await _api.get(ApiConstants.videos,
        queryParameters: category != null ? {'category': category} : null);
    return (res.data as List).cast<Map<String, dynamic>>();
  }

  Future<List<Map<String, dynamic>>> getCategories() async {
    final res = await _api.get(ApiConstants.videoCategories);
    return (res.data as List).cast<Map<String, dynamic>>();
  }

  Future<Map<String, dynamic>> getVideoDetail(String slug) async {
    final res = await _api.get(ApiConstants.videoDetail(slug));
    return res.data;
  }
}

class EbookRepository {
  final ApiClient _api;
  EbookRepository({required ApiClient api}) : _api = api;

  Future<List<Map<String, dynamic>>> getEbooks() async {
    final res = await _api.get(ApiConstants.ebooks);
    return (res.data as List).cast<Map<String, dynamic>>();
  }

  Future<Map<String, dynamic>> getEbookDetail(String slug) async {
    final res = await _api.get(ApiConstants.ebookDetail(slug));
    return res.data;
  }
}
