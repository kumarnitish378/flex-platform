library;

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:smart_cab_api/smart_cab_api.dart' as api;

import '../../core/session_controller.dart';

final Provider<RideRequestRepository> rideRequestRepositoryProvider =
    Provider<RideRequestRepository>((Ref ref) {
  return RideRequestRepository(
    api.EmployeeApi(ref.read(dioProvider), api.standardSerializers),
  );
});

class RideRequestException implements Exception {
  const RideRequestException(this.message, {this.statusCode});

  final String message;
  final int? statusCode;

  @override
  String toString() => message;
}

class RideRequestRepository {
  RideRequestRepository(this._api);

  final api.EmployeeApi _api;

  /// Fetch all ride requests belonging to the signed in employee.
  Future<List<api.RideRequest>> getMyRequests() async {
    try {
      final Response<api.RideRequestsMineGet200Response> response =
          await _api.rideRequestsMineGet();
      final List<api.RideRequest>? items = response.data?.items?.toList();
      return items ?? <api.RideRequest>[];
    } on DioException catch (e) {
      throw RideRequestException(
        e.response?.data?.toString() ?? 'Failed to load ride requests',
        statusCode: e.response?.statusCode,
      );
    }
  }

  /// Create a new ride request.
  Future<api.RideRequest> createRequest(api.RideRequestInput input) async {
    try {
      final Response<api.RideRequest> response = await _api.rideRequestsPost(
        rideRequestInput: input,
      );
      final api.RideRequest? request = response.data;
      if (request == null) {
        throw const RideRequestException('Empty response from server');
      }
      return request;
    } on DioException catch (e) {
      final String msg = e.response?.data != null ? e.response!.data.toString() : 'Failed to create ride request';
      throw RideRequestException(msg, statusCode: e.response?.statusCode);
    }
  }

  /// Get details for a specific ride request.
  Future<api.RideRequest> getRequest(String requestId) async {
    try {
      final Response<api.RideRequest> response = await _api.rideRequestsRequestIdGet(
        requestId: requestId,
      );
      final api.RideRequest? request = response.data;
      if (request == null) {
        throw const RideRequestException('Request not found');
      }
      return request;
    } on DioException catch (e) {
      throw RideRequestException(
        'Failed to fetch request $requestId',
        statusCode: e.response?.statusCode,
      );
    }
  }

  /// Cancel an active ride request.
  Future<api.RideRequest> cancelRequest(String requestId, {String? reason}) async {
    try {
      final api.RideRequestsRequestIdCancelPostRequest body =
          api.RideRequestsRequestIdCancelPostRequest(
        (api.RideRequestsRequestIdCancelPostRequestBuilder b) =>
            b..reason = reason ?? 'Cancelled by user',
      );
      final Response<api.RideRequest> response =
          await _api.rideRequestsRequestIdCancelPost(
        requestId: requestId,
        rideRequestsRequestIdCancelPostRequest: body,
      );
      final api.RideRequest? request = response.data;
      if (request == null) {
        throw const RideRequestException('Failed to cancel request');
      }
      return request;
    } on DioException catch (e) {
      throw RideRequestException(
        'Failed to cancel request $requestId',
        statusCode: e.response?.statusCode,
      );
    }
  }
}
