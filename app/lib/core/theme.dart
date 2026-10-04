import 'package:flutter/material.dart';

/// One theme for every role (A01).
///
/// `screens-by-role.md` "Layout rules" asks for large tap targets and high contrast:
/// this is used one-handed, outdoors, often in sunlight, sometimes by a driver who
/// should be looking at the road. That is a product requirement, not a style
/// preference, so the sizes live here rather than being chosen per screen.
class AppTheme {
  const AppTheme._();

  /// Minimum tap target. Material's default is 48; a driver tapping "Arrived" while
  /// parked in traffic gets more room than that.
  static const double minTapTarget = 56;

  /// Enough contrast to read in direct sun, which rules out a light grey on white.
  static const Color _seed = Color(0xFF0B5FFF);

  static ThemeData light() => _build(Brightness.light);

  static ThemeData dark() => _build(Brightness.dark);

  static ThemeData _build(Brightness brightness) {
    final ColorScheme scheme = ColorScheme.fromSeed(
      seedColor: _seed,
      brightness: brightness,
    );
    return ThemeData(
      colorScheme: scheme,
      useMaterial3: true,
      visualDensity: VisualDensity.standard,
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          minimumSize: const Size.fromHeight(minTapTarget),
          textStyle: const TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          minimumSize: const Size.fromHeight(minTapTarget),
        ),
      ),
      snackBarTheme: const SnackBarThemeData(behavior: SnackBarBehavior.floating),
    );
  }
}
