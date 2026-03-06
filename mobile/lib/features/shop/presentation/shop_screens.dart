import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/colors.dart';
import '../../../shared/widgets/glass_card.dart';
import '../../../shared/widgets/shimmer_loading.dart';
import '../providers.dart';

class ShopScreen extends ConsumerWidget {
  const ShopScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final itemsAsync = ref.watch(shopItemsProvider);
    final balanceAsync = ref.watch(walletBalanceProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Cửa hàng'),
        actions: [
          // Wallet balance
          balanceAsync.when(
            data: (b) => Padding(
              padding: const EdgeInsets.only(right: 16),
              child: Center(
                child: Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: AppColors.streakGold.withOpacity(0.15),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Row(
                    children: [
                      const Text('💰', style: TextStyle(fontSize: 14)),
                      const SizedBox(width: 4),
                      Text('${b['balance'] ?? 0}',
                          style: TextStyle(
                              color: AppColors.streakGold,
                              fontWeight: FontWeight.w600)),
                    ],
                  ),
                ),
              ),
            ),
            loading: () => const SizedBox.shrink(),
            error: (_, __) => const SizedBox.shrink(),
          ),
        ],
      ),
      body: itemsAsync.when(
        loading: () => const Padding(
          padding: EdgeInsets.all(20),
          child: ShimmerList(itemCount: 6, itemHeight: 90),
        ),
        error: (e, _) => Center(child: Text('Lỗi: $e')),
        data: (items) => GridView.builder(
          padding: const EdgeInsets.all(20),
          gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: 2,
            crossAxisSpacing: 12,
            mainAxisSpacing: 12,
            childAspectRatio: 0.85,
          ),
          itemCount: items.length,
          itemBuilder: (context, i) {
            final item = items[i];
            return GlassCard(
              padding: const EdgeInsets.all(14),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(item['icon'] ?? '🎁',
                      style: const TextStyle(fontSize: 36)),
                  Column(
                    children: [
                      Text(item['name'] ?? '',
                          style: theme.textTheme.titleSmall?.copyWith(
                              fontWeight: FontWeight.w600,
                              color: theme.textTheme.bodyLarge?.color),
                          textAlign: TextAlign.center),
                      const SizedBox(height: 4),
                      Text('${item['price'] ?? 0} xu',
                          style: theme.textTheme.bodySmall?.copyWith(
                              color: AppColors.streakGold,
                              fontWeight: FontWeight.w600)),
                    ],
                  ),
                  SizedBox(
                    width: double.infinity,
                    height: 32,
                    child: ElevatedButton(
                      onPressed: () async {
                        await ref
                            .read(shopRepositoryProvider)
                            .purchase(item['id']);
                        ref.invalidate(walletBalanceProvider);
                        if (context.mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(
                                content: Text('Mua thành công! 🎉')),
                          );
                        }
                      },
                      style: ElevatedButton.styleFrom(
                        padding: EdgeInsets.zero,
                        textStyle: const TextStyle(fontSize: 12),
                      ),
                      child: const Text('Mua'),
                    ),
                  ),
                ],
              ),
            );
          },
        ),
      ),
    );
  }
}

class WalletScreen extends ConsumerWidget {
  const WalletScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final balanceAsync = ref.watch(walletBalanceProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Ví')),
      body: balanceAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Lỗi: $e')),
        data: (data) => SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Column(
            children: [
              GlassCard(
                gradient: AppColors.primaryGradient,
                padding: const EdgeInsets.all(24),
                child: Column(
                  children: [
                    const Text('Số dư',
                        style: TextStyle(color: Colors.white70, fontSize: 14)),
                    const SizedBox(height: 8),
                    Text(
                      '${data['balance'] ?? 0} xu',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 36,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),
              Text('Lịch sử giao dịch', style: theme.textTheme.titleLarge),
              const SizedBox(height: 12),
              if (data['transactions'] != null)
                ...((data['transactions'] as List?)?.map((t) => Padding(
                          padding: const EdgeInsets.only(bottom: 8),
                          child: GlassCard(
                            padding: const EdgeInsets.all(14),
                            child: Row(
                              children: [
                                Icon(
                                  (t['amount'] as num?) != null &&
                                          (t['amount'] as num) > 0
                                      ? Icons.add_circle_outline
                                      : Icons.remove_circle_outline,
                                  color: (t['amount'] as num?) != null &&
                                          (t['amount'] as num) > 0
                                      ? AppColors.accent
                                      : AppColors.error,
                                ),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: Text(t['description'] ?? '',
                                      style: theme.textTheme.bodyMedium),
                                ),
                                Text(
                                  '${(t['amount'] as num?) != null && (t['amount'] as num) > 0 ? '+' : ''}${t['amount']}',
                                  style: theme.textTheme.titleSmall?.copyWith(
                                    color: (t['amount'] as num?) != null &&
                                            (t['amount'] as num) > 0
                                        ? AppColors.accent
                                        : AppColors.error,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        )) ??
                    [])
              else
                GlassCard(
                  padding: const EdgeInsets.all(16),
                  child: Center(
                    child: Text('Chưa có giao dịch nào',
                        style: theme.textTheme.bodySmall),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

class NotificationsScreen extends ConsumerWidget {
  const NotificationsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final notiAsync = ref.watch(notificationsProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Thông báo')),
      body: notiAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Lỗi: $e')),
        data: (notis) {
          if (notis.isEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Text('🔔', style: TextStyle(fontSize: 48)),
                  const SizedBox(height: 12),
                  Text('Không có thông báo mới',
                      style: theme.textTheme.bodyMedium),
                ],
              ),
            );
          }
          return ListView.builder(
            padding: const EdgeInsets.all(20),
            itemCount: notis.length,
            itemBuilder: (context, i) {
              final n = notis[i];
              final isRead = n['is_read'] == true;
              return Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: GlassCard(
                  onTap: () {
                    if (!isRead && n['id'] != null) {
                      ref
                          .read(notificationRepositoryProvider)
                          .markRead(n['id']);
                      ref.invalidate(notificationsProvider);
                    }
                  },
                  padding: const EdgeInsets.all(14),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      if (!isRead)
                        Container(
                          width: 8,
                          height: 8,
                          margin: const EdgeInsets.only(top: 6, right: 10),
                          decoration: const BoxDecoration(
                            color: AppColors.primary,
                            shape: BoxShape.circle,
                          ),
                        )
                      else
                        const SizedBox(width: 18),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(n['title'] ?? '',
                                style: theme.textTheme.titleSmall?.copyWith(
                                  fontWeight:
                                      isRead ? FontWeight.w400 : FontWeight.w600,
                                  color: theme.textTheme.bodyLarge?.color,
                                )),
                            if (n['message'] != null)
                              Text(n['message'],
                                  style: theme.textTheme.bodySmall),
                            if (n['created_at'] != null)
                              Padding(
                                padding: const EdgeInsets.only(top: 4),
                                child: Text(n['created_at'],
                                    style: theme.textTheme.bodySmall
                                        ?.copyWith(fontSize: 11)),
                              ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }
}

class FeedbackScreen extends ConsumerStatefulWidget {
  const FeedbackScreen({super.key});

  @override
  ConsumerState<FeedbackScreen> createState() => _FeedbackScreenState();
}

class _FeedbackScreenState extends ConsumerState<FeedbackScreen> {
  final _controller = TextEditingController();
  String _type = 'feedback';
  bool _sending = false;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Góp ý')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Loại góp ý', style: theme.textTheme.titleMedium),
            const SizedBox(height: 8),
            SegmentedButton<String>(
              segments: const [
                ButtonSegment(value: 'feedback', label: Text('Góp ý')),
                ButtonSegment(value: 'bug', label: Text('Lỗi')),
                ButtonSegment(value: 'feature', label: Text('Tính năng')),
              ],
              selected: {_type},
              onSelectionChanged: (s) => setState(() => _type = s.first),
            ),
            const SizedBox(height: 20),
            Text('Nội dung', style: theme.textTheme.titleMedium),
            const SizedBox(height: 8),
            TextFormField(
              controller: _controller,
              maxLines: 6,
              decoration: const InputDecoration(
                hintText: 'Mô tả chi tiết...',
              ),
            ),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              height: 48,
              child: ElevatedButton(
                onPressed: _sending
                    ? null
                    : () async {
                        if (_controller.text.trim().isEmpty) return;
                        setState(() => _sending = true);
                        try {
                          await ref
                              .read(feedbackRepositoryProvider)
                              .submit(_type, _controller.text.trim());
                          if (mounted) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(
                                  content: Text('Cảm ơn bạn đã góp ý! 🙏')),
                            );
                            Navigator.pop(context);
                          }
                        } finally {
                          if (mounted) setState(() => _sending = false);
                        }
                      },
                child: _sending
                    ? const SizedBox(
                        width: 22,
                        height: 22,
                        child: CircularProgressIndicator(
                            strokeWidth: 2, color: Colors.white))
                    : const Text('Gửi góp ý'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
