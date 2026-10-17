import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_cab/data/api/admin_repository.dart';
import 'package:smart_cab/features/admin/clients_screen.dart';
import 'package:smart_cab/features/admin/dashboard_screen.dart';
import 'package:smart_cab/features/admin/drivers_screen.dart';
import 'package:smart_cab/features/admin/reports_screen.dart';
import 'package:smart_cab/features/admin/settings_screen.dart';
import 'package:smart_cab/features/admin/users_screen.dart';
import 'package:smart_cab/features/admin/vehicles_screen.dart';
import 'package:smart_cab/features/client/client_reports_screen.dart';
import 'package:smart_cab/features/client/employee_form_screen.dart';
import 'package:smart_cab/features/client/employees_screen.dart';
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

  group('A12: Admin & Client Admin screens (A-01..A-05, A-07, A-08, L-01, L-02, L-04)', () {
    testWidgets('A-01 Dashboard renders A-01 key', (WidgetTester tester) async {
      await tester.pumpWidget(buildTestableWidget(const DashboardScreen()));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('A-01')), findsOneWidget);
    });

    testWidgets('A-02 Vehicles renders A-02 key', (WidgetTester tester) async {
      await tester.pumpWidget(buildTestableWidget(const VehiclesScreen()));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('A-02')), findsOneWidget);
    });

    testWidgets('A-03 Drivers renders A-03 key', (WidgetTester tester) async {
      await tester.pumpWidget(buildTestableWidget(const DriversScreen()));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('A-03')), findsOneWidget);
    });

    testWidgets('A-04 Clients renders A-04 key', (WidgetTester tester) async {
      await tester.pumpWidget(buildTestableWidget(const ClientsScreen()));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('A-04')), findsOneWidget);
    });

    testWidgets('A-05 Users renders A-05 key', (WidgetTester tester) async {
      await tester.pumpWidget(buildTestableWidget(const UsersScreen()));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('A-05')), findsOneWidget);
    });

    testWidgets('A-07 Reports renders A-07 key', (WidgetTester tester) async {
      await tester.pumpWidget(buildTestableWidget(const ReportsScreen()));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('A-07')), findsOneWidget);
    });

    testWidgets('A-08 Settings renders A-08 key', (WidgetTester tester) async {
      await tester.pumpWidget(buildTestableWidget(const SettingsScreen()));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('A-08')), findsOneWidget);
    });

    testWidgets('L-01 Client Employees renders L-01 key and CSV import button', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(buildTestableWidget(const ClientEmployeesScreen()));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('L-01')), findsOneWidget);
      expect(find.byKey(const Key('import-csv-button')), findsOneWidget);
    });

    testWidgets('L-02 Employee Form renders L-02 key and form inputs', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(buildTestableWidget(const EmployeeFormScreen()));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('L-02')), findsOneWidget);
      expect(find.byKey(const Key('employee-name-input')), findsOneWidget);
      expect(find.byKey(const Key('employee-phone-input')), findsOneWidget);
      expect(find.byKey(const Key('save-employee')), findsOneWidget);
    });

    testWidgets('L-04 Client Reports renders L-04 key', (WidgetTester tester) async {
      await tester.pumpWidget(buildTestableWidget(const ClientReportsScreen()));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('L-04')), findsOneWidget);
    });
  });
}

class _FakeAdminRepository implements AdminRepository {
  @override
  Future<List<api.Vehicle>> getVehicles() async => <api.Vehicle>[];

  @override
  Future<api.Vehicle> createVehicle(api.VehicleInput input) async {
    return api.VehicleLive(
      (b) => b
        ..id = 'v1'
        ..registrationNo = 'DL 01 AB 1234'
        ..seatCapacity = 4
        ..vehicleType = api.VehicleType.sedan4,
    );
  }

  @override
  Future<List<api.Driver>> getDrivers() async => <api.Driver>[];

  @override
  Future<List<api.Client>> getClients() async => <api.Client>[];

  @override
  Future<List<api.Employee>> getEmployees(String clientId) async => <api.Employee>[];
}
