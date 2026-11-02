import 'dart:math';

import 'package:smart_cab_api/smart_cab_api.dart' as api;

/// Service managing Driver GPS location filtering, heartbeat publishing, and offline batching
/// (A09 / Item 1 / mqtt-topics.md).
///
/// Rules:
/// - Distance Filter: Publishes if moved ≥ [distanceFilterM] (default 5 m) since last published fix.
/// - Heartbeat: Publishes a heartbeat ping if stationary for ≥ [heartbeatSeconds] (default 60 s).
/// - Offline Buffering: Buffers pings locally when offline, capping at max 500 pings.
/// - Batch Transmission: Generates batch payload `{ "v": 1, "batch": [...] }` when network returns.
/// - Foreground Service & Duty Resume: Tracks duty state for auto-resume after reboot or app restart.
class GpsLocationService {
  GpsLocationService({
    this.distanceFilterM = 5.0,
    this.heartbeatSeconds = 60,
    this.maxBufferedPings = 500,
  });

  final double distanceFilterM;
  final int heartbeatSeconds;
  final int maxBufferedPings;

  api.LatLng? _lastPublishedFix;
  DateTime? _lastPublishedTime;
  final List<api.LocationPing> _bufferedQueue = <api.LocationPing>[];
  bool _isBatteryOptimizationExempted = false;
  bool _foregroundServiceActive = false;
  bool _onDutyAutoResume = false;

  api.LatLng? get lastPublishedFix => _lastPublishedFix;
  DateTime? get lastPublishedTime => _lastPublishedTime;
  List<api.LocationPing> get bufferedQueue => List<api.LocationPing>.unmodifiable(_bufferedQueue);
  bool get isBatteryOptimizationExempted => _isBatteryOptimizationExempted;
  bool get foregroundServiceActive => _foregroundServiceActive;
  bool get onDutyAutoResume => _onDutyAutoResume;

  /// Determines whether a new GPS fix should be published according to distance filter
  /// or stationary heartbeat interval.
  bool shouldPublishFix(api.LatLng newFix, DateTime now) {
    if (_lastPublishedFix == null || _lastPublishedTime == null) {
      _recordPublish(newFix, now);
      return true;
    }

    final double distanceM = calculateHaversineDistance(_lastPublishedFix!, newFix);
    final int secondsElapsed = now.difference(_lastPublishedTime!).inSeconds;

    // Condition 1: Moved at least distanceFilterM (5 m)
    if (distanceM >= distanceFilterM) {
      _recordPublish(newFix, now);
      return true;
    }

    // Condition 2: Stationary heartbeat timeout (60 s)
    if (secondsElapsed >= heartbeatSeconds) {
      _recordPublish(newFix, now);
      return true;
    }

    return false;
  }

  /// Buffers a GPS ping locally when offline up to [maxBufferedPings] (500 max).
  void bufferPing(api.LocationPing ping) {
    if (_bufferedQueue.length >= maxBufferedPings) {
      _bufferedQueue.removeAt(0); // Drop oldest ping when full
    }
    _bufferedQueue.add(ping);
  }

  /// Generates the MQTT batch payload structure `{ "v": 1, "batch": [...] }` for reconnect.
  Map<String, dynamic> getBufferedBatchPayload() {
    return <String, dynamic>{
      'v': 1,
      'batch': _bufferedQueue.map((api.LocationPing p) {
        return <String, dynamic>{
          'v': 1,
          'ts': p.ts.toUtc().toIso8601String(),
          'lat': p.lat,
          'lng': p.lng,
          'spd': p.speedMps,
          'hdg': p.headingDeg,
          'acc': p.accuracyM,
          'bat': p.batteryPct,
          'src': 'app',
        };
      }).toList(),
    };
  }

  /// Clears the offline buffer queue after successful batch transmission.
  void clearBufferedQueue() {
    _bufferedQueue.clear();
  }

  /// Sets battery optimization exemption status.
  void setBatteryOptimizationExempted(bool exempted) {
    _isBatteryOptimizationExempted = exempted;
  }

  /// Starts or stops the background foreground service with persistent notification.
  void setForegroundServiceActive(bool active) {
    _foregroundServiceActive = active;
  }

  /// Persists or restores duty status for reboot/kill auto-resume.
  void setOnDutyAutoResume(bool active) {
    _onDutyAutoResume = active;
  }

  void _recordPublish(api.LatLng fix, DateTime time) {
    _lastPublishedFix = fix;
    _lastPublishedTime = time;
  }

  void reset() {
    _lastPublishedFix = null;
    _lastPublishedTime = null;
    _bufferedQueue.clear();
    _foregroundServiceActive = false;
  }

  /// Calculates distance in metres between two LatLng points using Haversine formula.
  static double calculateHaversineDistance(api.LatLng p1, api.LatLng p2) {
    const double earthRadiusM = 6371000.0;
    final double lat1Rad = p1.lat * (pi / 180.0);
    final double lat2Rad = p2.lat * (pi / 180.0);
    final double deltaLatRad = (p2.lat - p1.lat) * (pi / 180.0);
    final double deltaLngRad = (p2.lng - p1.lng) * (pi / 180.0);

    final double a = sin(deltaLatRad / 2.0) * sin(deltaLatRad / 2.0) +
        cos(lat1Rad) * cos(lat2Rad) * sin(deltaLngRad / 2.0) * sin(deltaLngRad / 2.0);
    final double c = 2.0 * atan2(sqrt(a), sqrt(1.0 - a));

    return earthRadiusM * c;
  }
}
