import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/theme/colors.dart';
import '../../../shared/widgets/glass_card.dart';

class LearnHubScreen extends StatelessWidget {
  const LearnHubScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Học tập'),
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          // ── Japanese Section ──────────────────────────────
          Text('Tiếng Nhật', style: theme.textTheme.titleLarge),
          const SizedBox(height: 12),
          _buildModuleItem(
            context,
            icon: '漢',
            title: 'Kanji',
            subtitle: 'Học Kanji theo JLPT N5 → N1',
            color: AppColors.jlptN3,
            onTap: () => context.go('/learn/kanji'),
          ),
          const SizedBox(height: 10),
          _buildModuleItem(
            context,
            icon: '📚',
            title: 'Từ vựng JP',
            subtitle: 'Khóa học, flashcards, games',
            color: AppColors.primary,
            onTap: () => context.go('/learn/vocab'),
          ),
          const SizedBox(height: 10),
          _buildModuleItem(
            context,
            icon: '📖',
            title: 'Ngữ pháp JP',
            subtitle: 'Bunpou N5 → N1, bài tập',
            color: AppColors.accent,
            onTap: () => context.go('/learn/grammar'),
          ),
          const SizedBox(height: 10),
          _buildModuleItem(
            context,
            icon: '🎬',
            title: 'Video',
            subtitle: 'Nghe hiểu với phụ đề',
            color: AppColors.error,
            onTap: () => context.go('/learn/videos'),
          ),
          const SizedBox(height: 10),
          _buildModuleItem(
            context,
            icon: '📕',
            title: 'Ebooks',
            subtitle: 'Đọc sách tiếng Nhật',
            color: AppColors.jlptN1,
            onTap: () => context.go('/learn/ebooks'),
          ),
          const SizedBox(height: 10),
          _buildModuleItem(
            context,
            icon: '🃏',
            title: 'Ôn tập Flashcards',
            subtitle: 'Spaced Repetition (FSRS)',
            color: AppColors.info,
            onTap: () => context.go('/learn/flashcards'),
          ),

          const SizedBox(height: 28),

          // ── English Section ──────────────────────────────
          Text('Tiếng Anh', style: theme.textTheme.titleLarge),
          const SizedBox(height: 12),
          _buildModuleItem(
            context,
            icon: '🎯',
            title: 'Placement Test',
            subtitle: 'Đánh giá trình độ TOEIC',
            color: AppColors.jlptN2,
            onTap: () => context.go('/learn/placement'),
          ),
          const SizedBox(height: 24),
        ],
      ),
    );
  }

  Widget _buildModuleItem(
    BuildContext context, {
    required String icon,
    required String title,
    required String subtitle,
    required Color color,
    required VoidCallback onTap,
  }) {
    return GlassCard(
      onTap: onTap,
      padding: const EdgeInsets.all(16),
      child: Row(
        children: [
          Container(
            width: 52,
            height: 52,
            decoration: BoxDecoration(
              color: color.withOpacity(0.12),
              borderRadius: BorderRadius.circular(14),
            ),
            alignment: Alignment.center,
            child: Text(icon, style: const TextStyle(fontSize: 26)),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w600,
                      ),
                ),
                const SizedBox(height: 2),
                Text(
                  subtitle,
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
          ),
          Icon(
            Icons.chevron_right_rounded,
            color: Theme.of(context).textTheme.bodySmall?.color,
          ),
        ],
      ),
    );
  }
}
