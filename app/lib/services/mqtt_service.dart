library;

import 'package:smart_cab_api/smart_cab_api.dart' as api;

/// Service for Driver MQTT GPS transmission (A09).
///
/// Respects host, port, and TLS explicitly returned from DutyStateMqtt.
class MqttService {
  MqttService();

  bool _isConnected = false;
  String? _currentHost;
  int? _currentPort;
  bool _useTls = false;

  bool get isConnected => _isConnected;
  String? get currentHost => _currentHost;
  int? get currentPort => _currentPort;
  bool get useTls => _useTls;

  /// Configure and connect using DutyStateMqtt details returned by /driver/duty.
  void configureFromMqttState(api.DutyStateMqtt? mqtt) {
    if (mqtt == null) {
      _isConnected = false;
      return;
    }

    _currentHost = mqtt.host;
    _currentPort = mqtt.port;
    _useTls = mqtt.tls ?? false;
    _isConnected = true;
  }

  void disconnect() {
    _isConnected = false;
  }
}
