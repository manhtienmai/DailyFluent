import 'package:dio/dio.dart';

import '../../../core/api/api_client.dart';
import '../../../core/api/api_endpoints.dart';
import '../../../core/storage/secure_storage.dart';
import '../domain/models.dart';

/// Auth repository — handles login, signup, refresh, logout, and user fetching.
class AuthRepository {
  final ApiClient _api;
  final SecureStorage _storage;

  AuthRepository({required ApiClient api, required SecureStorage storage})
      : _api = api,
        _storage = storage;

  /// Login and store tokens.
  Future<User> login({
    required String email,
    required String password,
  }) async {
    final response = await _api.post(
      ApiConstants.login,
      data: {'email': email, 'password': password},
    );

    final data = response.data;
    if (data['success'] != true) {
      throw Exception(data['message'] ?? 'Login failed');
    }

    // Save tokens
    await _storage.saveTokens(
      accessToken: data['access_token'],
      refreshToken: data['refresh_token'],
    );

    return User.fromJson(data['user']);
  }

  /// Signup and store tokens.
  Future<User> signup({
    required String email,
    required String password1,
    required String password2,
  }) async {
    final response = await _api.post(
      ApiConstants.signup,
      data: {
        'email': email,
        'password1': password1,
        'password2': password2,
      },
    );

    final data = response.data;
    if (data['success'] != true) {
      throw Exception(data['message'] ?? 'Signup failed');
    }

    await _storage.saveTokens(
      accessToken: data['access_token'],
      refreshToken: data['refresh_token'],
    );

    return User.fromJson(data['user']);
  }

  /// Get current user info.
  Future<User> getCurrentUser() async {
    final response = await _api.get(ApiConstants.me);
    return User.fromJson(response.data);
  }

  /// Try to restore session from stored tokens.
  Future<User?> restoreSession() async {
    final hasTokens = await _storage.hasTokens();
    if (!hasTokens) return null;

    try {
      return await getCurrentUser();
    } on DioException catch (e) {
      if (e.response?.statusCode == 401) {
        // Token expired and refresh failed
        await _storage.clearTokens();
        return null;
      }
      rethrow;
    }
  }

  /// Logout — clear tokens.
  Future<void> logout() async {
    try {
      await _api.post(ApiConstants.logout);
    } catch (_) {
      // Ignore errors during logout
    }
    await _storage.clearTokens();
  }
}
