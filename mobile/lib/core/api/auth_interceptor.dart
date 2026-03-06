import 'package:dio/dio.dart';

import '../storage/secure_storage.dart';
import 'api_endpoints.dart';

/// Dio interceptor that:
/// 1. Attaches JWT Bearer token to every request
/// 2. Auto-refreshes expired tokens on 401
/// 3. Retries the original request after refresh
class AuthInterceptor extends QueuedInterceptor {
  final Dio _dio;
  final SecureStorage _storage;

  AuthInterceptor({
    required Dio dio,
    required SecureStorage storage,
  })  : _dio = dio,
        _storage = storage;

  @override
  void onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    // Skip auth for public endpoints
    final publicPaths = [
      ApiConstants.login,
      ApiConstants.signup,
      ApiConstants.refreshToken,
    ];

    final isPublic = publicPaths.any((path) => options.path.contains(path));

    if (!isPublic) {
      final token = await _storage.getAccessToken();
      if (token != null) {
        options.headers['Authorization'] = 'Bearer $token';
      }
    }

    handler.next(options);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    if (err.response?.statusCode == 401) {
      // Don't try to refresh if we're already refreshing or logging in
      final isRefreshRequest =
          err.requestOptions.path.contains(ApiConstants.refreshToken);
      final isLoginRequest =
          err.requestOptions.path.contains(ApiConstants.login);

      if (isRefreshRequest || isLoginRequest) {
        return handler.next(err);
      }

      // Try to refresh the token
      try {
        final refreshToken = await _storage.getRefreshToken();
        if (refreshToken == null) {
          return handler.next(err);
        }

        final refreshResponse = await _dio.post(
          ApiConstants.refreshToken,
          data: {'refresh_token': refreshToken},
        );

        if (refreshResponse.statusCode == 200) {
          final newAccessToken = refreshResponse.data['access_token'];
          await _storage.setAccessToken(newAccessToken);

          // Retry the original request with new token
          final options = err.requestOptions;
          options.headers['Authorization'] = 'Bearer $newAccessToken';

          final retryResponse = await _dio.fetch(options);
          return handler.resolve(retryResponse);
        }
      } catch (e) {
        // Refresh failed — clear tokens (user needs to re-login)
        await _storage.clearTokens();
      }
    }

    handler.next(err);
  }
}
