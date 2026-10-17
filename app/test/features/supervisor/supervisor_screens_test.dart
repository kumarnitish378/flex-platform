import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_cab/data/api/driver_trips_repository.dart';
import 'package:smart_cab/data/api/ride_request_repository.dart';
import 'package:smart_cab/data/api/supervisor_repository.dart';
import 'package:smart_cab/features/supervisor/alerts_list_screen.dart';
import 'package:smart_cab/features/supervisor/assign_panel_screen.dart';
import 'package:smart_cab/features/supervisor/live_map_screen.dart';
import 'package:smart_cab/features/supervisor/pending_queue_screen.dart';
import 'package:smart_cab/features/supervisor/trips_board_screen.dart';
import 'package:smart_cab/l10n/app_localizations.dart';
import 'package:smart_cab_api/smart_cab_api.dart' as api;

void main() {
  late _FakeSupervisorRepository fakeSupervisorRepo;
  late _FakeRideRequestRepository fakeRideRequestRepo;
  late _FakeDriverTripsRepository fakeDriverTripsRepo;

  setUp(() {
    fakeSupervisorRepo = _FakeSupervisorRepository();
    fakeRideRequestRepo = _FakeRideRequestRepository();
    fakeDriverTripsRepo = _FakeDriverTripsRepository();
  });

  Widget buildTestableWidget(Widget child) {
    return ProviderScope(
      overrides: [
        supervisorRepositoryProvider.overrideWithValue(fakeSupervisorRepo),
        rideRequestRepositoryProvider.overrideWithValue(fakeRideRequestRepo),
        driverTripsRepositoryProvider.overrideWithValue(fakeDriverTripsRepo),
      ],
      child: MaterialApp(
        localizationsDelegates: AppText.localizationsDelegates,
        supportedLocales: AppText.supportedLocales,
        home: child,
      ),
    );
  }

  group('A11: Supervisor screens (S-01, S-02, S-03, S-04, S-07)', () {
    testWidgets('S-01 Live Map renders S-01 key and map widget', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(
        buildTestableWidget(const SupervisorLiveMapScreen(isTestMode: true)),
      );
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('S-01')), findsOneWidget);
      expect(find.byKey(const Key('supervisor-map')), findsOneWidget);
    });

    testWidgets('S-02 Pending Queue renders S-02 key', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(buildTestableWidget(const PendingQueueScreen()));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('S-02')), findsOneWidget);
    });

    testWidgets('S-03 Assign Panel renders S-03 key', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(
        buildTestableWidget(const AssignPanelScreen(requestId: 'req_100')),
      );
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('S-03')), findsOneWidget);
    });

    testWidgets('S-04 Trips Board renders S-04 key', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(buildTestableWidget(const TripsBoardScreen()));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('S-04')), findsOneWidget);
    });

    testWidgets('S-07 Alerts List renders S-07 key', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(buildTestableWidget(const AlertsListScreen()));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('S-07')), findsOneWidget);
    });
  });
}

class _FakeSupervisorRepository implements SupervisorRepository {
  @override
  Future<List<api.VehicleLive>> getLiveVehicles() async => <api.VehicleLive>[];

  @override
  Future<List<api.Candidate>> getCandidates(String requestId) async =>
      <api.Candidate>[];

  @override
  Future<List<api.Candidate>> getSuggestions(String requestId) async =>
      <api.Candidate>[];

  @override
  Future<void> submitSuggestionDecision(
    String suggestionId, {
    required String decision,
    String? vehicleId,
    String? reasonCode,
    String? note,
  }) async {}

  @override
  Future<api.Trip> assignRequest({
    required String requestId,
    String? vehicleId,
    String? tripId,
  }) async {
    return api.Trip((b) => b..id = 't1');
  }

  @override
  Future<List<api.Alert>> getAlerts() async => <api.Alert>[];

  @override
  Future<void> acknowledgeAlert(String alertId) async {}

  @override
  Future<void> resolveAlert(String alertId) async {}
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

class _FakeDriverTripsRepository implements DriverTripsRepository {
  @override
  Future<List<api.Trip>> getTrips() async => <api.Trip>[];

  @override
  Future<api.Trip> getTripDetail(String tripId) async {
    return api.Trip((b) => b..id = tripId);
  }

  @override
  Future<api.Trip> startTrip(String tripId) async {
    return api.Trip((b) => b..id = tripId);
  }

  @override
  Future<void> reportIssue({required String issueType, String? note}) async {}
}
