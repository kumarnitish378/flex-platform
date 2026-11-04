import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_cab/data/api/ride_request_repository.dart';
import 'package:smart_cab/features/employee/employee_home_screen.dart';
import 'package:smart_cab/features/employee/request_confirmation_screen.dart';
import 'package:smart_cab/features/employee/request_form_screen.dart';
import 'package:smart_cab/l10n/app_localizations.dart';
import 'package:smart_cab_api/smart_cab_api.dart' as api;

void main() {
  late _FakeRideRequestRepository fakeRepo;

  setUp(() {
    fakeRepo = _FakeRideRequestRepository();
  });

  Widget buildTestableWidget(Widget child) {
    return ProviderScope(
      overrides: [
        rideRequestRepositoryProvider.overrideWithValue(fakeRepo),
      ],
      child: MaterialApp(
        localizationsDelegates: AppText.localizationsDelegates,
        supportedLocales: AppText.supportedLocales,
        home: child,
      ),
    );
  }

  group('A06: Employee screens (E-01..E-03)', () {
    testWidgets('E-01 Employee Home renders E-01 key and request button', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(buildTestableWidget(const EmployeeHomeScreen()));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('E-01')), findsOneWidget);
      expect(find.byKey(const Key('request-cab-button')), findsOneWidget);
    });

    testWidgets('E-02 Request Form renders E-02 key and controls (no search box)', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(buildTestableWidget(const RequestFormScreen()));
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('E-02')), findsOneWidget);
      expect(find.byKey(const Key('direction-toggle')), findsOneWidget);
      expect(find.byKey(const Key('request-map')), findsOneWidget);
      expect(find.byKey(const Key('landmark-input')), findsOneWidget);
      expect(find.byKey(const Key('urgency-picker')), findsOneWidget);
      expect(find.byKey(const Key('submit-request')), findsOneWidget);

      // Verify no address search box is present (ADR-0010 §A1)
      expect(find.byType(SearchBar), findsNothing);
    });

    testWidgets('E-03 Request Confirmation renders E-03 key and cancel button', (
      WidgetTester tester,
    ) async {
      fakeRepo.requestToReturn = api.RideRequest(
        (api.RideRequestBuilder b) => b
          ..id = 'req_test_123'
          ..status = api.RequestStatus.requested
          ..direction = api.Direction.toOffice
          ..location.replace(
            api.LatLng(
              (api.LatLngBuilder lb) => lb
                ..lat = 28.5703
                ..lng = 77.3218,
            ),
          )
          ..urgency = api.Urgency.medium,
      );

      await tester.pumpWidget(
        buildTestableWidget(
          const RequestConfirmationScreen(requestId: 'req_test_123'),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('E-03')), findsOneWidget);
      expect(find.byKey(const Key('request-status-text')), findsOneWidget);
      expect(find.text('Finding your cab'), findsOneWidget);
      expect(find.byKey(const Key('cancel-request')), findsOneWidget);
    });
  });
}

class _FakeRideRequestRepository implements RideRequestRepository {
  api.RideRequest? requestToReturn;

  @override
  Future<List<api.RideRequest>> getMyRequests() async => <api.RideRequest>[];

  @override
  Future<api.RideRequest> createRequest(api.RideRequestInput input) async {
    return requestToReturn ??
        api.RideRequest(
          (api.RideRequestBuilder b) => b
            ..id = 'req_new'
            ..status = api.RequestStatus.requested
            ..direction = input.direction
            ..location.replace(
              api.LatLng(
                (api.LatLngBuilder lb) => lb
                  ..lat = input.location?.lat ?? 28.5703
                  ..lng = input.location?.lng ?? 77.3218,
              ),
            )
            ..urgency = input.urgency,
        );
  }

  @override
  Future<api.RideRequest> getRequest(String requestId) async {
    return requestToReturn ??
        api.RideRequest(
          (api.RideRequestBuilder b) => b
            ..id = requestId
            ..status = api.RequestStatus.requested
            ..direction = api.Direction.toOffice
            ..location.replace(
              api.LatLng(
                (api.LatLngBuilder lb) => lb
                  ..lat = 28.5703
                  ..lng = 77.3218,
              ),
            )
            ..urgency = api.Urgency.medium,
        );
  }

  @override
  Future<api.RideRequest> cancelRequest(String requestId, {String? reason}) async {
    return api.RideRequest(
      (api.RideRequestBuilder b) => b
        ..id = requestId
        ..status = api.RequestStatus.cancelled
        ..direction = api.Direction.toOffice
        ..location.replace(
          api.LatLng(
            (api.LatLngBuilder lb) => lb
              ..lat = 28.5703
              ..lng = 77.3218,
          ),
        )
        ..urgency = api.Urgency.medium,
    );
  }
}
