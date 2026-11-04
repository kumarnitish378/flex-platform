import 'package:flutter_test/flutter_test.dart';
import 'package:smart_cab/services/mqtt_service.dart';
import 'package:smart_cab_api/smart_cab_api.dart' as api;

void main() {
  group('A09: MqttService', () {
    test('configures host, port, and tls from DutyStateMqtt without inferring', () {
      final MqttService service = MqttService();

      final api.DutyStateMqtt mqtt = api.DutyStateMqtt(
        (api.DutyStateMqttBuilder b) => b
          ..host = 'staging.smartcab.internal'
          ..port = 8883
          ..tls = true
          ..username = 'driver_v1'
          ..password = 'secret'
          ..topicPrefix = 'sc/v1/vehicles/v1',
      );

      service.configureFromMqttState(mqtt);

      expect(service.isConnected, isTrue);
      expect(service.currentHost, 'staging.smartcab.internal');
      expect(service.currentPort, 8883);
      expect(service.useTls, isTrue);
    });
  });
}
