import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/colors.dart';
import '../../../shared/widgets/glass_card.dart';
import '../../../shared/widgets/shimmer_loading.dart';
import '../providers.dart';
import '../domain/models.dart';

class GrammarListScreen extends ConsumerWidget {
  const GrammarListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final pointsAsync = ref.watch(grammarListProvider(null));

    return Scaffold(
      appBar: AppBar(title: const Text('Ngữ pháp')),
      body: pointsAsync.when(
        loading: () => const Padding(
          padding: EdgeInsets.all(20),
          child: ShimmerList(itemCount: 8, itemHeight: 72),
        ),
        error: (e, _) => Center(child: Text('Lỗi: $e')),
        data: (points) => ListView.builder(
          padding: const EdgeInsets.all(20),
          itemCount: points.length,
          itemBuilder: (context, i) {
            final p = points[i];
            final color = AppColors.jlptColor(p.level);
            return Padding(
              padding: const EdgeInsets.only(bottom: 10),
              child: GlassCard(
                onTap: () => Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => GrammarDetailScreen(slug: p.slug),
                  ),
                ),
                padding: const EdgeInsets.all(14),
                child: Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: color.withOpacity(0.15),
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(p.level,
                          style: TextStyle(
                              color: color,
                              fontSize: 11,
                              fontWeight: FontWeight.w600)),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(p.title,
                              style: Theme.of(context)
                                  .textTheme
                                  .titleSmall
                                  ?.copyWith(
                                    fontWeight: FontWeight.w600,
                                    color: Theme.of(context)
                                        .textTheme
                                        .bodyLarge
                                        ?.color,
                                  )),
                          if (p.meaning.isNotEmpty)
                            Text(p.meaning,
                                style:
                                    Theme.of(context).textTheme.bodySmall,
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis),
                        ],
                      ),
                    ),
                    Icon(Icons.chevron_right_rounded,
                        size: 20,
                        color:
                            Theme.of(context).textTheme.bodySmall?.color),
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

class GrammarDetailScreen extends ConsumerWidget {
  final String slug;
  const GrammarDetailScreen({super.key, required this.slug});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Chi tiết ngữ pháp')),
      body: FutureBuilder<Map<String, dynamic>>(
        future: ref.read(grammarRepositoryProvider).getPointDetail(slug),
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(child: Text('Lỗi: ${snapshot.error}'));
          }
          final data = snapshot.data!;
          final point = GrammarPoint.fromJson(data);

          return SingleChildScrollView(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Title + level
                GlassCard(
                  gradient: AppColors.primaryGradient,
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(point.title,
                          style: const TextStyle(
                              color: Colors.white,
                              fontSize: 22,
                              fontWeight: FontWeight.w700)),
                      if (point.meaning.isNotEmpty) ...[
                        const SizedBox(height: 8),
                        Text(point.meaning,
                            style: TextStyle(
                                color: Colors.white.withOpacity(0.85),
                                fontSize: 15)),
                      ],
                    ],
                  ),
                ),
                const SizedBox(height: 20),

                // Structure
                if (point.structure.isNotEmpty) ...[
                  Text('Cấu trúc', style: theme.textTheme.titleMedium),
                  const SizedBox(height: 8),
                  GlassCard(
                    padding: const EdgeInsets.all(16),
                    child: Text(point.structure,
                        style: theme.textTheme.bodyLarge
                            ?.copyWith(fontWeight: FontWeight.w500)),
                  ),
                  const SizedBox(height: 20),
                ],

                // Explanation
                if (point.explanation != null &&
                    point.explanation!.isNotEmpty) ...[
                  Text('Giải thích', style: theme.textTheme.titleMedium),
                  const SizedBox(height: 8),
                  GlassCard(
                    padding: const EdgeInsets.all(16),
                    child: Text(point.explanation!,
                        style: theme.textTheme.bodyMedium),
                  ),
                  const SizedBox(height: 20),
                ],

                // Examples
                if (point.examples.isNotEmpty) ...[
                  Text('Ví dụ (${point.examples.length})',
                      style: theme.textTheme.titleMedium),
                  const SizedBox(height: 8),
                  ...point.examples.map((ex) => Padding(
                        padding: const EdgeInsets.only(bottom: 8),
                        child: GlassCard(
                          padding: const EdgeInsets.all(14),
                          child: Text(ex, style: theme.textTheme.bodyMedium),
                        ),
                      )),
                ],

                // Practice button
                const SizedBox(height: 20),
                SizedBox(
                  width: double.infinity,
                  height: 48,
                  child: ElevatedButton.icon(
                    onPressed: () => Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (_) =>
                            GrammarExerciseScreen(slug: slug),
                      ),
                    ),
                    icon: const Icon(Icons.quiz_outlined),
                    label: const Text('Làm bài tập'),
                  ),
                ),
                const SizedBox(height: 24),
              ],
            ),
          );
        },
      ),
    );
  }
}

class GrammarExerciseScreen extends ConsumerStatefulWidget {
  final String slug;
  const GrammarExerciseScreen({super.key, required this.slug});

  @override
  ConsumerState<GrammarExerciseScreen> createState() =>
      _GrammarExerciseScreenState();
}

class _GrammarExerciseScreenState
    extends ConsumerState<GrammarExerciseScreen> {
  List<ExerciseQuestion> _questions = [];
  Map<int, int> _answers = {};
  bool _submitted = false;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadQuestions();
  }

  Future<void> _loadQuestions() async {
    try {
      final questions = await ref
          .read(grammarRepositoryProvider)
          .getExercise(widget.slug);
      setState(() {
        _questions = questions;
        _loading = false;
      });
    } catch (e) {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    if (_loading) {
      return Scaffold(
        appBar: AppBar(title: const Text('Bài tập')),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    final correctCount = _submitted
        ? _answers.entries
            .where((e) => e.value == _questions[e.key].correctIndex)
            .length
        : 0;

    return Scaffold(
      appBar: AppBar(
        title: Text('Bài tập (${_questions.length} câu)'),
      ),
      body: ListView.builder(
        padding: const EdgeInsets.all(20),
        itemCount: _questions.length + (_submitted ? 1 : 1),
        itemBuilder: (context, i) {
          if (i == _questions.length) {
            if (_submitted) {
              return GlassCard(
                gradient: correctCount == _questions.length
                    ? AppColors.accentGradient
                    : null,
                padding: const EdgeInsets.all(20),
                child: Column(
                  children: [
                    Text(
                        '$correctCount / ${_questions.length} câu đúng',
                        style: theme.textTheme.headlineMedium?.copyWith(
                            color: correctCount == _questions.length
                                ? Colors.white
                                : null)),
                  ],
                ),
              );
            }
            return Padding(
              padding: const EdgeInsets.only(top: 8, bottom: 24),
              child: SizedBox(
                width: double.infinity,
                height: 48,
                child: ElevatedButton(
                  onPressed: _answers.length == _questions.length
                      ? () => setState(() => _submitted = true)
                      : null,
                  child: const Text('Nộp bài'),
                ),
              ),
            );
          }

          final q = _questions[i];
          final selected = _answers[i];

          return Padding(
            padding: const EdgeInsets.only(bottom: 16),
            child: GlassCard(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Câu ${i + 1}',
                      style: theme.textTheme.labelMedium),
                  const SizedBox(height: 4),
                  Text(q.question,
                      style: theme.textTheme.bodyLarge
                          ?.copyWith(fontWeight: FontWeight.w500)),
                  const SizedBox(height: 12),
                  ...q.options.asMap().entries.map((entry) {
                    final idx = entry.key;
                    final text = entry.value;
                    final isSelected = selected == idx;
                    final isCorrect = idx == q.correctIndex;

                    Color? bgColor;
                    if (_submitted) {
                      if (isCorrect) bgColor = AppColors.accent.withOpacity(0.15);
                      if (isSelected && !isCorrect) bgColor = AppColors.error.withOpacity(0.15);
                    } else if (isSelected) {
                      bgColor = AppColors.primary.withOpacity(0.12);
                    }

                    return Padding(
                      padding: const EdgeInsets.only(bottom: 6),
                      child: InkWell(
                        onTap: _submitted
                            ? null
                            : () => setState(() => _answers[i] = idx),
                        borderRadius: BorderRadius.circular(10),
                        child: Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: bgColor,
                            borderRadius: BorderRadius.circular(10),
                            border: Border.all(
                              color: isSelected && !_submitted
                                  ? AppColors.primary
                                  : Colors.transparent,
                            ),
                          ),
                          child: Row(
                            children: [
                              Container(
                                width: 24,
                                height: 24,
                                decoration: BoxDecoration(
                                  shape: BoxShape.circle,
                                  border: Border.all(
                                    color: isSelected
                                        ? AppColors.primary
                                        : theme.dividerColor,
                                    width: isSelected ? 2 : 1,
                                  ),
                                  color: isSelected
                                      ? AppColors.primary
                                      : null,
                                ),
                                child: isSelected
                                    ? const Icon(Icons.check,
                                        size: 14, color: Colors.white)
                                    : null,
                              ),
                              const SizedBox(width: 10),
                              Expanded(
                                child: Text(text,
                                    style: theme.textTheme.bodyMedium),
                              ),
                            ],
                          ),
                        ),
                      ),
                    );
                  }),
                  if (_submitted &&
                      q.explanation != null &&
                      q.explanation!.isNotEmpty)
                    Padding(
                      padding: const EdgeInsets.only(top: 8),
                      child: Container(
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: AppColors.info.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text('💡 ${q.explanation}',
                            style: theme.textTheme.bodySmall),
                      ),
                    ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}
