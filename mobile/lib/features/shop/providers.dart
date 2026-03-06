import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api/api_client.dart';
import 'data/repositories.dart';

final shopRepositoryProvider = Provider<ShopRepository>((ref) {
  return ShopRepository(api: ref.watch(apiClientProvider));
});

final walletRepositoryProvider = Provider<WalletRepository>((ref) {
  return WalletRepository(api: ref.watch(apiClientProvider));
});

final notificationRepositoryProvider = Provider<NotificationRepository>(
    (ref) {
  return NotificationRepository(api: ref.watch(apiClientProvider));
});

final feedbackRepositoryProvider = Provider<FeedbackRepository>((ref) {
  return FeedbackRepository(api: ref.watch(apiClientProvider));
});

final shopItemsProvider =
    FutureProvider<List<Map<String, dynamic>>>((ref) async {
  return ref.watch(shopRepositoryProvider).getItems();
});

final walletBalanceProvider =
    FutureProvider<Map<String, dynamic>>((ref) async {
  return ref.watch(walletRepositoryProvider).getBalance();
});

final notificationsProvider =
    FutureProvider<List<Map<String, dynamic>>>((ref) async {
  return ref.watch(notificationRepositoryProvider).getList();
});
