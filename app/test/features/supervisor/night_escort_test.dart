import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_cab/data/api/driver_trips_repository.dart';
import 'package:smart_cab/data/api/supervisor_repository.dart';
import 'package:smart_cab/features/driver/trip_detail_screen.dart';
import 'package:smart_cab/features/supervisor/trips_board_screen.dart';
import 'package:smart_cab/l10n/app_localizations.dart';
import 'package:smart_cab_api/smart_cab_api.dart' as api;

void main() {
  late _FakeSupervisorRepository fakeSupervisorRepo;
  late _FakeDriverTripsRepository fakeDriverTripsRepo;

  setUp(() {
    fakeSupervisorRepo = _FakeSupervisorRepository();
    fakeDriverTripsRepo = _FakeDriverTripsRepository();
  });

  Widget buildTestableWidget(Widget child) {
    return ProviderScope(
      overrides: [
        supervisorRepositoryProvider.overrideWithValue(fakeSupervisorRepo),
        driverTripsRepositoryProvider.overrideWithValue(fakeDriverTripsRepo),
      ],
      child: MaterialApp(
        localizationsDelegates: AppText.localizationsDelegates,
        supportedLocales: AppText.supportedLocales,
        home: child,
      ),
    );
  }

  group('Item 2: Night escort UI and start trip gate tests', () {
    testWidgets('Trips Board renders Escort Needed banner and confirmation buttons', (
      WidgetTester tester,
    ) async {
      fakeDriverTripsRepo.tripToReturn = api.Trip(
        (b) => b
          ..id = 't_escort_1'
          ..status = api.TripStatus.dispatched
          ..escort.required_ = true
          ..escort.confirmed = false,
      );

      await tester.pumpWidget(buildTestableWidget(const TripsBoardScreen()));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('escort-needed-banner-t_escort_1')), findsOneWidget);
      expect(find.byKey(const Key('escort-arranged-t_escort_1')), findsOneWidget);
      expect(find.byKey(const Key('male-co-rider-t_escort_1')), findsOneWidget);

      await tester.tap(find.byKey(const Key('escort-arranged-t_escort_1')));
      await tester.pumpAndSettle();

      expect(fakeSupervisorRepo.confirmCalled, isTrue);
    });

    testWidgets('TripDetailScreen shows waiting for supervisor message on 409 escort required error', (
      WidgetTester tester,
    ) async {
      fakeDriverTripsRepo.tripToReturn = api.Trip(
        (b) => b
          ..id = 't_escort_2'
          ..status = api.TripStatus.dispatched
          ..escort.required_ = true
          ..escort.confirmed = false,
      );
      fakeDriverTripsRepo.shouldFailStartWithEscort = true;

      await tester.pumpWidget(
        buildTestableWidget(const TripDetailScreen(tripId: 't_escort_2')),
      );
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('start-trip')), findsOneWidget);
      await tester.tap(find.byKey(const Key('start-trip')));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('escort-start-blocked-msg')), findsOneWidget);
      expect(find.text('Waiting for supervisor to confirm the night escort'), findsOneWidget);
    });
  });
}

class _FakeSupervisorRepository implements SupervisorRepository {
  bool confirmCalled = false;

  @override
  Future<List<api.VehicleLive>> getLiveVehicles() async => <api.VehicleLive>[];

  @override
  Future<List<api.Candidate>> getCandidates(String requestId) async => <api.Candidate>[];

  @override
  Future<List<api.Candidate>> getSuggestions(String requestId) async => <api.Candidate>[];

  @override
  Future<List<api.RequestHint>> getDispatchHints() async => <api.RequestHint>[];

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
  }) async => api.Trip((b) => b..id = 't1');

  @override
  Future<api.Trip> confirmEscort({
    required String tripId,
    required String basis,
    String? note,
  }) async {
    confirmCalled = true;
    return api.Trip(
      (b) => b
        ..id = tripId
        ..escort.required_ = true
        ..escort.confirmed = true
        ..escort.confirmedBy = 'usr_sup'
        ..escort.confirmedAt = DateTime.now(),
    );
  }

  @override
  Future<List<api.Alert>> getAlerts() async => <api.Alert>[];

  @override
  Future<void> acknowledgeAlert(String alertId) async {}

  @override
  Future<void> resolveAlert(String alertId) async {}
}

class _FakeDriverTripsRepository implements DriverTripsRepository {
  api.Trip? tripToReturn;
  bool shouldFailStartWithEscort = false;

  @override
  Future<List<api.Trip>> getTrips() async =>
      tripToReturn != null ? <api.Trip>[tripToReturn!] : <api.Trip>[];

  @override
  Future<api.Trip> getTripDetail(String tripId) async =>
      tripToReturn ?? api.Trip((b) => b..id = tripId);

  @override
  Future<api.Trip> startTrip(String tripId) async {
    if (shouldFailStartWithEscort) {
      throw const DriverTripsException('409 escort_confirmation_required', statusCode: 409);
    }
    return tripToReturn ?? api.Trip((b) => b..id = tripId);
  }

  @override
  Future<void> reportIssue({required String issueType, String? note}) async {}
}
