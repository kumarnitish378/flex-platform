import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_cab/core/session.dart';
import 'package:smart_cab/core/session_controller.dart';
import 'package:smart_cab/core/token_store.dart';
import 'package:smart_cab/features/common/role_switcher.dart';
import 'package:smart_cab/l10n/app_localizations.dart';

void main() {
  testWidgets('renders C-03 modal with all user roles and active checkmark', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          sessionProvider.overrideWith(_FakeMultiRoleSession.new),
          tokenStoreProvider.overrideWithValue(_FakeTokenStore()),
        ],
        child: MaterialApp(
          localizationsDelegates: AppText.localizationsDelegates,
          supportedLocales: AppText.supportedLocales,
          home: Scaffold(
            body: Builder(
              builder: (BuildContext context) => ElevatedButton(
                key: const Key('open-switcher'),
                onPressed: () => RoleSwitcherModal.show(context),
                child: const Text('Open'),
              ),
            ),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('open-switcher')));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('C-03')), findsOneWidget);
    expect(find.text('Employee'), findsOneWidget);
    expect(find.text('Supervisor'), findsOneWidget);
    expect(find.byKey(const Key('role-option-employee')), findsOneWidget);
    expect(find.byKey(const Key('role-option-supervisor')), findsOneWidget);
  });

  testWidgets('tapping a role switches active role', (WidgetTester tester) async {
    late WidgetRef testRef;

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          sessionProvider.overrideWith(_FakeMultiRoleSession.new),
          tokenStoreProvider.overrideWithValue(_FakeTokenStore()),
        ],
        child: MaterialApp(
          localizationsDelegates: AppText.localizationsDelegates,
          supportedLocales: AppText.supportedLocales,
          home: Scaffold(
            body: Consumer(
              builder: (BuildContext context, WidgetRef ref, _) {
                testRef = ref;
                return ElevatedButton(
                  key: const Key('open-switcher'),
                  onPressed: () => RoleSwitcherModal.show(context),
                  child: const Text('Open'),
                );
              },
            ),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(testRef.read(sessionProvider).activeRole, Role.employee);

    await tester.tap(find.byKey(const Key('open-switcher')));
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('role-option-supervisor')));
    await tester.pumpAndSettle();

    expect(testRef.read(sessionProvider).activeRole, Role.supervisor);
    expect(find.byKey(const Key('C-03')), findsNothing);
  });
}

class _FakeMultiRoleSession extends SessionNotifier {
  @override
  Session build() => const Session(
        roles: <Role>[Role.employee, Role.supervisor],
        activeRole: Role.employee,
        accessToken: 'test-token',
        userId: 'test-user',
      );
}

class _FakeTokenStore implements TokenStore {
  StoredSession? session;

  @override
  Future<StoredSession?> read() async => session;

  @override
  Future<void> write(StoredSession session) async {
    this.session = session;
  }

  @override
  Future<void> clear() async {
    session = null;
  }
}
