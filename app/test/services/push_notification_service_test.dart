import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_cab/services/push_notification_service.dart';

void main() {
  group('A07: PushNotificationService', () {
    test('handleNotificationTap resolves explicit target_route', () {
      final ProviderContainer container = ProviderContainer();
      final PushNotificationService service =
          container.read(pushNotificationServiceProvider);

      const PushNotification notif = PushNotification(
        id: 'n1',
        title: 'Cab 5 min away',
        body: 'Your cab is arriving soon',
        targetRoute: '/employee/trip/t_123',
      );

      final String? route = service.handleNotificationTap(notif);
      expect(route, '/employee/trip/t_123');
      container.dispose();
    });

    test('handleNotificationTap resolves route from trip_id data', () {
      final ProviderContainer container = ProviderContainer();
      final PushNotificationService service =
          container.read(pushNotificationServiceProvider);

      const PushNotification notif = PushNotification(
        id: 'n2',
        title: 'Trip Started',
        body: 'Driver has started the trip',
        data: <String, dynamic>{'trip_id': 't_456'},
      );

      final String? route = service.handleNotificationTap(notif);
      expect(route, '/employee/trip/t_456');
      container.dispose();
    });
  });
}
