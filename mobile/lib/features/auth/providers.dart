import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_client.dart';
import 'data/auth_repository.dart';
import 'domain/models.dart';

/// Auth repository provider.
final authRepositoryProvider = Provider<AuthRepository>((ref) {
  final api = ref.watch(apiClientProvider);
  final storage = ref.watch(secureStorageProvider);
  return AuthRepository(api: api, storage: storage);
});

/// Auth state notifier provider.
final authProvider =
    StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  final repo = ref.watch(authRepositoryProvider);
  return AuthNotifier(repo);
});

class AuthNotifier extends StateNotifier<AuthState> {
  final AuthRepository _repo;

  AuthNotifier(this._repo) : super(const AuthInitial()) {
    _init();
  }

  Future<void> _init() async {
    state = const AuthLoading();
    try {
      final user = await _repo.restoreSession();
      if (user != null) {
        state = AuthAuthenticated(user);
      } else {
        state = const AuthUnauthenticated();
      }
    } catch (e) {
      state = const AuthUnauthenticated();
    }
  }

  Future<void> login({
    required String email,
    required String password,
  }) async {
    state = const AuthLoading();
    try {
      final user = await _repo.login(email: email, password: password);
      state = AuthAuthenticated(user);
    } catch (e) {
      state = AuthError(_extractMessage(e));
    }
  }

  Future<void> signup({
    required String email,
    required String password1,
    required String password2,
  }) async {
    state = const AuthLoading();
    try {
      final user = await _repo.signup(
        email: email,
        password1: password1,
        password2: password2,
      );
      state = AuthAuthenticated(user);
    } catch (e) {
      state = AuthError(_extractMessage(e));
    }
  }

  Future<void> logout() async {
    await _repo.logout();
    state = const AuthUnauthenticated();
  }

  String _extractMessage(dynamic error) {
    if (error is Exception) {
      return error.toString().replaceFirst('Exception: ', '');
    }
    return 'Đã xảy ra lỗi. Vui lòng thử lại.';
  }
}

/// Convenience provider: true when authenticated.
final isAuthenticatedProvider = Provider<bool>((ref) {
  return ref.watch(authProvider) is AuthAuthenticated;
});

/// Convenience provider: current user (nullable).
final currentUserProvider = Provider<User?>((ref) {
  final state = ref.watch(authProvider);
  if (state is AuthAuthenticated) return state.user;
  return null;
});
