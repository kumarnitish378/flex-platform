import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_cab/features/driver/permission_explainer_screen.dart';

void main() {
  group('Item 2: Permission flow step-by-step tests', () {
    testWidgets('PermissionExplainerScreen steps through location and notification prompts', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(
        const MaterialApp(home: PermissionExplainerScreen()),
      );
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('D-02')), findsOneWidget);
      expect(find.textContaining('1. Location Access'), findsOneWidget);

      // Advance to Step 2
      await tester.tap(find.byKey(const Key('request-location-permission')));
      await tester.pumpAndSettle();

      expect(find.textContaining('2. Background Location'), findsOneWidget);

      // Advance to Step 3
      await tester.tap(find.byKey(const Key('request-location-permission')));
      await tester.pumpAndSettle();

      expect(find.textContaining('3. Notification Permission'), findsOneWidget);
    });

    testWidgets('PermissionExplainerScreen renders denied/revoked card gracefully without locking app', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(
        const MaterialApp(home: PermissionExplainerScreen()),
      );
      await tester.pumpAndSettle();

      await tester.tap(find.byKey(const Key('simulate-denied-button')));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('permission-denied-card')), findsOneWidget);
      expect(find.byKey(const Key('open-settings-button')), findsOneWidget);

      await tester.tap(find.byKey(const Key('open-settings-button')));
      await tester.pumpAndSettle();

      expect(find.textContaining('2. Background Location'), findsOneWidget);
    });
  });
}
