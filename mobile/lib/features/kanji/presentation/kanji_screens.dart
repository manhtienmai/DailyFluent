import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/colors.dart';
import '../../../shared/widgets/glass_card.dart';
import '../../../shared/widgets/shimmer_loading.dart';
import '../providers.dart';
import '../domain/models.dart';

class KanjiLevelListScreen extends ConsumerWidget {
  const KanjiLevelListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final levelsAsync = ref.watch(kanjiLevelsProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Kanji JLPT')),
      body: levelsAsync.when(
        loading: () => const Padding(
          padding: EdgeInsets.all(20),
          child: ShimmerList(itemCount: 5, itemHeight: 100),
        ),
        error: (e, _) => Center(child: Text('Lỗi: $e')),
        data: (levels) => ListView.builder(
          padding: const EdgeInsets.all(20),
          itemCount: levels.length,
          itemBuilder: (context, i) {
            final group = levels[i];
            final color = AppColors.jlptColor(group.level);
            return Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: GlassCard(
                onTap: () => Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) =>
                        KanjiLessonListScreen(group: group),
                  ),
                ),
                padding: const EdgeInsets.all(20),
                child: Row(
                  children: [
                    Container(
                      width: 56,
                      height: 56,
                      decoration: BoxDecoration(
                        color: color.withOpacity(0.15),
                        borderRadius: BorderRadius.circular(14),
                      ),
                      alignment: Alignment.center,
                      child: Text(
                        group.level,
                        style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.w700,
                          color: color,
                        ),
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'JLPT ${group.level}',
                            style: Theme.of(context)
                                .textTheme
                                .titleMedium
                                ?.copyWith(fontWeight: FontWeight.w600),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            '${group.totalKanji} kanji · ${group.lessons.length} bài',
                            style: Theme.of(context).textTheme.bodySmall,
                          ),
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

class KanjiLessonListScreen extends StatelessWidget {
  final JlptGroup group;
  const KanjiLessonListScreen({super.key, required this.group});

  @override
  Widget build(BuildContext context) {
    final color = AppColors.jlptColor(group.level);

    return Scaffold(
      appBar: AppBar(title: Text('JLPT ${group.level}')),
      body: ListView.builder(
        padding: const EdgeInsets.all(20),
        itemCount: group.lessons.length,
        itemBuilder: (context, i) {
          final lesson = group.lessons[i];
          return Padding(
            padding: const EdgeInsets.only(bottom: 10),
            child: GlassCard(
              onTap: () => Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => KanjiGridScreen(lesson: lesson),
                ),
              ),
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  Container(
                    width: 40,
                    height: 40,
                    decoration: BoxDecoration(
                      color: color.withOpacity(0.12),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    alignment: Alignment.center,
                    child: Text(
                      '${lesson.lessonNumber}',
                      style: TextStyle(
                        fontWeight: FontWeight.w700,
                        color: color,
                      ),
                    ),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          lesson.topic.isNotEmpty
                              ? lesson.topic
                              : 'Bài ${lesson.lessonNumber}',
                          style: Theme.of(context)
                              .textTheme
                              .titleSmall
                              ?.copyWith(
                                fontWeight: FontWeight.w600,
                                color: Theme.of(context)
                                    .textTheme
                                    .bodyLarge
                                    ?.color,
                              ),
                        ),
                        Text(
                          '${lesson.kanjis.length} kanji',
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                      ],
                    ),
                  ),
                  // Preview kanji chars
                  ...lesson.kanjis.take(5).map((k) => Padding(
                        padding: const EdgeInsets.only(left: 4),
                        child: Text(k.char,
                            style: const TextStyle(fontSize: 18)),
                      )),
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}

class KanjiGridScreen extends StatelessWidget {
  final KanjiLesson lesson;
  const KanjiGridScreen({super.key, required this.lesson});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(lesson.topic.isNotEmpty
            ? lesson.topic
            : 'Bài ${lesson.lessonNumber}'),
      ),
      body: GridView.builder(
        padding: const EdgeInsets.all(16),
        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: 4,
          crossAxisSpacing: 10,
          mainAxisSpacing: 10,
          childAspectRatio: 0.85,
        ),
        itemCount: lesson.kanjis.length,
        itemBuilder: (context, i) {
          final k = lesson.kanjis[i];
          return GlassCard(
            onTap: () => Navigator.push(
              context,
              MaterialPageRoute(
                builder: (_) => KanjiDetailScreen(char: k.char),
              ),
            ),
            padding: const EdgeInsets.all(8),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(k.char,
                    style: const TextStyle(
                        fontSize: 32, fontWeight: FontWeight.w500)),
                const SizedBox(height: 4),
                Text(
                  k.sinoVi,
                  style: Theme.of(context).textTheme.bodySmall,
                  textAlign: TextAlign.center,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}

class KanjiDetailScreen extends ConsumerWidget {
  final String char;
  const KanjiDetailScreen({super.key, required this.char});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final detailAsync = ref.watch(kanjiDetailProvider(char));
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: Text('Kanji $char')),
      body: detailAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Lỗi: $e')),
        data: (detail) => SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Main kanji card
              Center(
                child: GlassCard(
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    children: [
                      Text(detail.char,
                          style: const TextStyle(fontSize: 72)),
                      const SizedBox(height: 8),
                      Text(detail.sinoVi,
                          style: theme.textTheme.headlineSmall?.copyWith(
                              color: AppColors.primary)),
                      if (detail.keyword.isNotEmpty)
                        Padding(
                          padding: const EdgeInsets.only(top: 4),
                          child: Text(detail.keyword,
                              style: theme.textTheme.bodyMedium),
                        ),
                      const SizedBox(height: 12),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          _infoChip('JLPT ${detail.jlptLevel}',
                              AppColors.jlptColor(detail.jlptLevel)),
                          if (detail.strokes != null) ...[
                            const SizedBox(width: 8),
                            _infoChip(
                                '${detail.strokes} nét', AppColors.info),
                          ],
                        ],
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 20),

              // Readings
              _sectionTitle(theme, 'Cách đọc'),
              GlassCard(
                padding: const EdgeInsets.all(16),
                child: Column(
                  children: [
                    if (detail.onyomi.isNotEmpty)
                      _readingRow('Onyomi (音)', detail.onyomi),
                    if (detail.kunyomi.isNotEmpty) ...[
                      if (detail.onyomi.isNotEmpty) const Divider(height: 16),
                      _readingRow('Kunyomi (訓)', detail.kunyomi),
                    ],
                    if (detail.meaningVi.isNotEmpty) ...[
                      const Divider(height: 16),
                      _readingRow('Nghĩa', detail.meaningVi),
                    ],
                  ],
                ),
              ),

              // Formation
              if (detail.formation.isNotEmpty) ...[
                const SizedBox(height: 20),
                _sectionTitle(theme, 'Cấu tạo'),
                GlassCard(
                  padding: const EdgeInsets.all(16),
                  child: Text(detail.formation,
                      style: theme.textTheme.bodyMedium),
                ),
              ],

              // Note
              if (detail.note.isNotEmpty) ...[
                const SizedBox(height: 20),
                _sectionTitle(theme, 'Ghi nhớ'),
                GlassCard(
                  padding: const EdgeInsets.all(16),
                  child:
                      Text(detail.note, style: theme.textTheme.bodyMedium),
                ),
              ],

              // Vocab list
              if (detail.vocab.isNotEmpty) ...[
                const SizedBox(height: 20),
                _sectionTitle(theme, 'Từ vựng (${detail.vocab.length})'),
                ...detail.vocab.map((v) => Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: GlassCard(
                        padding: const EdgeInsets.all(14),
                        child: Row(
                          children: [
                            Expanded(
                              child: Column(
                                crossAxisAlignment:
                                    CrossAxisAlignment.start,
                                children: [
                                  Text(v.word,
                                      style: theme.textTheme.titleMedium
                                          ?.copyWith(
                                              fontWeight: FontWeight.w600)),
                                  Text(v.reading,
                                      style: theme.textTheme.bodySmall),
                                ],
                              ),
                            ),
                            Expanded(
                              child: Text(v.meaning,
                                  style: theme.textTheme.bodyMedium,
                                  textAlign: TextAlign.end),
                            ),
                          ],
                        ),
                      ),
                    )),
              ],
              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
    );
  }

  Widget _sectionTitle(ThemeData theme, String title) => Padding(
        padding: const EdgeInsets.only(bottom: 8),
        child: Text(title, style: theme.textTheme.titleMedium),
      );

  Widget _readingRow(String label, String value) => Row(
        children: [
          SizedBox(
            width: 100,
            child: Text(label,
                style: const TextStyle(
                    fontWeight: FontWeight.w500, fontSize: 13)),
          ),
          Expanded(child: Text(value, style: const TextStyle(fontSize: 15))),
        ],
      );

  Widget _infoChip(String text, Color color) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
        decoration: BoxDecoration(
          color: color.withOpacity(0.15),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Text(text,
            style: TextStyle(
                color: color, fontSize: 12, fontWeight: FontWeight.w600)),
      );
}
