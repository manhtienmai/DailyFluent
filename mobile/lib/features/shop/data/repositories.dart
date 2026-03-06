import '../../../core/api/api_client.dart';
import '../../../core/api/api_endpoints.dart';

class ShopRepository {
  final ApiClient _api;
  ShopRepository({required ApiClient api}) : _api = api;

  Future<List<Map<String, dynamic>>> getItems() async {
    final res = await _api.get(ApiConstants.shopItems);
    return (res.data as List).cast<Map<String, dynamic>>();
  }

  Future<Map<String, dynamic>> purchase(int itemId) async {
    final res =
        await _api.post(ApiConstants.shopPurchase, data: {'item_id': itemId});
    return res.data;
  }
}

class WalletRepository {
  final ApiClient _api;
  WalletRepository({required ApiClient api}) : _api = api;

  Future<Map<String, dynamic>> getBalance() async {
    final res = await _api.get(ApiConstants.walletBalance);
    return res.data;
  }
}

class NotificationRepository {
  final ApiClient _api;
  NotificationRepository({required ApiClient api}) : _api = api;

  Future<List<Map<String, dynamic>>> getList() async {
    final res = await _api.get(ApiConstants.notifications);
    return (res.data as List).cast<Map<String, dynamic>>();
  }

  Future<void> markRead(int id) async {
    await _api.patch(ApiConstants.notificationRead(id));
  }
}

class FeedbackRepository {
  final ApiClient _api;
  FeedbackRepository({required ApiClient api}) : _api = api;

  Future<void> submit(String type, String message) async {
    await _api.post(ApiConstants.feedback,
        data: {'type': type, 'message': message});
  }
}
