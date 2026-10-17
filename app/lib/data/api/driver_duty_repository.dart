library;

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:smart_cab_api/smart_cab_api.dart' as api;

import '../../core/session_controller.dart';

class DriverDutyException implements Exception {
  const DriverDutyException(this.message, {this.statusCode});

  final String message;
  final int? statusCode;

  @override
  String toString() => message;
}

class DriverDutyRepository {
  DriverDutyRepository(this._api);

  final api.DriverApi _api;

  /// Toggle on/off duty status.
  Future<api.DutyState> setDutyStatus({
    required bool onDuty,
    String? vehicleId,
  }) async {
    try {
      final api.DriverDutyPostRequest request = api.DriverDutyPostRequest(
        (api.DriverDutyPostRequestBuilder b) => b
          ..onDuty = onDuty
          ..vehicleId = vehicleId,
      );
      final Response<api.DutyState> response = await _api.driverDutyPost(
        driverDutyPostRequest: request,
      );
      final api.DutyState? state = response.data;
      if (state == null) {
        throw const DriverDutyException('Empty response from duty endpoint');
      }
      return state;
    } on DioException catch (e) {
      throw DriverDutyException(
        e.response?.data?.toString() ?? 'Failed to update duty status',
        statusCode: e.response?.statusCode,
      );
    }
  }
}

final Provider<DriverDutyRepository> driverDutyRepositoryProvider =
    Provider<DriverDutyRepository>((Ref ref) {
  return DriverDutyRepository(
    api.DriverApi(ref.read(dioProvider), api.standardSerializers),
  );
});
