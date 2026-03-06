import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/theme/colors.dart';
import '../../../shared/widgets/glass_card.dart';

class ExamHubScreen extends StatelessWidget {
  const ExamHubScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Luyện thi'),
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          _examCategory(
            context,
            icon: '🏆',
            title: 'TOEIC',
            subtitle: 'Đề thi TOEIC đầy đủ',
            color: AppColors.primary,
            onTap: () => context.go('/exam/toeic'),
          ),
          const SizedBox(height: 12),
          _examCategory(
            context,
            icon: '🎧',
            title: 'Choukai (聴解)',
            subtitle: 'Luyện nghe JLPT',
            color: AppColors.info,
            onTap: () {},
          ),
          const SizedBox(height: 12),
          _examCategory(
            context,
            icon: '📖',
            title: 'Dokkai (読解)',
            subtitle: 'Luyện đọc hiểu JLPT',
            color: AppColors.accent,
            onTap: () {},
          ),
          const SizedBox(height: 12),
          _examCategory(
            context,
            icon: '💡',
            title: 'Usage (用法)',
            subtitle: 'Cách dùng từ vựng',
            color: AppColors.warning,
            onTap: () {},
          ),
          const SizedBox(height: 12),
          _examCategory(
            context,
            icon: '📝',
            title: 'Bunpou (文法)',
            subtitle: 'Trắc nghiệm ngữ pháp JLPT',
            color: AppColors.jlptN2,
            onTap: () {},
          ),
          const SizedBox(height: 12),
          _examCategory(
            context,
            icon: '🇬🇧',
            title: 'English Exams',
            subtitle: 'Grammar & Phrasal Verbs',
            color: AppColors.jlptN1,
            onTap: () {},
          ),
          const SizedBox(height: 24),
        ],
      ),
    );
  }

  Widget _examCategory(
    BuildContext context, {
    required String icon,
    required String title,
    required String subtitle,
    required Color color,
    required VoidCallback onTap,
  }) {
    return GlassCard(
      onTap: onTap,
      padding: const EdgeInsets.all(20),
      child: Row(
        children: [
          Container(
            width: 56,
            height: 56,
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [color, color.withOpacity(0.7)],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(16),
              boxShadow: [
                BoxShadow(
                  color: color.withOpacity(0.3),
                  blurRadius: 12,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            alignment: Alignment.center,
            child: Text(icon, style: const TextStyle(fontSize: 28)),
          ),
          const SizedBox(width: 16),
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
                const SizedBox(height: 4),
                Text(
                  subtitle,
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
          ),
          Icon(
            Icons.arrow_forward_ios_rounded,
            size: 16,
            color: Theme.of(context).textTheme.bodySmall?.color,
          ),
        ],
      ),
    );
  }
}
