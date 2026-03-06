import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api/api_client.dart';
import 'data/video_repository.dart';

final videoRepositoryProvider = Provider<VideoRepository>((ref) {
  return VideoRepository(api: ref.watch(apiClientProvider));
});

final videoListProvider =
    FutureProvider<List<Map<String, dynamic>>>((ref) async {
  return ref.watch(videoRepositoryProvider).getVideos();
});

final videoCategoriesProvider =
    FutureProvider<List<Map<String, dynamic>>>((ref) async {
  return ref.watch(videoRepositoryProvider).getCategories();
});

final ebookRepositoryProvider = Provider<EbookRepository>((ref) {
  return EbookRepository(api: ref.watch(apiClientProvider));
});

final ebookListProvider =
    FutureProvider<List<Map<String, dynamic>>>((ref) async {
  return ref.watch(ebookRepositoryProvider).getEbooks();
});
