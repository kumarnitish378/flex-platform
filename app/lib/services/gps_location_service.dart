import 'dart:math';

import 'package:smart_cab_api/smart_cab_api.dart' as api;

/// Service managing Driver GPS location filtering and heartbeat publishing (A09 / mqtt-topics.md).
///
/// Rules:
/// - Distance Filter: Publishes if moved ≥ [distanceFilterM] (default 5 m) since last published fix.
/// - Heartbeat: Publishes a heartbeat ping if stationary for ≥ [heartbeatSeconds] (default 60 s).
/// - Off duty: No GPS published.
class GpsLocationService {
  GpsLocationService({
    this.distanceFilterM = 5.0,
    this.heartbeatSeconds = 60,
  });

  final double distanceFilterM;
  final int heartbeatSeconds;

  api.LatLng? _lastPublishedFix;
  DateTime? _lastPublishedTime;

  api.LatLng? get lastPublishedFix => _lastPublishedFix;
  DateTime? get lastPublishedTime => _lastPublishedTime;

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

  void _recordPublish(api.LatLng fix, DateTime time) {
    _lastPublishedFix = fix;
    _lastPublishedTime = time;
  }

  void reset() {
    _lastPublishedFix = null;
    _lastPublishedTime = null;
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
