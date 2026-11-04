import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_cab/data/api/ride_request_repository.dart';
import 'package:smart_cab/features/employee/employee_home_screen.dart';
import 'package:smart_cab/features/employee/request_form_screen.dart';
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

  group('Item 3: Riders never pay (No fare/charge displayed on employee screens)', () {
    testWidgets('Employee Home renders no fare or price', (WidgetTester tester) async {
      await tester.pumpWidget(buildTestableWidget(const EmployeeHomeScreen()));
      await tester.pumpAndSettle();

      expect(find.textContaining('₹'), findsNothing);
      expect(find.textContaining('Fare'), findsNothing);
      expect(find.textContaining('Price'), findsNothing);
      expect(find.textContaining('Charge'), findsNothing);
    });

    testWidgets('Request Form renders no fare or price', (WidgetTester tester) async {
      await tester.pumpWidget(
        buildTestableWidget(const RequestFormScreen(isTestMode: true)),
      );
      await tester.pumpAndSettle();

      expect(find.textContaining('₹'), findsNothing);
      expect(find.textContaining('Fare'), findsNothing);
      expect(find.textContaining('Price'), findsNothing);
      expect(find.textContaining('Charge'), findsNothing);
    });

    testWidgets('Trip Completed renders no fare or price', (WidgetTester tester) async {
      await tester.pumpWidget(
        buildTestableWidget(const TripCompletedScreen(tripId: 't1')),
      );
      await tester.pumpAndSettle();

      expect(find.textContaining('₹'), findsNothing);
      expect(find.textContaining('Fare'), findsNothing);
      expect(find.textContaining('Price'), findsNothing);
      expect(find.textContaining('Charge'), findsNothing);
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
