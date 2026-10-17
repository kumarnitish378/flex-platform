import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_cab/core/session.dart';
import 'package:smart_cab/services/realtime_service.dart';

void main() {
  test('RealtimeEvent parses event JSON properly', () {
    final Map<String, dynamic> json = <String, dynamic>{
      'type': 'event',
      'event': 'vehicle.location',
      'channel': 'operator.op1.vehicles',
      'data': <String, dynamic>{'vehicle_id': 'v1', 'lat': 28.57, 'lng': 77.32},
    };

    final RealtimeEvent event = RealtimeEvent.fromJson(json);

    expect(event.event, 'vehicle.location');
    expect(event.channel, 'operator.op1.vehicles');
    expect(event.data['vehicle_id'], 'v1');
    expect(event.data['lat'], 28.57);
  });

  test('RealtimeService manages subscription channels list', () {
    final ProviderContainer container = ProviderContainer(
      overrides: [
        sessionProvider.overrideWith(_FakeSession.new),
      ],
    );

    final RealtimeService service = container.read(realtimeServiceProvider);
    expect(service.isConnected, isFalse);

    service.subscribe(<String>['trip.t123', 'operator.op1.vehicles']);
    service.unsubscribe(<String>['trip.t123']);

    container.dispose();
  });
}

class _FakeSession extends SessionNotifier {
  @override
  Session build() => const Session(
        roles: <Role>[Role.employee],
        activeRole: Role.employee,
        accessToken: 'test-token',
        userId: 'u1',
      );
}
