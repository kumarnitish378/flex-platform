import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_cab/data/api/admin_repository.dart';
import 'package:smart_cab/features/admin/reports_screen.dart';
import 'package:smart_cab/features/client/client_reports_screen.dart';
import 'package:smart_cab/l10n/app_localizations.dart';
import 'package:smart_cab_api/smart_cab_api.dart' as api;

void main() {
  late _FakeAdminRepository fakeAdminRepo;

  setUp(() {
    fakeAdminRepo = _FakeAdminRepository();
  });

  Widget buildTestableWidget(Widget child) {
    return ProviderScope(
      overrides: [
        adminRepositoryProvider.overrideWithValue(fakeAdminRepo),
      ],
      child: MaterialApp(
        localizationsDelegates: AppText.localizationsDelegates,
        supportedLocales: AppText.supportedLocales,
        home: child,
      ),
    );
  }

  group('A19: Reports and billing export (A-07, L-04)', () {
    testWidgets('A-07 Reports Screen renders distance, acceptance rate, and CSV button', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(buildTestableWidget(const ReportsScreen()));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('A-07')), findsOneWidget);
      expect(find.byKey(const Key('download-billing-csv')), findsOneWidget);
      expect(find.byKey(const Key('cab-km-per-trip')), findsOneWidget);
      expect(find.text('Cab-km per trip: not measured'), findsOneWidget);
      expect(find.byKey(const Key('acceptance-rate-first')), findsOneWidget);
      expect(find.byKey(const Key('acceptance-rate-alt')), findsOneWidget);
    });

    testWidgets('L-04 Client Reports renders billing treatment rules card', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(buildTestableWidget(const ClientReportsScreen()));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('L-04')), findsOneWidget);
      expect(find.byKey(const Key('billing-treatment-card')), findsOneWidget);
    });
  });
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
  }) async {
    return api.OperationsReport(
      (b) => b
        ..period.from = api.Date(from.year, from.month, from.day)
        ..period.to = api.Date(to.year, to.month, to.day)
        ..requests.total = 10
        ..requests.completed = 8
        ..requests.stillOpen = 2
        ..wait.medianMinutes = 12.0
        ..wait.p90Minutes = 24.0
        ..pooling.trips = 4
        ..pooling.poolingRate = 0.5
        ..distance.tripsMeasured = 0
        ..distance.cabKmTotal = null
        ..distance.cabKmPerTrip = null
        ..distance.cabKmPerRider = null
        ..overrides.total = 1
        ..suggestions.answeredByAPerson = 5
        ..suggestions.accepted = 4
        ..suggestions.rejected = 1
        ..suggestions.acceptanceRate = 0.8
        ..suggestions.acceptanceRateWithAlternatives = 0.8
        ..optimizer.runs = 10,
    );
  }

  @override
  Future<api.BillingExport?> getBillingExport({
    required String month,
    String? clientId,
  }) async {
    return api.BillingExport(
      (b) => b
        ..clientId = 'c1'
        ..clientName = 'Client One'
        ..month = month
        ..treatment.noShowBillable = true
        ..treatment.lateCancelBillable = false
        ..treatment.distanceBasis = api.BillingExportTreatmentDistanceBasisEnum.tripShare
        ..summary.rides = 10
        ..summary.billableRides = 8
        ..summary.billableKm = 120.0
        ..rows.replace([]),
    );
  }

  @override
  Future<String> getBillingExportCsv({
    required String month,
    String? clientId,
  }) async {
    return 'client_id,month,billable_rides,billable_km\nc1,$month,8,120.0';
  }

  @override
  Future<String> getOperationsReportCsv({
    required DateTime from,
    required DateTime to,
    String? clientId,
  }) async {
    return 'from,to,requests,completed\n${from.toIso8601String()},${to.toIso8601String()},10,8';
  }
}
