import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_cab/data/api/admin_repository.dart';
import 'package:smart_cab/data/api/supervisor_repository.dart';
import 'package:smart_cab/features/admin/mode_settings_screen.dart';
import 'package:smart_cab/features/supervisor/suggestions_panel_screen.dart';
import 'package:smart_cab/l10n/app_localizations.dart';
import 'package:smart_cab_api/smart_cab_api.dart' as api;

void main() {
  late _FakeSupervisorRepository fakeSupervisorRepo;
  late _FakeAdminRepository fakeAdminRepo;

  setUp(() {
    fakeSupervisorRepo = _FakeSupervisorRepository();
    fakeAdminRepo = _FakeAdminRepository();
  });

  Widget buildTestableWidget(Widget child) {
    return ProviderScope(
      overrides: [
        supervisorRepositoryProvider.overrideWithValue(fakeSupervisorRepo),
        adminRepositoryProvider.overrideWithValue(fakeAdminRepo),
      ],
      child: MaterialApp(
        localizationsDelegates: AppText.localizationsDelegates,
        supportedLocales: AppText.supportedLocales,
        home: child,
      ),
    );
  }

  group('A13 & A14: Suggestions panel & Mode Settings (S-05, A-06)', () {
    testWidgets('S-05 Suggestions Panel renders S-05 key and failsafe timer', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(
        buildTestableWidget(const SuggestionsPanelScreen(requestId: 'req_100')),
      );
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('S-05')), findsOneWidget);
      expect(find.byKey(const Key('failsafe-timer')), findsOneWidget);
    });

    testWidgets('A-06 Mode Settings renders A-06 key', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(buildTestableWidget(const ModeSettingsScreen()));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('A-06')), findsOneWidget);
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

class _FakeAdminRepository implements AdminRepository {
  @override
  Future<List<api.Vehicle>> getVehicles() async => <api.Vehicle>[];

  @override
  Future<api.Vehicle> createVehicle(api.VehicleInput input) async {
    return api.VehicleLive((b) => b..id = 'v1');
  }

  @override
  Future<List<api.Driver>> getDrivers() async => <api.Driver>[];

  @override
  Future<List<api.Client>> getClients() async => <api.Client>[];

  @override
  Future<List<api.Employee>> getEmployees(String clientId) async => <api.Employee>[];
}
