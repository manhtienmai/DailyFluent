import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/colors.dart';
import '../../../shared/widgets/glass_card.dart';
import '../../../shared/widgets/shimmer_loading.dart';
import '../providers.dart';

class VideoListScreen extends ConsumerWidget {
  const VideoListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final videosAsync = ref.watch(videoListProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Video')),
      body: videosAsync.when(
        loading: () => const Padding(
          padding: EdgeInsets.all(20),
          child: ShimmerList(itemCount: 4, itemHeight: 200),
        ),
        error: (e, _) => Center(child: Text('Lỗi: $e')),
        data: (videos) => ListView.builder(
          padding: const EdgeInsets.all(20),
          itemCount: videos.length,
          itemBuilder: (context, i) {
            final v = videos[i];
            return Padding(
              padding: const EdgeInsets.only(bottom: 16),
              child: GlassCard(
                onTap: () => Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => VideoDetailScreen(
                      slug: v['slug'] ?? '',
                    ),
                  ),
                ),
                padding: EdgeInsets.zero,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Thumbnail
                    Container(
                      height: 180,
                      width: double.infinity,
                      decoration: BoxDecoration(
                        color: AppColors.darkSurface,
                        borderRadius: const BorderRadius.vertical(
                            top: Radius.circular(16)),
                      ),
                      child: Stack(
                        alignment: Alignment.center,
                        children: [
                          if (v['thumbnail'] != null)
                            ClipRRect(
                              borderRadius: const BorderRadius.vertical(
                                  top: Radius.circular(16)),
                              child: Image.network(
                                v['thumbnail'],
                                fit: BoxFit.cover,
                                width: double.infinity,
                                height: 180,
                                errorBuilder: (_, __, ___) =>
                                    const Icon(Icons.play_circle_outline,
                                        size: 48, color: Colors.white54),
                              ),
                            )
                          else
                            const Icon(Icons.play_circle_outline,
                                size: 48, color: Colors.white54),
                          Container(
                            decoration: BoxDecoration(
                              color: Colors.black26,
                              shape: BoxShape.circle,
                            ),
                            padding: const EdgeInsets.all(8),
                            child: const Icon(Icons.play_arrow,
                                color: Colors.white, size: 32),
                          ),
                        ],
                      ),
                    ),
                    Padding(
                      padding: const EdgeInsets.all(14),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            v['title'] ?? '',
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
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                          ),
                          if (v['category'] != null) ...[
                            const SizedBox(height: 4),
                            Text(v['category'],
                                style:
                                    Theme.of(context).textTheme.bodySmall),
                          ],
                        ],
                      ),
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

class VideoDetailScreen extends ConsumerWidget {
  final String slug;
  const VideoDetailScreen({super.key, required this.slug});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Video')),
      body: FutureBuilder<Map<String, dynamic>>(
        future: ref.read(videoRepositoryProvider).getVideoDetail(slug),
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(child: Text('Lỗi: ${snapshot.error}'));
          }
          final data = snapshot.data!;
          final transcript =
              data['transcript'] as List? ?? data['subtitles'] as List? ?? [];

          return ListView(
            padding: const EdgeInsets.all(20),
            children: [
              // Video player placeholder
              Container(
                height: 220,
                decoration: BoxDecoration(
                  color: Colors.black,
                  borderRadius: BorderRadius.circular(12),
                ),
                alignment: Alignment.center,
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Icon(Icons.play_circle_filled,
                        size: 56, color: Colors.white70),
                    const SizedBox(height: 8),
                    Text(
                      'YouTube Player',
                      style: TextStyle(color: Colors.white60, fontSize: 12),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),
              Text(data['title'] ?? '',
                  style: theme.textTheme.titleLarge),
              const SizedBox(height: 20),

              // Transcript
              if (transcript.isNotEmpty) ...[
                Text('Phụ đề (${transcript.length})',
                    style: theme.textTheme.titleMedium),
                const SizedBox(height: 8),
                ...transcript.map((t) => Padding(
                      padding: const EdgeInsets.only(bottom: 6),
                      child: GlassCard(
                        padding: const EdgeInsets.all(12),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            if (t['time'] != null)
                              Text(t['time'],
                                  style: TextStyle(
                                      color: AppColors.primary,
                                      fontSize: 11,
                                      fontWeight: FontWeight.w600)),
                            Text(t['text'] ?? t['jp'] ?? '',
                                style: theme.textTheme.bodyMedium
                                    ?.copyWith(fontWeight: FontWeight.w500)),
                            if (t['vi'] != null)
                              Text(t['vi'],
                                  style: theme.textTheme.bodySmall),
                          ],
                        ),
                      ),
                    )),
              ],
            ],
          );
        },
      ),
    );
  }
}

class EbookListScreen extends ConsumerWidget {
  const EbookListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final ebooksAsync = ref.watch(ebookListProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Ebooks')),
      body: ebooksAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Lỗi: $e')),
        data: (ebooks) => ListView.builder(
          padding: const EdgeInsets.all(20),
          itemCount: ebooks.length,
          itemBuilder: (context, i) {
            final e = ebooks[i];
            return Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: GlassCard(
                onTap: () {},
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    Container(
                      width: 52,
                      height: 68,
                      decoration: BoxDecoration(
                        color: AppColors.jlptN1.withOpacity(0.12),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: const Icon(Icons.menu_book,
                          color: AppColors.jlptN1),
                    ),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(e['title'] ?? '',
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
                          if (e['author'] != null)
                            Text(e['author'],
                                style: Theme.of(context).textTheme.bodySmall),
                        ],
                      ),
                    ),
                    Icon(Icons.chevron_right_rounded,
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
