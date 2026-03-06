import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/theme/colors.dart';
import '../../../shared/widgets/glass_card.dart';
import '../../auth/providers.dart';
import '../../settings/providers.dart';

class AccountScreen extends ConsumerWidget {
  const AccountScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(currentUserProvider);
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Tài khoản'),
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          // ── User Profile Card ────────────────────────────
          GlassCard(
            padding: const EdgeInsets.all(20),
            child: Row(
              children: [
                CircleAvatar(
                  radius: 30,
                  backgroundColor: AppColors.primary,
                  child: Text(
                    user?.initials ?? '?',
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 22,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        user?.displayName ?? 'Người dùng',
                        style: theme.textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        user?.email ?? '',
                        style: theme.textTheme.bodySmall,
                      ),
                    ],
                  ),
                ),
                IconButton(
                  onPressed: () {},
                  icon: const Icon(Icons.edit_outlined, size: 20),
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),

          // ── Settings Section ─────────────────────────────
          Text('Cài đặt', style: theme.textTheme.titleLarge),
          const SizedBox(height: 12),

          // Theme toggle
          GlassCard(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
            child: SwitchListTile(
              contentPadding: EdgeInsets.zero,
              title: const Text('Chế độ tối'),
              subtitle: Text(
                isDark ? 'Đang bật' : 'Đang tắt',
                style: theme.textTheme.bodySmall,
              ),
              secondary: Icon(
                isDark ? Icons.dark_mode : Icons.light_mode,
                color: isDark ? AppColors.streakGold : AppColors.warning,
              ),
              value: isDark,
              onChanged: (value) {
                ref.read(themeModeProvider.notifier).setThemeMode(
                      value ? ThemeMode.dark : ThemeMode.light,
                    );
              },
            ),
          ),
          const SizedBox(height: 10),

          // Menu items
          _menuItem(context, Icons.account_balance_wallet_outlined, 'Ví',
              onTap: () => context.go('/account/wallet')),
          const SizedBox(height: 10),
          _menuItem(context, Icons.shopping_bag_outlined, 'Cửa hàng',
              onTap: () => context.go('/account/shop')),
          const SizedBox(height: 10),
          _menuItem(context, Icons.notifications_outlined, 'Thông báo',
              onTap: () => context.go('/account/notifications')),
          const SizedBox(height: 10),
          _menuItem(context, Icons.feedback_outlined, 'Góp ý',
              onTap: () => context.go('/account/feedback')),
          const SizedBox(height: 10),
          _menuItem(context, Icons.info_outline, 'Về DailyFluent',
              onTap: () {}),
          const SizedBox(height: 24),

          // ── Logout ───────────────────────────────────────
          SizedBox(
            height: 48,
            child: OutlinedButton.icon(
              onPressed: () => _showLogoutDialog(context, ref),
              icon: const Icon(Icons.logout, color: AppColors.error),
              label: const Text(
                'Đăng xuất',
                style: TextStyle(color: AppColors.error),
              ),
              style: OutlinedButton.styleFrom(
                side: const BorderSide(color: AppColors.error),
              ),
            ),
          ),
          const SizedBox(height: 24),
        ],
      ),
    );
  }

  Widget _menuItem(BuildContext context, IconData icon, String title,
      {required VoidCallback onTap}) {
    return GlassCard(
      onTap: onTap,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      child: Row(
        children: [
          Icon(icon, size: 22),
          const SizedBox(width: 14),
          Expanded(
            child: Text(
              title,
              style: Theme.of(context).textTheme.bodyLarge,
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

  void _showLogoutDialog(BuildContext context, WidgetRef ref) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Đăng xuất'),
        content: const Text('Bạn có chắc muốn đăng xuất?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Hủy'),
          ),
          FilledButton(
            onPressed: () {
              Navigator.pop(ctx);
              ref.read(authProvider.notifier).logout();
            },
            style: FilledButton.styleFrom(
              backgroundColor: AppColors.error,
            ),
            child: const Text('Đăng xuất'),
          ),
        ],
      ),
    );
  }
}
