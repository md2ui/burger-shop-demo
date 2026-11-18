// The Burger Shop palette, the same as backend/md2ui_theme/THEME.md and the web app, so
// the native header, footer and sheets match what md2ui draws between them.

import 'package:flutter/material.dart';

abstract final class Palette {
  static const forest = Color(0xFF2D4E3A); // the brand: big buttons, the band, Limited / Chef's Pick
  static const forestDark = Color(0xFF223D2D); // a pressed forest button
  static const mustard = Color(0xFFE69F35); // New, stars, the success badge
  static const orange = Color(0xFFFF642D); // Offer, a liked heart
  static const root = Color(0xFFF2FCD9); // the page
  static const cream = Color(0xFFF9F3EB); // (249, 243, 235) quiet buttons and fields
  static const ink = Color(0xFF1C2B22); // titles and prices
  static const body = Color(0xFF4A5A50);
  static const muted = Color(0xFF7A887E);
  static const border = Color(0xFFE3EBD3);
  static const white = Color(0xFFFFFFFF);
  static const mustardTint = Color(0xFFFBEBD0);
  static const mustardInk = Color(0xFF8A5410);
  static const error = Color(0xFFA8361A);
}

abstract final class Fonts {
  static const heading = 'Plus Jakarta Sans';
  static const text = 'Inter';
}

ThemeData burgerTheme() {
  final scheme = ColorScheme.fromSeed(
    seedColor: Palette.forest,
    primary: Palette.forest,
    onPrimary: Palette.white,
    secondary: Palette.mustard,
    tertiary: Palette.orange,
    surface: Palette.white,
    onSurface: Palette.ink,
    error: Palette.error,
  );
  final text = ThemeData.light().textTheme.apply(fontFamily: Fonts.text, bodyColor: Palette.body, displayColor: Palette.ink);
  const pill = StadiumBorder();
  return ThemeData(
    useMaterial3: true,
    colorScheme: scheme,
    scaffoldBackgroundColor: Palette.root,
    fontFamily: Fonts.text,
    textTheme: text.copyWith(
      titleLarge: text.titleLarge?.copyWith(fontFamily: Fonts.heading, fontWeight: FontWeight.w800, color: Palette.ink),
      titleMedium: text.titleMedium?.copyWith(fontFamily: Fonts.heading, fontWeight: FontWeight.w700, color: Palette.ink),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: Palette.forest,
        foregroundColor: Palette.white,
        disabledBackgroundColor: Palette.forest.withValues(alpha: 0.35),
        disabledForegroundColor: Palette.white,
        minimumSize: const Size(0, 48),
        padding: const EdgeInsets.symmetric(horizontal: 22),
        shape: pill,
        textStyle: const TextStyle(fontFamily: Fonts.heading, fontWeight: FontWeight.w700, fontSize: 15),
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: Palette.forest,
        minimumSize: const Size(0, 48),
        padding: const EdgeInsets.symmetric(horizontal: 20),
        side: const BorderSide(color: Palette.forest, width: 1.5),
        shape: pill,
        textStyle: const TextStyle(fontFamily: Fonts.heading, fontWeight: FontWeight.w700, fontSize: 15),
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: Palette.cream,
      hintStyle: const TextStyle(color: Palette.muted, fontSize: 14),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(999), borderSide: const BorderSide(color: Palette.border)),
      enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(999), borderSide: const BorderSide(color: Palette.border)),
      focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(999), borderSide: const BorderSide(color: Palette.forest, width: 2)),
    ),
    snackBarTheme: const SnackBarThemeData(
      behavior: SnackBarBehavior.floating,
      backgroundColor: Palette.ink,
      contentTextStyle: TextStyle(fontFamily: Fonts.text, color: Palette.white),
    ),
  );
}
