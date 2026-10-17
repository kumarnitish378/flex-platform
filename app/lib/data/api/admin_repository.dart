library;

import 'package:built_collection/built_collection.dart';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:smart_cab_api/smart_cab_api.dart' as api;

import '../../core/session_controller.dart';

class AdminException implements Exception {
  const AdminException(this.message, {this.statusCode});

  final String message;
  final int? statusCode;

  @override
  String toString() => message;
}

class AdminRepository {
  AdminRepository(this._api);

  final api.AdminApi _api;

  /// Fetch vehicles list.
  Future<List<api.Vehicle>> getVehicles() async {
    try {
      final Response<api.AdminVehiclesGet200Response> response =
          await _api.adminVehiclesGet();
      return response.data?.items?.toList() ?? <api.Vehicle>[];
    } on DioException catch (e) {
      throw AdminException(
        e.response?.data?.toString() ?? 'Failed to fetch vehicles',
        statusCode: e.response?.statusCode,
      );
    }
  }

  /// Create a vehicle.
  Future<api.Vehicle> createVehicle(api.VehicleInput input) async {
    try {
      final Response<api.Vehicle> response =
          await _api.adminVehiclesPost(vehicleInput: input);
      final api.Vehicle? v = response.data;
      if (v == null) {
        throw const AdminException('Failed to create vehicle');
      }
      return v;
    } on DioException catch (e) {
      throw AdminException(
        e.response?.data?.toString() ?? 'Failed to create vehicle',
        statusCode: e.response?.statusCode,
      );
    }
  }

  /// Fetch drivers list.
  Future<List<api.Driver>> getDrivers() async {
    try {
      final Response<api.AdminDriversGet200Response> response =
          await _api.adminDriversGet();
      return response.data?.items?.toList() ?? <api.Driver>[];
    } on DioException catch (e) {
      throw AdminException(
        e.response?.data?.toString() ?? 'Failed to fetch drivers',
        statusCode: e.response?.statusCode,
      );
    }
  }

  /// Fetch clients list.
  Future<List<api.Client>> getClients() async {
    try {
      final Response<BuiltList<api.Client>> response = await _api.adminClientsGet();
      return response.data?.toList() ?? <api.Client>[];
    } on DioException catch (e) {
      throw AdminException(
        e.response?.data?.toString() ?? 'Failed to fetch clients',
        statusCode: e.response?.statusCode,
      );
    }
  }

  /// Fetch employees for a client.
  Future<List<api.Employee>> getEmployees(String clientId) async {
    try {
      final Response<api.AdminClientsClientIdEmployeesGet200Response> response =
          await _api.adminClientsClientIdEmployeesGet(clientId: clientId);
      return response.data?.items?.toList() ?? <api.Employee>[];
    } on DioException catch (e) {
      throw AdminException(
        e.response?.data?.toString() ?? 'Failed to fetch employees',
        statusCode: e.response?.statusCode,
      );
    }
  }
}

final Provider<AdminRepository> adminRepositoryProvider =
    Provider<AdminRepository>((Ref ref) {
  return AdminRepository(
    api.AdminApi(ref.read(dioProvider), api.standardSerializers),
  );
});
