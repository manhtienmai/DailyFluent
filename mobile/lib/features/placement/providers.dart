import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api/api_client.dart';
import 'data/placement_repository.dart';

final placementRepositoryProvider = Provider<PlacementRepository>((ref) {
  return PlacementRepository(api: ref.watch(apiClientProvider));
});

final placementStatusProvider =
    FutureProvider<Map<String, dynamic>>((ref) async {
  return ref.watch(placementRepositoryProvider).checkStatus();
});

final placementDashboardProvider =
    FutureProvider<Map<String, dynamic>>((ref) async {
  return ref.watch(placementRepositoryProvider).getDashboard();
});

final placementLearningPathProvider =
    FutureProvider<Map<String, dynamic>>((ref) async {
  return ref.watch(placementRepositoryProvider).getLearningPath();
});
