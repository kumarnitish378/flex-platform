import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_cab/core/session.dart';
import 'package:smart_cab/data/api/admin_repository.dart';
import 'package:smart_cab/features/client/client_reports_screen.dart';
import 'package:smart_cab/features/client/employees_screen.dart';
import 'package:smart_cab/l10n/app_localizations.dart';
import 'package:smart_cab_api/smart_cab_api.dart' as api;

void main() {
  late _TrackingAdminRepository trackingAdminRepo;

  setUp(() {
    trackingAdminRepo = _TrackingAdminRepository();
  });

  Widget buildTestableWidget(Widget child, Session session) {
    return ProviderScope(
      overrides: [
        adminRepositoryProvider.overrideWithValue(trackingAdminRepo),
        sessionProvider.overrideWith((ref) => session),
      ],
      child: MaterialApp(
        localizationsDelegates: AppText.localizationsDelegates,
        supportedLocales: AppText.supportedLocales,
        home: child,
      ),
    );
  }

  group('Item 1: Client ID handling per role tests', () {
    testWidgets('Client Admin role omits clientId (passes null/empty)', (
      WidgetTester tester,
    ) async {
      const clientAdminSession = Session(
        roles: [Role.clientAdmin],
        activeRole: Role.clientAdmin,
        accessToken: 'token',
        userId: 'usr_client_admin',
      );

      await tester.pumpWidget(
        buildTestableWidget(const ClientEmployeesScreen(), clientAdminSession),
      );
      await tester.pumpAndSettle();

      expect(trackingAdminRepo.lastRequestedEmployeesClientId, equals(''));
      expect(find.byKey(const Key('client-selector')), findsNothing);
    });

    testWidgets('Operator Admin role selects client from GET /admin/clients', (
      WidgetTester tester,
    ) async {
      const operatorAdminSession = Session(
        roles: [Role.operatorAdmin],
        activeRole: Role.operatorAdmin,
        accessToken: 'token',
        userId: 'usr_op_admin',
      );

      await tester.pumpWidget(
        buildTestableWidget(const ClientEmployeesScreen(), operatorAdminSession),
      );
      await tester.pumpAndSettle();

      expect(trackingAdminRepo.lastRequestedEmployeesClientId, equals('c_acme'));
      expect(find.byKey(const Key('client-selector')), findsOneWidget);
    });

    testWidgets('ClientReportsScreen omits clientId for Client Admin', (
      WidgetTester tester,
    ) async {
      const clientAdminSession = Session(
        roles: [Role.clientAdmin],
        activeRole: Role.clientAdmin,
        accessToken: 'token',
        userId: 'usr_client_admin',
      );

      await tester.pumpWidget(
        buildTestableWidget(const ClientReportsScreen(), clientAdminSession),
      );
      await tester.pumpAndSettle();

      expect(trackingAdminRepo.lastRequestedBillingClientId, isNull);
    });
  });
}

class _TrackingAdminRepository implements AdminRepository {
  String? lastRequestedEmployeesClientId;
  String? lastRequestedBillingClientId;

  @override
  Future<List<api.Vehicle>> getVehicles() async => <api.Vehicle>[];

  @override
  Future<api.Vehicle> createVehicle(api.VehicleInput input) async {
    return api.VehicleLive((b) => b..id = 'v1');
  }

  @override
  Future<List<api.Driver>> getDrivers() async => <api.Driver>[];

  @override
  Future<List<api.Client>> getClients() async => <api.Client>[
        api.Client((b) => b..id = 'c_acme'..name = 'Acme Corp'),
        api.Client((b) => b..id = 'c_beta'..name = 'Beta LLC'),
      ];

  @override
  Future<List<api.Employee>> getEmployees(String clientId) async {
    lastRequestedEmployeesClientId = clientId;
    return <api.Employee>[];
  }

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
    lastRequestedBillingClientId = clientId;
    return api.BillingExport(
      (b) => b
        ..clientId = clientId ?? 'c_self'
        ..clientName = 'Client Self'
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
  }) async => 'csv_content';

  @override
  Future<String> getOperationsReportCsv({
    required DateTime from,
    required DateTime to,
    String? clientId,
  }) async => 'csv_content';
}
