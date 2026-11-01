import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_cab/features/auth/login_screen.dart';
import 'package:smart_cab/l10n/app_localizations.dart';

void main() {
  Widget buildTestableWidget(Widget child) {
    return ProviderScope(
      child: MaterialApp(
        localizationsDelegates: AppText.localizationsDelegates,
        supportedLocales: AppText.supportedLocales,
        home: child,
      ),
    );
  }

  group('Item 1: APP_TESTING login flag tests', () {
    testWidgets('APP_TESTING = false shows standard OTP flow without TEST MODE banner', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(
        buildTestableWidget(const LoginScreen(isAppTesting: false)),
      );
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('test-mode-banner')), findsNothing);
      expect(find.byKey(const Key('send-code')), findsOneWidget);
      expect(find.byKey(const Key('test-sign-in-button')), findsNothing);
    });

    testWidgets('APP_TESTING = true shows TEST MODE banner and single-step Test Sign In button', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(
        buildTestableWidget(const LoginScreen(isAppTesting: true)),
      );
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('test-mode-banner')), findsOneWidget);
      expect(find.byKey(const Key('test-sign-in-button')), findsOneWidget);
      expect(find.byKey(const Key('send-code')), findsNothing);
    });
  });
}
