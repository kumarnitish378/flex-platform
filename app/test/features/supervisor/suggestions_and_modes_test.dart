import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_cab/data/api/admin_repository.dart';
import 'package:smart_cab/data/api/supervisor_repository.dart';
import 'package:smart_cab/features/admin/mode_settings_screen.dart';
import 'package:smart_cab/features/supervisor/alerts_list_screen.dart';
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

    testWidgets('A17 S-05 renders optimizer hint banner in manual scope', (
      WidgetTester tester,
    ) async {
      fakeSupervisorRepo.hintToReturn = api.RequestHint(
        (b) => b
          ..requestId = 'req_100'
          ..vehicleId = 'v_cab_99'
          ..pickupEtaMinutes = 8
          ..reasons.replace(['8 min away', '2 seats left']),
      );

      await tester.pumpWidget(
        buildTestableWidget(const SuggestionsPanelScreen(requestId: 'req_100')),
      );
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('optimizer-hint-card')), findsOneWidget);
      expect(find.text('Proposed Cab: v_cab_99'), findsOneWidget);
      expect(find.byKey(const Key('apply-hint-button')), findsOneWidget);
    });

    testWidgets('A-06 Mode Settings renders A-06 key and Full Auto mode segment', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(buildTestableWidget(const ModeSettingsScreen()));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('A-06')), findsOneWidget);
      expect(find.text('Full Auto'), findsWidgets);
    });

    testWidgets('A18 S-07 renders mode_prompt alert banner with Switch to Manual button', (
      WidgetTester tester,
    ) async {
      fakeSupervisorRepo.alertToReturn = api.Alert(
        (b) => b
          ..id = 'alt_prompt_1'
          ..type = api.AlertTypeEnum.modePrompt
          ..severity = api.AlertSeverityEnum.warning
          ..status = api.AlertStatusEnum.open,
      );

      await tester.pumpWidget(buildTestableWidget(const AlertsListScreen()));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('mode-prompt-card-alt_prompt_1')), findsOneWidget);
      expect(find.byKey(const Key('switch-to-manual-alt_prompt_1')), findsOneWidget);

      await tester.tap(find.byKey(const Key('switch-to-manual-alt_prompt_1')));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('mode-prompt-card-alt_prompt_1')), findsNothing);
    });
  });
}

class _FakeSupervisorRepository implements SupervisorRepository {
  api.RequestHint? hintToReturn;
  api.Alert? alertToReturn;

  @override
  Future<List<api.VehicleLive>> getLiveVehicles() async => <api.VehicleLive>[];

  @override
  Future<List<api.Candidate>> getCandidates(String requestId) async =>
      <api.Candidate>[];

  @override
  Future<List<api.Candidate>> getSuggestions(String requestId) async =>
      <api.Candidate>[];

  @override
  Future<List<api.RequestHint>> getDispatchHints() async =>
      hintToReturn != null ? <api.RequestHint>[hintToReturn!] : <api.RequestHint>[];

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
  Future<api.Trip> confirmEscort({
    required String tripId,
    required String basis,
    String? note,
  }) async => api.Trip((b) => b..id = tripId);

  @override
  Future<List<api.Alert>> getAlerts() async =>
      alertToReturn != null ? <api.Alert>[alertToReturn!] : <api.Alert>[];

  @override
  Future<void> acknowledgeAlert(String alertId) async {}

  @override
  Future<void> resolveAlert(String alertId) async {
    if (alertToReturn?.id == alertId) {
      alertToReturn = alertToReturn!.rebuild((b) => b..status = api.AlertStatusEnum.resolved);
    }
  }
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

  @override
  Future<api.OperationsReport?> getOperationsReport({
    required DateTime from,
    required DateTime to,
    String? clientId,
  }) async => null;

  @override
  Future<api.BillingExport?> getBillingExport({
    required String month,
    String? clientId,
  }) async => null;

  @override
  Future<String> getBillingExportCsv({
    required String month,
    String? clientId,
  }) async => 'csv_data';

  @override
  Future<String> getOperationsReportCsv({
    required DateTime from,
    required DateTime to,
    String? clientId,
  }) async => 'csv_data';

  @override
  Future<void> updateDutySessionBillingBasis({
    required String sessionId,
    required String basis,
    String? note,
  }) async {}
}
