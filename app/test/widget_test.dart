import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_cab/core/session.dart';
import 'package:smart_cab/main.dart';

/// The app starts, shows the splash, and sends a signed-out person to login (A01).
void main() {
  testWidgets('a cold start shows the splash', (WidgetTester tester) async {
    await tester.pumpWidget(const ProviderScope(child: SmartCabApp()));

    expect(find.byKey(const Key('splash')), findsOneWidget);
    expect(find.text('Smart Cab'), findsOneWidget);
  });

  testWidgets('a signed-out person lands at login, not at a role home', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(const ProviderScope(child: SmartCabApp()));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('login')), findsOneWidget);
    expect(find.byKey(const Key('home-employee')), findsNothing);
  });

  testWidgets('a signed-in driver lands on the driver home', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          sessionProvider.overrideWith(_FakeSession.new),
        ],
        child: const SmartCabApp(),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('home-driver')), findsOneWidget);
    // One role only, so there is nothing to switch to and no switcher.
    expect(find.byKey(const Key('switch-role')), findsNothing);
  });

  testWidgets('signing out returns to login', (WidgetTester tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          sessionProvider.overrideWith(_FakeSession.new),
        ],
        child: const SmartCabApp(),
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('sign-out')));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('login')), findsOneWidget);
  });
}

/// A driver who is already signed in. No HTTP: A03 brings the real thing.
class _FakeSession extends SessionNotifier {
  @override
  Session build() => const Session(
    roles: <Role>[Role.driver],
    activeRole: Role.driver,
    accessToken: 'test-token',
    userId: 'test-user',
  );
}
