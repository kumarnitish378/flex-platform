library;

import 'package:built_collection/built_collection.dart';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:smart_cab_api/smart_cab_api.dart' as api;

import '../../core/session_controller.dart';

class DriverTripsException implements Exception {
  const DriverTripsException(this.message, {this.statusCode});

  final String message;
  final int? statusCode;

  @override
  String toString() => message;
}

class DriverTripsRepository {
  DriverTripsRepository(this._api);

  final api.DriverApi _api;

  /// Fetch all assigned trips for the driver.
  Future<List<api.Trip>> getTrips() async {
    try {
      final Response<BuiltList<api.Trip>> response = await _api.driverTripsGet();
      return response.data?.toList() ?? <api.Trip>[];
    } on DioException catch (e) {
      throw DriverTripsException(
        e.response?.data?.toString() ?? 'Failed to fetch driver trips',
        statusCode: e.response?.statusCode,
      );
    }
  }

  /// Fetch details for a specific trip.
  Future<api.Trip> getTripDetail(String tripId) async {
    try {
      final List<api.Trip> allTrips = await getTrips();
      final api.Trip? trip = allTrips.cast<api.Trip?>().firstWhere(
            (api.Trip? t) => t?.id == tripId,
            orElse: () => null,
          );
      if (trip == null) {
        throw DriverTripsException('Trip $tripId not found');
      }
      return trip;
    } on DioException catch (e) {
      throw DriverTripsException(
        'Failed to fetch trip $tripId',
        statusCode: e.response?.statusCode,
      );
    }
  }

  /// Start a trip.
  Future<api.Trip> startTrip(String tripId) async {
    try {
      final api.DriverTripsTripIdStartPostRequest request =
          api.DriverTripsTripIdStartPostRequest(
        (api.DriverTripsTripIdStartPostRequestBuilder b) =>
            b..clientEventId = 'evt_start_$tripId',
      );
      final Response<api.Trip> response = await _api.driverTripsTripIdStartPost(
        tripId: tripId,
        driverTripsTripIdStartPostRequest: request,
      );
      final api.Trip? trip = response.data;
      if (trip == null) {
        throw const DriverTripsException('Failed to start trip');
      }
      return trip;
    } on DioException catch (e) {
      throw DriverTripsException(
        'Failed to start trip $tripId',
        statusCode: e.response?.statusCode,
      );
    }
  }

  /// Report a driver issue/incident.
  Future<void> reportIssue({
    required String issueType,
    String? note,
  }) async {
    try {
      api.DriverIssuesPostRequestTypeEnum enumType;
      switch (issueType) {
        case 'accident':
          enumType = api.DriverIssuesPostRequestTypeEnum.accident;
          break;
        case 'traffic_delay':
        case 'traffic_block':
          enumType = api.DriverIssuesPostRequestTypeEnum.trafficBlock;
          break;
        case 'rider_issue':
          enumType = api.DriverIssuesPostRequestTypeEnum.riderIssue;
          break;
        case 'other':
          enumType = api.DriverIssuesPostRequestTypeEnum.other;
          break;
        case 'breakdown':
        default:
          enumType = api.DriverIssuesPostRequestTypeEnum.breakdown;
          break;
      }

      final api.DriverIssuesPostRequest request = api.DriverIssuesPostRequest(
        (api.DriverIssuesPostRequestBuilder b) => b
          ..type = enumType
          ..note = note,
      );
      await _api.driverIssuesPost(driverIssuesPostRequest: request);
    } on DioException catch (e) {
      throw DriverTripsException(
        'Failed to report issue',
        statusCode: e.response?.statusCode,
      );
    }
  }
}

final Provider<DriverTripsRepository> driverTripsRepositoryProvider =
    Provider<DriverTripsRepository>((Ref ref) {
  return DriverTripsRepository(
    api.DriverApi(ref.read(dioProvider), api.standardSerializers),
  );
});
