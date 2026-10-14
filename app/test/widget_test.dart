import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_cab/core/session.dart';
import 'package:smart_cab/core/session_controller.dart';
import 'package:smart_cab/core/token_store.dart';
import 'package:smart_cab/main.dart';

/// The app starts, shows the splash, and sends a signed-out person to login (A01).
void main() {
  testWidgets('a cold start shows the splash', (WidgetTester tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          tokenStoreProvider.overrideWithValue(_InMemoryTokenStore()),
        ],
        child: const SmartCabApp(),
      ),
    );

    expect(find.byKey(const Key('C-01')), findsOneWidget);
    expect(find.text('Smart Cab'), findsOneWidget);
  });

  testWidgets('a signed-out person lands at login, not at a role home', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          tokenStoreProvider.overrideWithValue(_InMemoryTokenStore()),
        ],
        child: const SmartCabApp(),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('C-02')), findsOneWidget);
    expect(find.byKey(const Key('home-employee')), findsNothing);
  });

  testWidgets('a signed-in driver lands on the driver home', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          sessionProvider.overrideWith(_FakeSession.new),
          tokenStoreProvider.overrideWithValue(_InMemoryTokenStore()),
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
          tokenStoreProvider.overrideWithValue(_InMemoryTokenStore()),
        ],
        child: const SmartCabApp(),
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('sign-out')));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('C-02')), findsOneWidget);
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

class _InMemoryTokenStore implements TokenStore {
  StoredSession? _session;

  @override
  Future<StoredSession?> read() async => _session;

  @override
  Future<void> write(StoredSession session) async {
    _session = session;
  }

  @override
  Future<void> clear() async {
    _session = null;
  }
}
