import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_cab/data/api/admin_repository.dart';
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

  group('Item 3: Employee gender in form and CSV import preview tests', () {
    testWidgets('EmployeeFormScreen renders gender dropdown selector', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(buildTestableWidget(const EmployeeFormScreen()));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('L-02')), findsOneWidget);
      expect(find.byKey(const Key('employee-gender-select')), findsOneWidget);
    });

    testWidgets('ClientEmployeesScreen renders CSV import preview with gender breakdown', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(buildTestableWidget(const ClientEmployeesScreen()));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('L-01')), findsOneWidget);
      expect(find.byKey(const Key('import-csv-button')), findsOneWidget);

      await tester.tap(find.byKey(const Key('import-csv-button')));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('csv-import-dialog')), findsOneWidget);
      expect(find.textContaining('Gender breakdown'), findsOneWidget);
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
  Future<List<api.Employee>> getEmployees(String clientId) async => <api.Employee>[
        api.Employee(
          (b) => b
            ..id = 'e1'
            ..name = 'Anita Sharma'
            ..phone = '+91 9876543210'
            ..gender = api.EmployeeInputGenderEnum.female,
        ),
      ];

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
  }) async => 'csv_content';

  @override
  Future<String> getOperationsReportCsv({
    required DateTime from,
    required DateTime to,
    String? clientId,
  }) async => 'csv_content';
}
