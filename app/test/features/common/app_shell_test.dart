import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_cab/core/router.dart';
import 'package:smart_cab/core/screens.dart';
import 'package:smart_cab/core/session.dart';
import 'package:smart_cab/core/session_controller.dart';
import 'package:smart_cab/core/token_store.dart';
import 'package:smart_cab/main.dart';

/// Role-based navigation, per role (A04).
///
/// The acceptance criterion is "each role sees only its screens, and an unauthorised
/// deep link redirects", so these tests sign in as each of the five roles in turn and
/// assert both halves. The second half is the one worth having: a deep link is how a
/// push notification, an `adb` intent, or a link in a WhatsApp message arrives, and
/// none of those ask the app first whether the person is allowed.
void main() {
  /// Every role that a person can actually be in the field. `platform_admin` is us and
  /// shares the operator admin screens, which `screens_test.dart` asserts separately.
  const List<Role> fieldRoles = <Role>[
    Role.employee,
    Role.driver,
    Role.supervisor,
    Role.operatorAdmin,
    Role.clientAdmin,
  ];

  for (final Role role in fieldRoles) {
    testWidgets('a ${role.wireName} sees its own tabs and nobody else\'s', (
      WidgetTester tester,
    ) async {
      await _pumpAs(tester, role);

      expect(
        find.byKey(Key('shell-${role.wireName}')),
        findsOneWidget,
        reason: 'the shell should know which role it is rendering',
      );

      for (final AppScreen screen in primaryDestinations[role]!) {
        expect(
          find.byKey(Key('nav-${screen.id}')),
          findsOneWidget,
          reason: '${role.wireName} should be offered ${screen.id}',
        );
      }

      // Every tab belonging to any other role must be absent, which is the whole of
      // "each role sees only its screens" stated as a test rather than by inspection.
      final Set<AppScreen> mine = destinationsFor(role).toSet();
      for (final Role other in Role.values) {
        if (other == role) {
          continue;
        }
        for (final AppScreen screen in primaryDestinations[other]!) {
          if (mine.contains(screen)) {
            continue;
          }
          expect(
            find.byKey(Key('nav-${screen.id}')),
            findsNothing,
            reason: '${role.wireName} must not be offered ${screen.id}, which belongs '
                'to ${other.wireName}',
          );
        }
      }
    });

    testWidgets('a ${role.wireName} lands on their own home', (
      WidgetTester tester,
    ) async {
      await _pumpAs(tester, role);
      final AppScreen home = primaryDestinations[role]!.first;
      expect(find.byKey(Key(home.id)), findsOneWidget);
    });
  }

  group('an unauthorised deep link redirects home', () {
    testWidgets('a driver sent to the admin screens ends up on duty', (
      WidgetTester tester,
    ) async {
      final ProviderContainer container = await _pumpAs(tester, Role.driver);

      container.read(routerProvider).go(AppScreen.adminVehicles.path);
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('A-02')), findsNothing);
      expect(find.byKey(const Key('D-01')), findsOneWidget);
    });

    testWidgets('an employee sent to the dispatch board ends up at home', (
      WidgetTester tester,
    ) async {
      final ProviderContainer container = await _pumpAs(tester, Role.employee);

      container.read(routerProvider).go(AppScreen.pendingQueue.path);
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('S-02')), findsNothing);
      expect(find.byKey(const Key('E-01')), findsOneWidget);
    });

    testWidgets('a client admin cannot deep-link into a detail screen either', (
      WidgetTester tester,
    ) async {
      // The gate is on the prefix, so a parameterised path has to be covered too - it
      // is the easiest one to forget, because it has no tab anywhere.
      final ProviderContainer container = await _pumpAs(tester, Role.clientAdmin);

      container.read(routerProvider).go('/driver/trips/some-trip-id');
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('D-04')), findsNothing);
      expect(find.byKey(const Key('L-01')), findsOneWidget);
    });

    testWidgets('a supervisor sent to the admin screens ends up on the board', (
      WidgetTester tester,
    ) async {
      // The permission matrix denies a supervisor vehicles, clients, users and zones,
      // so the dispatcher who can work the board still cannot manage the fleet.
      final ProviderContainer container = await _pumpAs(tester, Role.supervisor);

      container.read(routerProvider).go(AppScreen.adminDashboard.path);
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('A-01')), findsNothing);
      expect(find.byKey(const Key('S-01')), findsOneWidget);
    });

    testWidgets('an operator admin may open the dispatch board', (
      WidgetTester tester,
    ) async {
      final ProviderContainer container = await _pumpAs(tester, Role.operatorAdmin);

      container.read(routerProvider).go(AppScreen.dispatchMap.path);
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('S-01')), findsOneWidget);
    });

    testWidgets('a supervisor may deep-link into their own assign panel', (
      WidgetTester tester,
    ) async {
      // The mirror of the tests above: the gate has to let the right role through, or
      // every notification tap would bounce to the board.
      final ProviderContainer container = await _pumpAs(tester, Role.supervisor);

      container.read(routerProvider).go('/supervisor/queue/some-request-id');
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('S-03')), findsOneWidget);
    });
  });

  group('navigating', () {
    testWidgets('tapping a tab opens that screen', (WidgetTester tester) async {
      await _pumpAs(tester, Role.employee);

      await tester.tap(find.byKey(const Key('nav-E-06')));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('E-06')), findsOneWidget);
      expect(find.byKey(const Key('E-01')), findsNothing);
    });

    testWidgets('"More" opens the screens without a tab', (
      WidgetTester tester,
    ) async {
      await _pumpAs(tester, Role.operatorAdmin);

      await tester.tap(find.byKey(const Key('nav-more')));
      await tester.pumpAndSettle();

      // A-08 settings has no tab of its own; an operator admin still has to reach it.
      expect(find.byKey(const Key('more-A-08')), findsOneWidget);
      await tester.tap(find.byKey(const Key('more-A-08')));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('A-08')), findsOneWidget);
    });

    testWidgets('a role is never offered a "More" entry it cannot open', (
      WidgetTester tester,
    ) async {
      await _pumpAs(tester, Role.driver);

      await tester.tap(find.byKey(const Key('nav-more')));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('more-D-06')), findsOneWidget);
      expect(find.byKey(const Key('more-A-08')), findsNothing);
      expect(find.byKey(const Key('more-S-02')), findsNothing);
    });

    testWidgets('a detail screen gets a back arrow, not a navigation bar', (
      WidgetTester tester,
    ) async {
      final ProviderContainer container = await _pumpAs(tester, Role.employee);

      container.read(routerProvider).go('/employee/request');
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('E-02')), findsOneWidget);
      expect(
        find.byKey(const Key('nav-bar-employee')),
        findsNothing,
        reason: 'a bottom bar on a half-filled form invites a tap that abandons it',
      );
    });
  });

  group('a wide screen', () {
    testWidgets('puts the destinations in a rail, with no "More" to open', (
      WidgetTester tester,
    ) async {
      tester.view.physicalSize = const Size(1600, 1200);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.reset);

      await _pumpAs(tester, Role.operatorAdmin);

      expect(find.byKey(const Key('nav-rail-operator_admin')), findsOneWidget);
      expect(find.byKey(const Key('nav-bar-operator_admin')), findsNothing);
      // The rail has room for all seven admin screens, so nothing hides behind "More".
      expect(find.byKey(const Key('nav-more')), findsNothing);
      expect(find.byKey(const Key('nav-A-08')), findsOneWidget);
    });
  });

  group('switching role', () {
    testWidgets('changes the navigation, not just the home screen', (
      WidgetTester tester,
    ) async {
      // The reason there is one shell rather than five: a person who holds both roles
      // switches mid-session, and the tabs have to follow.
      final ProviderContainer container = ProviderContainer(
        overrides: [
          sessionProvider.overrideWith(_FakeSession.new),
          tokenStoreProvider.overrideWithValue(_InMemoryTokenStore()),
        ],
      );
      addTearDown(container.dispose);

      await tester.pumpWidget(
        UncontrolledProviderScope(container: container, child: const SmartCabApp()),
      );
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('nav-S-01')), findsOneWidget);

      container.read(sessionProvider.notifier).switchTo(Role.employee);
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('shell-employee')), findsOneWidget);
      expect(find.byKey(const Key('nav-E-01')), findsOneWidget);
      expect(find.byKey(const Key('nav-S-01')), findsNothing);
      expect(find.byKey(const Key('E-01')), findsOneWidget);
    });

    testWidgets('the switcher is offered only to someone holding two roles', (
      WidgetTester tester,
    ) async {
      await _pumpAs(tester, Role.supervisor);
      expect(find.byKey(const Key('switch-role')), findsNothing);
    });
  });
}

/// Pumps the app signed in as one role, and hands back the container so a test can
/// drive the router the way a deep link would.
Future<ProviderContainer> _pumpAs(WidgetTester tester, Role role) async {
  final ProviderContainer container = ProviderContainer(
    overrides: [
      sessionProvider.overrideWith(() => _SingleRoleSession(role)),
      tokenStoreProvider.overrideWithValue(_InMemoryTokenStore()),
    ],
  );
  addTearDown(container.dispose);

  await tester.pumpWidget(
    UncontrolledProviderScope(container: container, child: const SmartCabApp()),
  );
  await tester.pumpAndSettle();
  return container;
}

/// Signed in holding exactly one role. No HTTP: the session is the thing under test
/// here, not how it was obtained.
class _SingleRoleSession extends SessionNotifier {
  _SingleRoleSession(this.role);

  final Role role;

  @override
  Session build() => Session(
    roles: <Role>[role],
    activeRole: role,
    accessToken: 'test-token',
    userId: 'test-user',
  );
}

/// A supervisor who also rides to work - the case the role switcher exists for.
class _FakeSession extends SessionNotifier {
  @override
  Session build() => const Session(
    roles: <Role>[Role.supervisor, Role.employee],
    activeRole: Role.supervisor,
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
