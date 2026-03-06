import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/colors.dart';
import '../../../shared/widgets/glass_card.dart';
import '../../auth/providers.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(currentUserProvider);
    final theme = Theme.of(context);

    return Scaffold(
      body: SafeArea(
        child: CustomScrollView(
          slivers: [
            // ── App Bar ────────────────────────────────────
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
                child: Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            _greeting(),
                            style: theme.textTheme.bodyMedium?.copyWith(
                              color: theme.textTheme.bodySmall?.color,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            user?.displayName ?? 'Bạn',
                            style: theme.textTheme.headlineMedium,
                          ),
                        ],
                      ),
                    ),
                    // Streak badge
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 12,
                        vertical: 8,
                      ),
                      decoration: BoxDecoration(
                        color: AppColors.streakFire.withOpacity(0.15),
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Row(
                        children: [
                          const Text('🔥', style: TextStyle(fontSize: 18)),
                          const SizedBox(width: 4),
                          Text(
                            '0',
                            style: theme.textTheme.titleMedium?.copyWith(
                              color: AppColors.streakFire,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 8),
                    // Notification bell
                    IconButton(
                      onPressed: () {},
                      icon: const Icon(Icons.notifications_outlined),
                    ),
                  ],
                ),
              ),
            ),

            // ── Daily Progress Card ────────────────────────
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(20, 24, 20, 0),
                child: GlassCard(
                  gradient: AppColors.primaryGradient,
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Mục tiêu hôm nay',
                        style: TextStyle(
                          color: Colors.white70,
                          fontSize: 13,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                      const SizedBox(height: 8),
                      const Text(
                        '0/10 phút',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 28,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      const SizedBox(height: 12),
                      ClipRRect(
                        borderRadius: BorderRadius.circular(6),
                        child: LinearProgressIndicator(
                          value: 0.0,
                          minHeight: 8,
                          backgroundColor: Colors.white.withOpacity(0.2),
                          valueColor: const AlwaysStoppedAnimation<Color>(
                            Colors.white,
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          _statItem('Thẻ mới', '0', Icons.add_circle_outline),
                          _statItem('Ôn tập', '0', Icons.replay_rounded),
                          _statItem('Streak', '0', Icons.local_fire_department),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
            ),

            // ── Quick Actions ──────────────────────────────
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(20, 24, 20, 0),
                child: Text(
                  'Bắt đầu nhanh',
                  style: theme.textTheme.titleLarge,
                ),
              ),
            ),
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(20, 12, 20, 0),
                child: Row(
                  children: [
                    Expanded(
                      child: _quickAction(
                        context,
                        icon: Icons.style_outlined,
                        label: 'Flashcard',
                        color: AppColors.primary,
                        onTap: () {},
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: _quickAction(
                        context,
                        icon: Icons.translate_rounded,
                        label: 'Kanji',
                        color: AppColors.accent,
                        onTap: () {},
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: _quickAction(
                        context,
                        icon: Icons.quiz_outlined,
                        label: 'Quiz',
                        color: AppColors.warning,
                        onTap: () {},
                      ),
                    ),
                  ],
                ),
              ),
            ),

            // ── Learning Modules Grid ──────────────────────
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(20, 28, 20, 0),
                child: Text(
                  'Công cụ học tập',
                  style: theme.textTheme.titleLarge,
                ),
              ),
            ),
            SliverPadding(
              padding: const EdgeInsets.fromLTRB(20, 12, 20, 24),
              sliver: SliverGrid(
                gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 2,
                  crossAxisSpacing: 12,
                  mainAxisSpacing: 12,
                  childAspectRatio: 1.5,
                ),
                delegate: SliverChildListDelegate([
                  _moduleCard(
                    context,
                    icon: '漢',
                    title: 'Kanji',
                    subtitle: 'JLPT N5 → N1',
                    color: AppColors.jlptN3,
                    onTap: () {},
                  ),
                  _moduleCard(
                    context,
                    icon: '📚',
                    title: 'Từ vựng',
                    subtitle: 'Flashcards & Games',
                    color: AppColors.primary,
                    onTap: () {},
                  ),
                  _moduleCard(
                    context,
                    icon: '📖',
                    title: 'Ngữ pháp',
                    subtitle: 'N5 → N1',
                    color: AppColors.accent,
                    onTap: () {},
                  ),
                  _moduleCard(
                    context,
                    icon: '🎬',
                    title: 'Video',
                    subtitle: 'Nghe & đọc phụ đề',
                    color: AppColors.error,
                    onTap: () {},
                  ),
                  _moduleCard(
                    context,
                    icon: '📝',
                    title: 'Luyện thi',
                    subtitle: 'TOEIC, JLPT',
                    color: AppColors.info,
                    onTap: () {},
                  ),
                  _moduleCard(
                    context,
                    icon: '🎯',
                    title: 'Placement',
                    subtitle: 'Kiểm tra trình độ',
                    color: AppColors.jlptN1,
                    onTap: () {},
                  ),
                ]),
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _greeting() {
    final hour = DateTime.now().hour;
    if (hour < 12) return 'Chào buổi sáng 👋';
    if (hour < 18) return 'Chào buổi chiều 👋';
    return 'Chào buổi tối 👋';
  }

  Widget _statItem(String label, String value, IconData icon) {
    return Row(
      children: [
        Icon(icon, size: 16, color: Colors.white70),
        const SizedBox(width: 4),
        Text(
          '$label: $value',
          style: const TextStyle(
            color: Colors.white,
            fontSize: 12,
            fontWeight: FontWeight.w500,
          ),
        ),
      ],
    );
  }

  Widget _quickAction(
    BuildContext context, {
    required IconData icon,
    required String label,
    required Color color,
    required VoidCallback onTap,
  }) {
    return GlassCard(
      onTap: onTap,
      padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 12),
      child: Column(
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: color.withOpacity(0.15),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(icon, color: color, size: 24),
          ),
          const SizedBox(height: 8),
          Text(
            label,
            style: Theme.of(context).textTheme.labelMedium?.copyWith(
                  fontWeight: FontWeight.w600,
                  color: Theme.of(context).textTheme.bodyLarge?.color,
                ),
          ),
        ],
      ),
    );
  }

  Widget _moduleCard(
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
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(icon, style: const TextStyle(fontSize: 28)),
          Column(
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
        ],
      ),
    );
  }
}
