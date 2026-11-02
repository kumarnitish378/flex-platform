import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_cab/data/api/admin_repository.dart';
import 'package:smart_cab/features/admin/reports_screen.dart';
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

  group('Item 6: Per-cab-per-day billing rows and monthly total tests', () {
    testWidgets('ReportsScreen renders per-cab billing card and monthly total', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(buildTestableWidget(const ReportsScreen()));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('per-cab-billing-card')), findsOneWidget);
      expect(find.byKey(const Key('monthly-total-summary')), findsOneWidget);
      expect(find.textContaining('Cab DL 01 AB 1234'), findsOneWidget);
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
  }) async => null;

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
        ..summary.billedKm = 100.0
        ..summary.amount = 800.0
        ..rows.replace([
          api.BillingExportRowsInner(
            (b) => b
              ..cab = 'Cab DL 01 AB 1234'
              ..gpsKm = 10.0
              ..odometerKm = 12.0
              ..billedKm = 10.0
              ..amount = 80.0
              ..flags.replace([api.BillingExportRowsInnerFlagsEnum.odometerGap]),
          ),
        ]),
    );
  }

  @override
  Future<String> getBillingExportCsv({
    required String month,
    String? clientId,
  }) async => 'csv_content';

  @override
  Future<String> getOperationsReportCsv({
    required DateTime from,
    required DateTime to,
    String? clientId,
  }) async => 'csv_content';

  @override
  Future<void> updateDutySessionBillingBasis({
    required String sessionId,
    required String basis,
    String? note,
  }) async {}
}
