import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../storage/secure_storage.dart';
import 'api_endpoints.dart';
import 'auth_interceptor.dart';

/// Singleton Dio API client with JWT auth interceptor.
class ApiClient {
  late final Dio dio;
  final SecureStorage storage;

  ApiClient({required this.storage}) {
    dio = Dio(
      BaseOptions(
        baseUrl: ApiConstants.baseUrl,
        connectTimeout: const Duration(seconds: 15),
        receiveTimeout: const Duration(seconds: 15),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      ),
    );

    // Add auth interceptor
    dio.interceptors.add(
      AuthInterceptor(dio: dio, storage: storage),
    );

    // Add logging in debug mode
    dio.interceptors.add(
      LogInterceptor(
        requestBody: true,
        responseBody: true,
        logPrint: (obj) => print('[API] $obj'),
      ),
    );
  }

  // ── GET ──────────────────────────────────────────────────

  Future<Response> get(
    String path, {
    Map<String, dynamic>? queryParameters,
  }) async {
    return dio.get(path, queryParameters: queryParameters);
  }

  // ── POST ─────────────────────────────────────────────────

  Future<Response> post(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
  }) async {
    return dio.post(path, data: data, queryParameters: queryParameters);
  }

  // ── PUT ──────────────────────────────────────────────────

  Future<Response> put(
    String path, {
    dynamic data,
  }) async {
    return dio.put(path, data: data);
  }

  // ── PATCH ────────────────────────────────────────────────

  Future<Response> patch(
    String path, {
    dynamic data,
  }) async {
    return dio.patch(path, data: data);
  }

  // ── DELETE ───────────────────────────────────────────────

  Future<Response> delete(String path) async {
    return dio.delete(path);
  }
}

// ── Riverpod Providers ────────────────────────────────────

final secureStorageProvider = Provider<SecureStorage>((ref) {
  return SecureStorage();
});

final apiClientProvider = Provider<ApiClient>((ref) {
  final storage = ref.watch(secureStorageProvider);
  return ApiClient(storage: storage);
});
