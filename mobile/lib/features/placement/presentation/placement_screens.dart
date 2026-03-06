import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/colors.dart';
import '../../../shared/widgets/glass_card.dart';
import '../../../shared/widgets/loading_button.dart';
import '../providers.dart';

class PlacementIntroScreen extends ConsumerStatefulWidget {
  const PlacementIntroScreen({super.key});

  @override
  ConsumerState<PlacementIntroScreen> createState() =>
      _PlacementIntroScreenState();
}

class _PlacementIntroScreenState
    extends ConsumerState<PlacementIntroScreen> {
  bool _loading = false;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Kiểm tra trình độ')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          children: [
            const SizedBox(height: 24),
            const Text('🎯', style: TextStyle(fontSize: 72)),
            const SizedBox(height: 24),
            Text('Placement Test',
                style: theme.textTheme.headlineMedium),
            const SizedBox(height: 12),
            Text(
              'Bài kiểm tra thích ứng sẽ đánh giá trình độ tiếng Anh của bạn qua nhiều kỹ năng: ngữ pháp, từ vựng, đọc hiểu.',
              style: theme.textTheme.bodyMedium,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 32),

            // Features
            _feature(theme, Icons.timer_outlined, 'Thời gian',
                '15-20 phút'),
            _feature(theme, Icons.auto_graph, 'Thích ứng',
                'Câu hỏi tự điều chỉnh theo trình độ'),
            _feature(theme, Icons.diamond_outlined, 'Kết quả',
                'Ước tính điểm TOEIC + lộ trình học'),

            const SizedBox(height: 40),
            SizedBox(
              width: double.infinity,
              child: LoadingButton(
                onPressed: () async {
                  setState(() => _loading = true);
                  try {
                    final result = await ref
                        .read(placementRepositoryProvider)
                        .startTest();
                    if (!mounted) return;
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (_) => PlacementTestScreen(
                            testId: result['test_id'] ?? result['id']),
                      ),
                    );
                  } finally {
                    if (mounted) setState(() => _loading = false);
                  }
                },
                isLoading: _loading,
                label: 'Bắt đầu kiểm tra',
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _feature(ThemeData theme, IconData icon, String title, String sub) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: GlassCard(
        padding: const EdgeInsets.all(14),
        child: Row(
          children: [
            Icon(icon, color: AppColors.primary),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title,
                      style: theme.textTheme.titleSmall?.copyWith(
                          fontWeight: FontWeight.w600,
                          color: theme.textTheme.bodyLarge?.color)),
                  Text(sub, style: theme.textTheme.bodySmall),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class PlacementTestScreen extends ConsumerStatefulWidget {
  final int testId;
  const PlacementTestScreen({super.key, required this.testId});

  @override
  ConsumerState<PlacementTestScreen> createState() =>
      _PlacementTestScreenState();
}

class _PlacementTestScreenState
    extends ConsumerState<PlacementTestScreen> {
  Map<String, dynamic>? _currentQ;
  int _answered = 0;
  bool _loading = true;
  bool _done = false;

  @override
  void initState() {
    super.initState();
    _loadNext();
  }

  Future<void> _loadNext() async {
    setState(() => _loading = true);
    try {
      final q = await ref
          .read(placementRepositoryProvider)
          .getNextQuestion(widget.testId);
      if (q['done'] == true || q['finished'] == true) {
        setState(() {
          _done = true;
          _loading = false;
        });
      } else {
        setState(() {
          _currentQ = q;
          _loading = false;
        });
      }
    } catch (e) {
      setState(() {
        _done = true;
        _loading = false;
      });
    }
  }

  Future<void> _submitAnswer(String answer) async {
    if (_currentQ == null) return;
    final qid = _currentQ!['id'] ?? _currentQ!['question_id'];
    await ref.read(placementRepositoryProvider).submitAnswer(
          widget.testId,
          qid,
          answer,
        );
    setState(() => _answered++);
    _loadNext();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    if (_done) {
      return Scaffold(
        appBar: AppBar(title: const Text('Hoàn thành!')),
        body: FutureBuilder<Map<String, dynamic>>(
          future: ref
              .read(placementRepositoryProvider)
              .getResult(widget.testId),
          builder: (context, snap) {
            if (!snap.hasData) {
              return const Center(child: CircularProgressIndicator());
            }
            final result = snap.data!;
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Text('🏆', style: TextStyle(fontSize: 64)),
                    const SizedBox(height: 16),
                    Text('Kết quả',
                        style: theme.textTheme.headlineMedium),
                    const SizedBox(height: 12),
                    if (result['estimated_toeic'] != null)
                      Text(
                        'TOEIC ≈ ${result['estimated_toeic']}',
                        style: theme.textTheme.displaySmall
                            ?.copyWith(color: AppColors.primary),
                      ),
                    if (result['level'] != null) ...[
                      const SizedBox(height: 8),
                      Text('Level: ${result['level']}',
                          style: theme.textTheme.titleMedium),
                    ],
                    const SizedBox(height: 32),
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton(
                        onPressed: () => Navigator.pop(context),
                        child: const Text('Xem lộ trình học'),
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

    return Scaffold(
      appBar: AppBar(title: Text('Câu ${_answered + 1}')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _currentQ == null
              ? const Center(child: Text('Lỗi'))
              : Padding(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        _currentQ!['text'] ?? _currentQ!['question'] ?? '',
                        style: theme.textTheme.bodyLarge
                            ?.copyWith(fontWeight: FontWeight.w500),
                      ),
                      const SizedBox(height: 20),
                      ...(_currentQ!['choices'] as List? ??
                              _currentQ!['options'] as List? ??
                              [])
                          .map((c) {
                        final text = c is String ? c : c['text'] ?? '';
                        final key = c is String
                            ? c
                            : c['key'] ?? c['label'] ?? text;
                        return Padding(
                          padding: const EdgeInsets.only(bottom: 10),
                          child: SizedBox(
                            width: double.infinity,
                            child: OutlinedButton(
                              onPressed: () =>
                                  _submitAnswer(key.toString()),
                              style: OutlinedButton.styleFrom(
                                padding: const EdgeInsets.all(14),
                              ),
                              child: Text(text.toString(),
                                  textAlign: TextAlign.start),
                            ),
                          ),
                        );
                      }),
                    ],
                  ),
                ),
    );
  }
}
