import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_cab/data/api/driver_trips_repository.dart';
import 'package:smart_cab/features/driver/navigation_map_screen.dart';
import 'package:smart_cab/features/driver/report_issue_screen.dart';
import 'package:smart_cab/features/driver/trip_detail_screen.dart';
import 'package:smart_cab/features/driver/trip_list_screen.dart';
import 'package:smart_cab/l10n/app_localizations.dart';
import 'package:smart_cab_api/smart_cab_api.dart' as api;

void main() {
  late _FakeDriverTripsRepository fakeRepo;

  setUp(() {
    fakeRepo = _FakeDriverTripsRepository();
  });

  Widget buildTestableWidget(Widget child) {
    return ProviderScope(
      overrides: [
        driverTripsRepositoryProvider.overrideWithValue(fakeRepo),
      ],
      child: MaterialApp(
        localizationsDelegates: AppText.localizationsDelegates,
        supportedLocales: AppText.supportedLocales,
        home: child,
      ),
    );
  }

  group('A10: Driver trip & navigation screens (D-03..D-06)', () {
    testWidgets('D-03 Trip List renders D-03 key', (WidgetTester tester) async {
      await tester.pumpWidget(buildTestableWidget(const TripListScreen()));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('D-03')), findsOneWidget);
    });

    testWidgets('D-04 Trip Detail renders D-04 key and trip info', (
      WidgetTester tester,
    ) async {
      fakeRepo.tripToReturn = api.Trip(
        (api.TripBuilder b) => b
          ..id = 't_test_100'
          ..status = api.TripStatus.dispatched,
      );

      await tester.pumpWidget(
        buildTestableWidget(
          const TripDetailScreen(tripId: 't_test_100'),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('D-04')), findsOneWidget);
    });

    testWidgets('D-05 Navigation Map renders D-05 key and external nav CTA', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(
        buildTestableWidget(
          const NavigationMapScreen(
            tripId: 't_test_100',
            isTestMode: true,
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('D-05')), findsOneWidget);
      expect(find.byKey(const Key('navigation-map')), findsOneWidget);
      expect(find.byKey(const Key('open-external-nav')), findsOneWidget);
    });

    testWidgets('D-06 Report Issue renders D-06 key, picker and submit', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(buildTestableWidget(const ReportIssueScreen()));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('D-06')), findsOneWidget);
      expect(find.byKey(const Key('issue-type-picker')), findsOneWidget);
      expect(find.byKey(const Key('issue-note-input')), findsOneWidget);
      expect(find.byKey(const Key('submit-issue')), findsOneWidget);
    });
  });
}

class _FakeDriverTripsRepository implements DriverTripsRepository {
  api.Trip? tripToReturn;

  @override
  Future<List<api.Trip>> getTrips() async => <api.Trip>[];

  @override
  Future<api.Trip> getTripDetail(String tripId) async {
    return tripToReturn ??
        api.Trip(
          (api.TripBuilder b) => b
            ..id = tripId
            ..status = api.TripStatus.dispatched,
        );
  }

  @override
  Future<api.Trip> startTrip(String tripId) async {
    return api.Trip(
      (api.TripBuilder b) => b
        ..id = tripId
        ..status = api.TripStatus.inProgress,
    );
  }

  @override
  Future<void> reportIssue({required String issueType, String? note}) async {}
}
