import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_cab/data/api/driver_duty_repository.dart';
import 'package:smart_cab/features/driver/duty_home_screen.dart';
import 'package:smart_cab/features/driver/offline_banner.dart';
import 'package:smart_cab/features/driver/permission_explainer_screen.dart';
import 'package:smart_cab/l10n/app_localizations.dart';
import 'package:smart_cab_api/smart_cab_api.dart' as api;

void main() {
  Widget buildTestableWidget(Widget child) {
    return ProviderScope(
      overrides: [
        driverDutyRepositoryProvider.overrideWithValue(_FakeDriverDutyRepository()),
      ],
      child: MaterialApp(
        localizationsDelegates: AppText.localizationsDelegates,
        supportedLocales: AppText.supportedLocales,
        home: child,
      ),
    );
  }

  group('A09: Driver duty & permission screens (D-01, D-02, D-07)', () {
    testWidgets('D-01 Duty Home renders D-01 key, duty switch, and GPS status', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(buildTestableWidget(const DutyHomeScreen()));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('D-01')), findsOneWidget);
      expect(find.byKey(const Key('duty-switch')), findsOneWidget);
      expect(find.byKey(const Key('gps-status')), findsOneWidget);
      expect(find.text('OFF DUTY'), findsOneWidget);

      await tester.tap(find.byKey(const Key('duty-switch')));
      await tester.pumpAndSettle();

      expect(find.text('ON DUTY'), findsOneWidget);
    });

    testWidgets('D-02 Permission Explainer renders D-02 key and request button', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(buildTestableWidget(const PermissionExplainerScreen()));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('D-02')), findsOneWidget);
      expect(find.byKey(const Key('request-location-permission')), findsOneWidget);
    });

    testWidgets('D-07 Offline Banner renders D-07 key and queued count', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(
        buildTestableWidget(
          const OfflineBanner(queuedCount: 5),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('D-07')), findsOneWidget);
      expect(find.byKey(const Key('offline-banner')), findsOneWidget);
      expect(find.text('Offline • 5 events queued for sync'), findsOneWidget);
    });
  });
}

class _FakeDriverDutyRepository implements DriverDutyRepository {
  @override
  Future<api.DutyState> setDutyStatus({
    required bool onDuty,
    String? vehicleId,
  }) async {
    return api.DutyState(
      (api.DutyStateBuilder b) => b
        ..onDuty = onDuty
        ..vehicleId = vehicleId ?? 'v1',
    );
  }
}
