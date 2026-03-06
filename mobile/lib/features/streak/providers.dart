import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api/api_client.dart';
import 'data/streak_repository.dart';

final streakRepositoryProvider = Provider<StreakRepository>((ref) {
  return StreakRepository(api: ref.watch(apiClientProvider));
});

final streakStatusProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  return ref.watch(streakRepositoryProvider).getStatus();
});

final streakHeatmapProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  return ref.watch(streakRepositoryProvider).getHeatmap();
});

final streakLeaderboardProvider =
    FutureProvider<List<Map<String, dynamic>>>((ref) async {
  return ref.watch(streakRepositoryProvider).getLeaderboard();
});
