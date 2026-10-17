library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Push Notification payload.
class PushNotification {
  const PushNotification({
    required this.id,
    required this.title,
    required this.body,
    this.targetRoute,
    this.data = const <String, dynamic>{},
  });

  factory PushNotification.fromJson(Map<String, dynamic> json) {
    return PushNotification(
      id: json['id'] as String? ?? '',
      title: json['title'] as String? ?? '',
      body: json['body'] as String? ?? '',
      targetRoute: json['target_route'] as String?,
      data: (json['data'] as Map<String, dynamic>?) ?? <String, dynamic>{},
    );
  }

  final String id;
  final String title;
  final String body;
  final String? targetRoute;
  final Map<String, dynamic> data;
}

/// Interface/Service for Push Notifications (FCM / Local / Fallback) (A07).
class PushNotificationService {
  PushNotificationService();

  /// Handles tap on a notification and returns target navigation route.
  String? handleNotificationTap(PushNotification notification) {
    if (notification.targetRoute != null && notification.targetRoute!.isNotEmpty) {
      return notification.targetRoute;
    }
    // Fallback routes based on notification data
    final String? tripId = notification.data['trip_id'] as String?;
    if (tripId != null && tripId.isNotEmpty) {
      return '/employee/trip/$tripId';
    }
    final String? requestId = notification.data['request_id'] as String?;
    if (requestId != null && requestId.isNotEmpty) {
      return '/employee/request/$requestId';
    }
    return null;
  }
}

final Provider<PushNotificationService> pushNotificationServiceProvider =
    Provider<PushNotificationService>((Ref ref) => PushNotificationService());
