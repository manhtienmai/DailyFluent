import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../features/auth/domain/models.dart';
import '../../features/auth/presentation/login_screen.dart';
import '../../features/auth/presentation/signup_screen.dart';
import '../../features/auth/providers.dart';
import '../../features/home/presentation/home_screen.dart';
import '../../features/home/presentation/main_shell.dart';
import '../../features/home/presentation/learn_hub_screen.dart';
import '../../features/home/presentation/exam_hub_screen.dart';
import '../../features/home/presentation/progress_screen.dart';
import '../../features/home/presentation/account_screen.dart';
import '../../features/kanji/presentation/kanji_screens.dart';
import '../../features/vocab/presentation/vocab_screens.dart';
import '../../features/grammar/presentation/grammar_screens.dart';
import '../../features/exam/presentation/exam_screens.dart';
import '../../features/exam/providers.dart';
import '../../features/streak/presentation/streak_screens.dart';
import '../../features/video/presentation/video_screens.dart';
import '../../features/placement/presentation/placement_screens.dart';
import '../../features/shop/presentation/shop_screens.dart';
import '../../shared/widgets/splash_screen.dart';

/// A [ChangeNotifier] that bridges Riverpod's auth state to GoRouter's
/// refreshListenable so the router can react to auth changes without
/// being fully recreated.
class _AuthRefreshNotifier extends ChangeNotifier {
  _AuthRefreshNotifier(Ref ref) {
    ref.listen<AuthState>(authProvider, (_, __) => notifyListeners());
  }
}

final routerProvider = Provider<GoRouter>((ref) {
  final refreshNotifier = _AuthRefreshNotifier(ref);

  return GoRouter(
    initialLocation: '/',
    debugLogDiagnostics: false,
    refreshListenable: refreshNotifier,
    redirect: (context, state) {
      final authState = ref.read(authProvider);
      final isAuthenticated = authState is AuthAuthenticated;
      final isLoading = authState is AuthInitial || authState is AuthLoading;
      final path = state.matchedLocation;
      final isOnAuth = path == '/login' || path == '/signup';

      // Still loading → show splash (stay on /)
      if (isLoading) {
        return isOnAuth ? null : '/';
      }

      // Not authenticated → redirect to login
      if (!isAuthenticated && !isOnAuth) return '/login';

      // Authenticated but on auth page → go home
      if (isAuthenticated && isOnAuth) return '/';

      return null;
    },
    routes: [
      // ── Auth routes ──────────────────────────────────────
      GoRoute(
        path: '/login',
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: '/signup',
        builder: (context, state) => const SignupScreen(),
      ),

      // ── Main app shell with bottom nav ───────────────────
      StatefulShellRoute.indexedStack(
        builder: (context, state, navigationShell) {
          return MainShell(navigationShell: navigationShell);
        },
        branches: [
          // Tab 0: Home
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/',
                builder: (context, state) {
                  final authState = ref.read(authProvider);
                  if (authState is AuthInitial || authState is AuthLoading) {
                    return const SplashScreen();
                  }
                  return const HomeScreen();
                },
              ),
            ],
          ),

          // Tab 1: Learn Hub
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/learn',
                builder: (context, state) => const LearnHubScreen(),
                routes: [
                  GoRoute(
                    path: 'kanji',
                    builder: (context, state) =>
                        const KanjiLevelListScreen(),
                  ),
                  GoRoute(
                    path: 'vocab',
                    builder: (context, state) =>
                        const VocabCoursesScreen(),
                  ),
                  GoRoute(
                    path: 'flashcards',
                    builder: (context, state) =>
                        const FlashcardReviewScreen(),
                  ),
                  GoRoute(
                    path: 'grammar',
                    builder: (context, state) =>
                        const GrammarListScreen(),
                  ),
                  GoRoute(
                    path: 'videos',
                    builder: (context, state) =>
                        const VideoListScreen(),
                  ),
                  GoRoute(
                    path: 'ebooks',
                    builder: (context, state) =>
                        const EbookListScreen(),
                  ),
                  GoRoute(
                    path: 'placement',
                    builder: (context, state) =>
                        const PlacementIntroScreen(),
                  ),
                ],
              ),
            ],
          ),

          // Tab 2: Exam Hub
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/exam',
                builder: (context, state) => const ExamHubScreen(),
                routes: [
                  GoRoute(
                    path: 'toeic',
                    builder: (context, state) => ExamListScreen(
                      title: 'TOEIC',
                      provider: examToeicListProvider,
                    ),
                  ),
                ],
              ),
            ],
          ),

          // Tab 3: Progress
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/progress',
                builder: (context, state) => const ProgressScreen(),
                routes: [
                  GoRoute(
                    path: 'heatmap',
                    builder: (context, state) => const HeatmapScreen(),
                  ),
                  GoRoute(
                    path: 'leaderboard',
                    builder: (context, state) =>
                        const LeaderboardScreen(),
                  ),
                ],
              ),
            ],
          ),

          // Tab 4: Account
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/account',
                builder: (context, state) => const AccountScreen(),
                routes: [
                  GoRoute(
                    path: 'wallet',
                    builder: (context, state) => const WalletScreen(),
                  ),
                  GoRoute(
                    path: 'shop',
                    builder: (context, state) => const ShopScreen(),
                  ),
                  GoRoute(
                    path: 'notifications',
                    builder: (context, state) =>
                        const NotificationsScreen(),
                  ),
                  GoRoute(
                    path: 'feedback',
                    builder: (context, state) =>
                        const FeedbackScreen(),
                  ),
                ],
              ),
            ],
          ),
        ],
      ),
    ],
  );
});
