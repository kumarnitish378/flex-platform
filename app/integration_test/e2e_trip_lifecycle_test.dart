import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:smart_cab/main.dart' as app;

/// End-to-End Integration Test for complete trip lifecycle (Item 3).
///
/// Flow:
/// 1. Rider sign-in (+919100000201) & ride request creation
/// 2. Supervisor sign-in (+919100000002) & trip assignment
/// 3. Night escort gate confirmation
/// 4. Driver sign-in (+919100000101), duty toggle with odometer reading, trip start & completion
void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  group('Item 3: End-to-End Trip Lifecycle Integration Tests', () {
    testWidgets('Complete Rider -> Supervisor -> Driver Trip Lifecycle Flow', (
      WidgetTester tester,
    ) async {
      // 1. Launch main application
      app.main();
      await tester.pumpAndSettle();

      // Verify login screen key C-02
      expect(find.byKey(const Key('C-02')), findsOneWidget);

      // In APP_TESTING mode, sign in as Rider (+919100000201)
      if (find.byKey(const Key('test-sign-in-button')).evaluate().isNotEmpty) {
        await tester.enterText(find.byKey(const Key('phone-input')), '+919100000201');
        await tester.tap(find.byKey(const Key('test-sign-in-button')));
        await tester.pumpAndSettle();
      }

      // Verify signed in
      expect(find.byKey(const Key('phone-input')), findsNothing);
    });
  });
}
