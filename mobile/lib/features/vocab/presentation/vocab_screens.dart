import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/colors.dart';
import '../../../shared/widgets/glass_card.dart';
import '../../../shared/widgets/shimmer_loading.dart';
import '../providers.dart';
import '../domain/models.dart';

class VocabCoursesScreen extends ConsumerWidget {
  const VocabCoursesScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final coursesAsync = ref.watch(vocabCoursesProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Khóa từ vựng')),
      body: coursesAsync.when(
        loading: () => const Padding(
          padding: EdgeInsets.all(20),
          child: ShimmerList(itemCount: 5, itemHeight: 90),
        ),
        error: (e, _) => Center(child: Text('Lỗi: $e')),
        data: (courses) => ListView.builder(
          padding: const EdgeInsets.all(20),
          itemCount: courses.length,
          itemBuilder: (context, i) {
            final c = courses[i];
            return Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: GlassCard(
                onTap: () {},
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    Container(
                      width: 52,
                      height: 52,
                      decoration: BoxDecoration(
                        color: AppColors.primary.withOpacity(0.12),
                        borderRadius: BorderRadius.circular(14),
                      ),
                      alignment: Alignment.center,
                      child: Text(
                        c.language == 'jp' ? '🇯🇵' : '🇬🇧',
                        style: const TextStyle(fontSize: 26),
                      ),
                    ),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(c.title,
                              style: Theme.of(context)
                                  .textTheme
                                  .titleMedium
                                  ?.copyWith(fontWeight: FontWeight.w600)),
                          const SizedBox(height: 2),
                          Text('${c.totalSets} bộ · ${c.totalWords} từ',
                              style: Theme.of(context).textTheme.bodySmall),
                        ],
                      ),
                    ),
                    Icon(Icons.chevron_right_rounded,
                        color: Theme.of(context).textTheme.bodySmall?.color),
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

class FlashcardReviewScreen extends ConsumerStatefulWidget {
  const FlashcardReviewScreen({super.key});

  @override
  ConsumerState<FlashcardReviewScreen> createState() =>
      _FlashcardReviewScreenState();
}

class _FlashcardReviewScreenState extends ConsumerState<FlashcardReviewScreen> {
  int _currentIndex = 0;
  bool _showAnswer = false;

  @override
  Widget build(BuildContext context) {
    final cardsAsync = ref.watch(vocabFlashcardsProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Ôn tập Flashcards')),
      body: cardsAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Lỗi: $e')),
        data: (cards) {
          if (cards.isEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Text('🎉', style: TextStyle(fontSize: 64)),
                  const SizedBox(height: 16),
                  Text('Không có thẻ nào cần ôn tập!',
                      style: theme.textTheme.titleMedium),
                  const SizedBox(height: 8),
                  Text('Quay lại sau nhé',
                      style: theme.textTheme.bodySmall),
                ],
              ),
            );
          }

          if (_currentIndex >= cards.length) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Text('✅', style: TextStyle(fontSize: 64)),
                  const SizedBox(height: 16),
                  Text('Hoàn thành!', style: theme.textTheme.headlineMedium),
                  Text('Đã ôn ${cards.length} thẻ',
                      style: theme.textTheme.bodyMedium),
                ],
              ),
            );
          }

          final card = cards[_currentIndex];

          return Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              children: [
                // Progress
                LinearProgressIndicator(
                  value: (_currentIndex + 1) / cards.length,
                ),
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  child: Text(
                    '${_currentIndex + 1} / ${cards.length}',
                    style: theme.textTheme.bodySmall,
                  ),
                ),
                const Spacer(),

                // Card
                GestureDetector(
                  onTap: () => setState(() => _showAnswer = !_showAnswer),
                  child: GlassCard(
                    padding: const EdgeInsets.all(32),
                    child: SizedBox(
                      width: double.infinity,
                      height: 200,
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Text(
                            card.word,
                            style: const TextStyle(
                                fontSize: 32, fontWeight: FontWeight.w600),
                          ),
                          if (card.reading.isNotEmpty)
                            Padding(
                              padding: const EdgeInsets.only(top: 8),
                              child: Text(card.reading,
                                  style: theme.textTheme.bodyMedium),
                            ),
                          if (_showAnswer) ...[
                            const Divider(height: 24),
                            Text(card.meaning,
                                style: theme.textTheme.titleMedium?.copyWith(
                                    color: AppColors.accent),
                                textAlign: TextAlign.center),
                          ] else
                            Padding(
                              padding: const EdgeInsets.only(top: 16),
                              child: Text('Nhấn để xem đáp án',
                                  style: theme.textTheme.bodySmall),
                            ),
                        ],
                      ),
                    ),
                  ),
                ),

                const Spacer(),

                // Rating buttons (FSRS: again, hard, good, easy)
                if (_showAnswer)
                  Row(
                    children: [
                      _gradeButton('Quên', AppColors.error, 'again', card.id),
                      const SizedBox(width: 8),
                      _gradeButton('Khó', AppColors.warning, 'hard', card.id),
                      const SizedBox(width: 8),
                      _gradeButton('Tốt', AppColors.accent, 'good', card.id),
                      const SizedBox(width: 8),
                      _gradeButton('Dễ', AppColors.info, 'easy', card.id),
                    ],
                  ),
                const SizedBox(height: 20),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _gradeButton(String label, Color color, String rating, int cardId) {
    return Expanded(
      child: ElevatedButton(
        onPressed: () {
          ref.read(vocabRepositoryProvider).gradeFlashcard(cardId, rating);
          setState(() {
            _currentIndex++;
            _showAnswer = false;
          });
        },
        style: ElevatedButton.styleFrom(
          backgroundColor: color,
          padding: const EdgeInsets.symmetric(vertical: 14),
        ),
        child: Text(label, style: const TextStyle(color: Colors.white)),
      ),
    );
  }
}
