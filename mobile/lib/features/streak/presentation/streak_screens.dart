import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/colors.dart';
import '../../../shared/widgets/glass_card.dart';
import '../providers.dart';

class HeatmapScreen extends ConsumerWidget {
  const HeatmapScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final heatmapAsync = ref.watch(streakHeatmapProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Hoạt động')),
      body: heatmapAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Lỗi: $e')),
        data: (data) {
          final days = (data['days'] as List?) ?? [];
          return SingleChildScrollView(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('60 ngày gần nhất', style: theme.textTheme.titleLarge),
                const SizedBox(height: 12),
                Wrap(
                  spacing: 3,
                  runSpacing: 3,
                  children: days.map((d) {
                    final minutes = d['minutes'] ?? 0;
                    Color color;
                    if (minutes == 0) {
                      color = theme.dividerTheme.color ?? Colors.grey.shade200;
                    } else if (minutes < 5) {
                      color = AppColors.accent.withOpacity(0.3);
                    } else if (minutes < 15) {
                      color = AppColors.accent.withOpacity(0.6);
                    } else {
                      color = AppColors.accent;
                    }
                    return Container(
                      width: 16,
                      height: 16,
                      decoration: BoxDecoration(
                        color: color,
                        borderRadius: BorderRadius.circular(3),
                      ),
                    );
                  }).toList(),
                ),
                const SizedBox(height: 24),

                // Legend
                Row(
                  children: [
                    Text('Ít', style: theme.textTheme.bodySmall),
                    const SizedBox(width: 8),
                    ...[0.2, 0.4, 0.7, 1.0].map((o) => Container(
                          width: 14,
                          height: 14,
                          margin: const EdgeInsets.only(right: 3),
                          decoration: BoxDecoration(
                            color: AppColors.accent.withOpacity(o),
                            borderRadius: BorderRadius.circular(3),
                          ),
                        )),
                    const SizedBox(width: 4),
                    Text('Nhiều', style: theme.textTheme.bodySmall),
                  ],
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}

class LeaderboardScreen extends ConsumerWidget {
  const LeaderboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final leaderboardAsync = ref.watch(streakLeaderboardProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Bảng xếp hạng')),
      body: leaderboardAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Lỗi: $e')),
        data: (entries) => ListView.builder(
          padding: const EdgeInsets.all(20),
          itemCount: entries.length,
          itemBuilder: (context, i) {
            final e = entries[i];
            final rank = e['rank'] ?? i + 1;
            String medal = '';
            if (rank == 1) medal = '🥇';
            if (rank == 2) medal = '🥈';
            if (rank == 3) medal = '🥉';

            return Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: GlassCard(
                padding: const EdgeInsets.symmetric(
                    horizontal: 16, vertical: 12),
                child: Row(
                  children: [
                    SizedBox(
                      width: 32,
                      child: Text(
                        medal.isNotEmpty ? medal : '$rank',
                        style: theme.textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.w700),
                        textAlign: TextAlign.center,
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(e['username'] ?? '',
                          style: theme.textTheme.bodyLarge),
                    ),
                    Row(
                      children: [
                        const Text('🔥', style: TextStyle(fontSize: 16)),
                        const SizedBox(width: 4),
                        Text('${e['current_streak'] ?? 0}',
                            style: theme.textTheme.titleMedium?.copyWith(
                                color: AppColors.streakFire,
                                fontWeight: FontWeight.w700)),
                      ],
                    ),
                  ],
                ),
              ),
            );
          },
        ),
      ),
    );
  }
}
