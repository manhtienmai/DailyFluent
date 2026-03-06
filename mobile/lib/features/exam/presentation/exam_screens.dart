import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/colors.dart';
import '../../../shared/widgets/glass_card.dart';
import '../../../shared/widgets/shimmer_loading.dart';
import '../providers.dart';
import '../domain/models.dart';

class ExamListScreen extends ConsumerWidget {
  final String title;
  final FutureProvider<List<ExamTemplate>> provider;

  const ExamListScreen({
    super.key,
    required this.title,
    required this.provider,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final examsAsync = ref.watch(provider);

    return Scaffold(
      appBar: AppBar(title: Text(title)),
      body: examsAsync.when(
        loading: () => const Padding(
          padding: EdgeInsets.all(20),
          child: ShimmerList(itemCount: 6),
        ),
        error: (e, _) => Center(child: Text('Lỗi: $e')),
        data: (exams) => ListView.builder(
          padding: const EdgeInsets.all(20),
          itemCount: exams.length,
          itemBuilder: (context, i) {
            final exam = exams[i];
            return Padding(
              padding: const EdgeInsets.only(bottom: 10),
              child: GlassCard(
                onTap: () => Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => ExamDetailScreen(slug: exam.slug),
                  ),
                ),
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    Container(
                      width: 44,
                      height: 44,
                      decoration: BoxDecoration(
                        color: AppColors.primary.withOpacity(0.12),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      alignment: Alignment.center,
                      child: Text('${i + 1}',
                          style: TextStyle(
                              color: AppColors.primary,
                              fontWeight: FontWeight.w700)),
                    ),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(exam.title,
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
                          Text(
                            '${exam.questionCount} câu · ${exam.timeLimitMinutes} phút',
                            style: Theme.of(context).textTheme.bodySmall,
                          ),
                        ],
                      ),
                    ),
                    Icon(Icons.play_circle_outline,
                        color: AppColors.primary),
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

class ExamDetailScreen extends ConsumerWidget {
  final String slug;
  const ExamDetailScreen({super.key, required this.slug});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Chi tiết đề thi')),
      body: FutureBuilder<Map<String, dynamic>>(
        future: ref.read(examRepositoryProvider).getExamDetail(slug),
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(child: Text('Lỗi: ${snapshot.error}'));
          }
          final data = snapshot.data!;
          final exam = ExamTemplate.fromJson(data);

          return SingleChildScrollView(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                GlassCard(
                  gradient: AppColors.primaryGradient,
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(exam.title,
                          style: const TextStyle(
                              color: Colors.white,
                              fontSize: 22,
                              fontWeight: FontWeight.w700)),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          _infoBadge(Icons.quiz_outlined,
                              '${exam.questionCount} câu'),
                          const SizedBox(width: 16),
                          _infoBadge(Icons.timer_outlined,
                              '${exam.timeLimitMinutes} phút'),
                        ],
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
                if (exam.description.isNotEmpty) ...[
                  Text(exam.description,
                      style: theme.textTheme.bodyMedium),
                  const SizedBox(height: 20),
                ],
                SizedBox(
                  width: double.infinity,
                  height: 52,
                  child: ElevatedButton.icon(
                    onPressed: () => Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (_) => ExamTakingScreen(
                            slug: slug, examData: data),
                      ),
                    ),
                    icon: const Icon(Icons.play_arrow_rounded),
                    label: const Text('Bắt đầu làm bài'),
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _infoBadge(IconData icon, String text) => Row(
        children: [
          Icon(icon, size: 16, color: Colors.white70),
          const SizedBox(width: 4),
          Text(text,
              style: const TextStyle(color: Colors.white, fontSize: 13)),
        ],
      );
}

class ExamTakingScreen extends ConsumerStatefulWidget {
  final String slug;
  final Map<String, dynamic> examData;

  const ExamTakingScreen({
    super.key,
    required this.slug,
    required this.examData,
  });

  @override
  ConsumerState<ExamTakingScreen> createState() => _ExamTakingScreenState();
}

class _ExamTakingScreenState extends ConsumerState<ExamTakingScreen> {
  late List<ExamQuestion> _questions;
  final Map<int, String> _answers = {};
  int _currentPage = 0;
  bool _submitted = false;
  Timer? _timer;
  int _remainingSeconds = 0;

  @override
  void initState() {
    super.initState();
    _parseQuestions();
    final timeLimit = widget.examData['time_limit_minutes'] ?? 60;
    _remainingSeconds = timeLimit * 60;
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (_remainingSeconds > 0 && !_submitted) {
        setState(() => _remainingSeconds--);
      } else {
        timer.cancel();
        if (!_submitted) _submitExam();
      }
    });
  }

  void _parseQuestions() {
    final sections = widget.examData['sections'] as List?;
    if (sections != null) {
      _questions = sections.expand((s) {
        final qs = s['questions'] as List? ?? [];
        return qs.map((q) => ExamQuestion.fromJson(q));
      }).toList();
    } else {
      final qs = widget.examData['questions'] as List? ?? [];
      _questions = qs.map((q) => ExamQuestion.fromJson(q)).toList();
    }
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  void _submitExam() {
    setState(() => _submitted = true);
    _timer?.cancel();

    final correctCount = _answers.entries.where((e) {
      final q = _questions[e.key];
      return e.value == q.correctKey;
    }).length;

    final score = _questions.isNotEmpty
        ? (correctCount / _questions.length * 10)
        : 0.0;

    ref.read(examRepositoryProvider).submitQuizResult(
          quizType: 'exam',
          quizId: widget.slug,
          totalQuestions: _questions.length,
          correctCount: correctCount,
          score: score,
          answersDetail: _answers.entries
              .map((e) => {
                    'q': e.key,
                    'selected': _questions[e.key]
                        .choices
                        .indexWhere((c) => c.key == e.value),
                    'correct': _questions[e.key]
                        .choices
                        .indexWhere((c) => c.key == _questions[e.key].correctKey),
                    'is_correct': e.value == _questions[e.key].correctKey,
                  })
              .toList(),
        );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final minutes = _remainingSeconds ~/ 60;
    final seconds = _remainingSeconds % 60;

    if (_submitted) {
      final correctCount = _answers.entries
          .where((e) => e.value == _questions[e.key].correctKey)
          .length;

      return Scaffold(
        appBar: AppBar(title: const Text('Kết quả')),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  correctCount == _questions.length ? '🎉' : '📊',
                  style: const TextStyle(fontSize: 64),
                ),
                const SizedBox(height: 16),
                Text('$correctCount / ${_questions.length}',
                    style: theme.textTheme.displayMedium),
                const SizedBox(height: 8),
                Text(
                  '${(correctCount / _questions.length * 100).toStringAsFixed(0)}% đúng',
                  style: theme.textTheme.titleMedium
                      ?.copyWith(color: AppColors.accent),
                ),
                const SizedBox(height: 32),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: () => Navigator.pop(context),
                    child: const Text('Quay lại'),
                  ),
                ),
              ],
            ),
          ),
        ),
      );
    }

    if (_questions.isEmpty) {
      return Scaffold(
        appBar: AppBar(title: const Text('Làm bài')),
        body: const Center(child: Text('Không có câu hỏi')),
      );
    }

    final q = _questions[_currentPage];

    return Scaffold(
      appBar: AppBar(
        title: Text(
            '${_currentPage + 1}/${_questions.length}'),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 16),
            child: Center(
              child: Text(
                '${minutes.toString().padLeft(2, '0')}:${seconds.toString().padLeft(2, '0')}',
                style: TextStyle(
                  color: _remainingSeconds < 60
                      ? AppColors.error
                      : null,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ),
        ],
      ),
      body: Column(
        children: [
          LinearProgressIndicator(
            value: (_currentPage + 1) / _questions.length,
          ),
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (q.passage != null && q.passage!.isNotEmpty) ...[
                    GlassCard(
                      padding: const EdgeInsets.all(14),
                      child: Text(q.passage!,
                          style: theme.textTheme.bodyMedium),
                    ),
                    const SizedBox(height: 16),
                  ],
                  Text(q.text,
                      style: theme.textTheme.bodyLarge
                          ?.copyWith(fontWeight: FontWeight.w500)),
                  const SizedBox(height: 16),
                  ...q.choices.map((c) {
                    final isSelected = _answers[_currentPage] == c.key;
                    return Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: InkWell(
                        onTap: () =>
                            setState(() => _answers[_currentPage] = c.key),
                        borderRadius: BorderRadius.circular(12),
                        child: Container(
                          padding: const EdgeInsets.all(14),
                          decoration: BoxDecoration(
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(
                              color: isSelected
                                  ? AppColors.primary
                                  : theme.dividerTheme.color ??
                                      Colors.grey.shade300,
                              width: isSelected ? 2 : 1,
                            ),
                            color: isSelected
                                ? AppColors.primary.withOpacity(0.08)
                                : null,
                          ),
                          child: Row(
                            children: [
                              Container(
                                width: 28,
                                height: 28,
                                decoration: BoxDecoration(
                                  shape: BoxShape.circle,
                                  color: isSelected
                                      ? AppColors.primary
                                      : null,
                                  border: Border.all(
                                    color: isSelected
                                        ? AppColors.primary
                                        : Colors.grey,
                                  ),
                                ),
                                alignment: Alignment.center,
                                child: Text(
                                  c.key,
                                  style: TextStyle(
                                    color: isSelected
                                        ? Colors.white
                                        : null,
                                    fontWeight: FontWeight.w600,
                                    fontSize: 12,
                                  ),
                                ),
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Text(c.text,
                                    style: theme.textTheme.bodyMedium),
                              ),
                            ],
                          ),
                        ),
                      ),
                    );
                  }),
                ],
              ),
            ),
          ),
          // Navigation bar
          Container(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                if (_currentPage > 0)
                  Expanded(
                    child: OutlinedButton(
                      onPressed: () =>
                          setState(() => _currentPage--),
                      child: const Text('← Trước'),
                    ),
                  ),
                if (_currentPage > 0 &&
                    _currentPage < _questions.length - 1)
                  const SizedBox(width: 12),
                if (_currentPage < _questions.length - 1)
                  Expanded(
                    child: ElevatedButton(
                      onPressed: () =>
                          setState(() => _currentPage++),
                      child: const Text('Tiếp →'),
                    ),
                  ),
                if (_currentPage == _questions.length - 1)
                  Expanded(
                    child: ElevatedButton(
                      onPressed: _submitExam,
                      style: ElevatedButton.styleFrom(
                          backgroundColor: AppColors.accent),
                      child: const Text('Nộp bài'),
                    ),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
