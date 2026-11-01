import 'package:flutter_test/flutter_test.dart';
import 'package:smart_cab/services/gps_location_service.dart';
import 'package:smart_cab_api/smart_cab_api.dart' as api;

void main() {
  group('Item 2: GpsLocationService distance filter and heartbeat tests', () {
    late GpsLocationService gpsService;

    setUp(() {
      gpsService = GpsLocationService(
        distanceFilterM: 5.0,
        heartbeatSeconds: 60,
      );
    });

    test('Initial GPS fix always publishes', () {
      final p1 = api.LatLng((b) => b..lat = 28.5703..lng = 77.3218);
      final now = DateTime.now();

      expect(gpsService.shouldPublishFix(p1, now), isTrue);
    });

    test('Fix moving less than 5m within 60s does NOT publish', () {
      final p1 = api.LatLng((b) => b..lat = 28.5703..lng = 77.3218);
      final now = DateTime.now();

      gpsService.shouldPublishFix(p1, now);

      // Move ~2 metres (0.00002 deg lat ~ 2.2 m)
      final p2 = api.LatLng((b) => b..lat = 28.57032..lng = 77.3218);
      final t2 = now.add(const Duration(seconds: 10));

      expect(gpsService.shouldPublishFix(p2, t2), isFalse);
    });

    test('Fix moving >= 5m publishes immediately', () {
      final p1 = api.LatLng((b) => b..lat = 28.5703..lng = 77.3218);
      final now = DateTime.now();

      gpsService.shouldPublishFix(p1, now);

      // Move ~11 metres (0.0001 deg lat ~ 11.1 m)
      final p2 = api.LatLng((b) => b..lat = 28.57041..lng = 77.3218);
      final t2 = now.add(const Duration(seconds: 5));

      expect(gpsService.shouldPublishFix(p2, t2), isTrue);
    });

    test('Stationary fix publishes heartbeat after 60s', () {
      final p1 = api.LatLng((b) => b..lat = 28.5703..lng = 77.3218);
      final now = DateTime.now();

      gpsService.shouldPublishFix(p1, now);

      // Stationary (0m moved) after 61s
      final t2 = now.add(const Duration(seconds: 61));

      expect(gpsService.shouldPublishFix(p1, t2), isTrue);
    });
  });
}
