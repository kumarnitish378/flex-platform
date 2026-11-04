import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_cab/data/api/ride_request_repository.dart';
import 'package:smart_cab/features/employee/live_tracking_screen.dart';
import 'package:smart_cab/features/employee/ride_history_screen.dart';
import 'package:smart_cab/features/employee/saved_places_screen.dart';
import 'package:smart_cab/features/employee/trip_completed_screen.dart';
import 'package:smart_cab/l10n/app_localizations.dart';
import 'package:smart_cab_api/smart_cab_api.dart' as api;

void main() {
  Widget buildTestableWidget(Widget child) {
    return ProviderScope(
      overrides: [
        rideRequestRepositoryProvider.overrideWithValue(_FakeRideRequestRepository()),
      ],
      child: MaterialApp(
        localizationsDelegates: AppText.localizationsDelegates,
        supportedLocales: AppText.supportedLocales,
        home: child,
      ),
    );
  }

  group('A08: Live tracking, rating, history & saved places (E-04..E-07)', () {
    testWidgets('E-04 Live Tracking renders E-04 key, map and bottom sheet', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(
        buildTestableWidget(
          const LiveTrackingScreen(
            tripId: 't_100',
            isTestMode: true,
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('E-04')), findsOneWidget);
      expect(find.byKey(const Key('tracking-map')), findsOneWidget);
      expect(find.byKey(const Key('tracking-bottom-sheet')), findsOneWidget);
      expect(find.byKey(const Key('sos-button')), findsOneWidget);
    });

    testWidgets('E-05 Trip Completed renders E-05 key and rating bar', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(
        buildTestableWidget(
          const TripCompletedScreen(tripId: 't_100'),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('E-05')), findsOneWidget);
      expect(find.byKey(const Key('rating-bar')), findsOneWidget);
      expect(find.byKey(const Key('submit-rating')), findsOneWidget);

      await tester.tap(find.byKey(const Key('submit-rating')));
      await tester.pumpAndSettle();

      expect(find.text('Rating Submitted'), findsOneWidget);
    });

    testWidgets('E-06 Ride History renders E-06 key', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(buildTestableWidget(const RideHistoryScreen()));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('E-06')), findsOneWidget);
    });

    testWidgets('E-07 Saved Places renders E-07 key and places list', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(buildTestableWidget(const SavedPlacesScreen()));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('E-07')), findsOneWidget);
      expect(find.byKey(const Key('saved-places-list')), findsOneWidget);
      expect(find.text('Home'), findsOneWidget);
      expect(find.text('Office'), findsOneWidget);
    });
  });
}

class _FakeRideRequestRepository implements RideRequestRepository {
  @override
  Future<List<api.RideRequest>> getMyRequests() async => <api.RideRequest>[];

  @override
  Future<api.RideRequest> createRequest(api.RideRequestInput input) async {
    return api.RideRequest((b) => b..id = 'r1');
  }

  @override
  Future<api.RideRequest> getRequest(String requestId) async {
    return api.RideRequest((b) => b..id = requestId);
  }

  @override
  Future<api.RideRequest> cancelRequest(String requestId, {String? reason}) async {
    return api.RideRequest((b) => b..id = requestId);
  }
}
