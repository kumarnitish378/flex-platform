import 'package:flutter_test/flutter_test.dart';
import 'package:smart_cab/services/gps_location_service.dart';
import 'package:smart_cab_api/smart_cab_api.dart' as api;

void main() {
  group('Item 1 & Item 2: GpsLocationService distance filter, heartbeat, and offline buffering tests', () {
    late GpsLocationService gpsService;

    setUp(() {
      gpsService = GpsLocationService(
        distanceFilterM: 5.0,
        heartbeatSeconds: 60,
        maxBufferedPings: 3,
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

    test('Offline buffering caps at max pings and generates batch payload', () {
      final now = DateTime.now();
      final ping1 = api.LocationPing((b) => b..ts = now..lat = 28.5..lng = 77.3);
      final ping2 = api.LocationPing((b) => b..ts = now..lat = 28.51..lng = 77.31);
      final ping3 = api.LocationPing((b) => b..ts = now..lat = 28.52..lng = 77.32);
      final ping4 = api.LocationPing((b) => b..ts = now..lat = 28.53..lng = 77.33);

      gpsService.bufferPing(ping1);
      gpsService.bufferPing(ping2);
      gpsService.bufferPing(ping3);
      gpsService.bufferPing(ping4); // Max capacity is 3, so ping1 is dropped

      expect(gpsService.bufferedQueue.length, equals(3));
      expect(gpsService.bufferedQueue.first.lat, equals(28.51));

      final Map<String, dynamic> payload = gpsService.getBufferedBatchPayload();
      expect(payload['v'], equals(1));
      expect((payload['batch'] as List).length, equals(3));

      gpsService.clearBufferedQueue();
      expect(gpsService.bufferedQueue, isEmpty);
    });
  });
}
