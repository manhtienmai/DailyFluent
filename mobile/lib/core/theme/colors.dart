import 'package:flutter/material.dart';

/// DailyFluent color palette — matches the web design system.
class AppColors {
  AppColors._();

  // ── Primary ──────────────────────────────────────────────
  static const Color primary = Color(0xFF6C5CE7);
  static const Color primaryLight = Color(0xFF9B8FEF);
  static const Color primaryDark = Color(0xFF4A3DB0);

  // ── Accent ───────────────────────────────────────────────
  static const Color accent = Color(0xFF00B894);
  static const Color accentLight = Color(0xFF55EFC4);

  // ── Semantic ─────────────────────────────────────────────
  static const Color success = Color(0xFF00B894);
  static const Color warning = Color(0xFFFDAA5E);
  static const Color error = Color(0xFFFF6B6B);
  static const Color info = Color(0xFF74B9FF);

  // ── Streak ───────────────────────────────────────────────
  static const Color streakFire = Color(0xFFFF6348);
  static const Color streakGold = Color(0xFFFFD32A);

  // ── JLPT Level Colors ────────────────────────────────────
  static const Color jlptN5 = Color(0xFF74B9FF);
  static const Color jlptN4 = Color(0xFF55EFC4);
  static const Color jlptN3 = Color(0xFFFDAA5E);
  static const Color jlptN2 = Color(0xFFFF6B6B);
  static const Color jlptN1 = Color(0xFFE056A0);

  // ── Light Theme Colors ───────────────────────────────────
  static const Color lightBackground = Color(0xFFF8F9FE);
  static const Color lightSurface = Color(0xFFFFFFFF);
  static const Color lightSurfaceVariant = Color(0xFFF0F1F8);
  static const Color lightText = Color(0xFF1A1B2E);
  static const Color lightTextSecondary = Color(0xFF6B7280);
  static const Color lightTextTertiary = Color(0xFF9CA3AF);
  static const Color lightBorder = Color(0xFFE5E7EB);

  // ── Dark Theme Colors ────────────────────────────────────
  static const Color darkBackground = Color(0xFF0F0F1A);
  static const Color darkSurface = Color(0xFF1A1B2E);
  static const Color darkSurfaceVariant = Color(0xFF252640);
  static const Color darkText = Color(0xFFF1F1F6);
  static const Color darkTextSecondary = Color(0xFFA0A5B5);
  static const Color darkTextTertiary = Color(0xFF6B7280);
  static const Color darkBorder = Color(0xFF2D2E45);

  // ── Gradients ────────────────────────────────────────────
  static const LinearGradient primaryGradient = LinearGradient(
    colors: [primary, Color(0xFF8B5CF6)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static const LinearGradient accentGradient = LinearGradient(
    colors: [accent, Color(0xFF00D2A0)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static const LinearGradient warmGradient = LinearGradient(
    colors: [Color(0xFFFF6348), Color(0xFFFF9F43)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  static Color jlptColor(String level) {
    switch (level.toUpperCase()) {
      case 'N5':
        return jlptN5;
      case 'N4':
        return jlptN4;
      case 'N3':
        return jlptN3;
      case 'N2':
        return jlptN2;
      case 'N1':
        return jlptN1;
      default:
        return primary;
    }
  }
}
