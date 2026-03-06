import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/theme/colors.dart';
import '../../../shared/widgets/glass_card.dart';

class ProgressScreen extends StatelessWidget {
  const ProgressScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Tiến độ'),
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          // ── Streak Overview ──────────────────────────────
          GlassCard(
            gradient: AppColors.warmGradient,
            padding: const EdgeInsets.all(20),
            child: Row(
              children: [
                const Text('🔥', style: TextStyle(fontSize: 48)),
                const SizedBox(width: 16),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      '0 ngày',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 28,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    Text(
                      'Streak hiện tại',
                      style: TextStyle(
                        color: Colors.white.withOpacity(0.8),
                        fontSize: 14,
                      ),
                    ),
                  ],
                ),
                const Spacer(),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    const Text(
                      '0',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 22,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    Text(
                      'Kỷ lục',
                      style: TextStyle(
                        color: Colors.white.withOpacity(0.8),
                        fontSize: 13,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),

          // ── Stats Row ────────────────────────────────────
          Row(
            children: [
              Expanded(
                child: _statCard(
                  context,
                  icon: Icons.timer_outlined,
                  value: '0',
                  label: 'Phút hôm nay',
                  color: AppColors.primary,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _statCard(
                  context,
                  icon: Icons.style_outlined,
                  value: '0',
                  label: 'Thẻ hôm nay',
                  color: AppColors.accent,
                ),
              ),
            ],
          ),
          const SizedBox(height: 24),

          // ── Heatmap ──────────────────────────────────────
          GlassCard(
            onTap: () => context.go('/progress/heatmap'),
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                const Icon(Icons.calendar_month_outlined),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Hoạt động 60 ngày',
                          style: theme.textTheme.titleSmall?.copyWith(
                              fontWeight: FontWeight.w600,
                              color: theme.textTheme.bodyLarge?.color)),
                      Text('Xem chi tiết heatmap',
                          style: theme.textTheme.bodySmall),
                    ],
                  ),
                ),
                Icon(Icons.chevron_right_rounded,
                    color: theme.textTheme.bodySmall?.color),
              ],
            ),
          ),
          const SizedBox(height: 12),

          // ── Leaderboard ──────────────────────────────────
          GlassCard(
            onTap: () => context.go('/progress/leaderboard'),
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                const Icon(Icons.leaderboard_outlined),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Bảng xếp hạng',
                          style: theme.textTheme.titleSmall?.copyWith(
                              fontWeight: FontWeight.w600,
                              color: theme.textTheme.bodyLarge?.color)),
                      Text('So sánh với bạn bè',
                          style: theme.textTheme.bodySmall),
                    ],
                  ),
                ),
                Icon(Icons.chevron_right_rounded,
                    color: theme.textTheme.bodySmall?.color),
              ],
            ),
          ),
          const SizedBox(height: 12),

          // ── Quiz History ─────────────────────────────────
          GlassCard(
            onTap: () {},
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                const Icon(Icons.history_outlined),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Lịch sử làm bài',
                          style: theme.textTheme.titleSmall?.copyWith(
                              fontWeight: FontWeight.w600,
                              color: theme.textTheme.bodyLarge?.color)),
                      Text('Xem kết quả các bài thi',
                          style: theme.textTheme.bodySmall),
                    ],
                  ),
                ),
                Icon(Icons.chevron_right_rounded,
                    color: theme.textTheme.bodySmall?.color),
              ],
            ),
          ),
          const SizedBox(height: 24),
        ],
      ),
    );
  }

  Widget _statCard(
    BuildContext context, {
    required IconData icon,
    required String value,
    required String label,
    required Color color,
  }) {
    return GlassCard(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          Icon(icon, color: color, size: 28),
          const SizedBox(height: 8),
          Text(
            value,
            style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                  fontWeight: FontWeight.w700,
                ),
          ),
          const SizedBox(height: 4),
          Text(label, style: Theme.of(context).textTheme.bodySmall),
        ],
      ),
    );
  }
}
