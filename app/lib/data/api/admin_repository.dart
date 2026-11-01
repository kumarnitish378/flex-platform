library;

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
  AdminRepository(this._api, this._reportsApi);

  final api.AdminApi _api;
  final api.ReportsApi _reportsApi;

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
      final Response<api.AdminClientsGet200Response> response =
          await _api.adminClientsGet();
      return response.data?.items.toList() ?? <api.Client>[];
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

  /// Fetch full operations report (A19).
  Future<api.OperationsReport?> getOperationsReport({
    required DateTime from,
    required DateTime to,
    String? clientId,
  }) async {
    try {
      final Response<api.OperationsReport> response =
          await _reportsApi.reportsOperationsGet(
        from: api.Date(from.year, from.month, from.day),
        to: api.Date(to.year, to.month, to.day),
        clientId: clientId,
      );
      return response.data;
    } on DioException catch (e) {
      throw AdminException(
        e.response?.data?.toString() ?? 'Failed to fetch operations report',
        statusCode: e.response?.statusCode,
      );
    }
  }

  /// Fetch billing export quantities and rules (A19).
  Future<api.BillingExport?> getBillingExport({
    required String month,
    String? clientId,
  }) async {
    try {
      final Response<api.BillingExport> response =
          await _reportsApi.reportsBillingGet(
        month: month,
        clientId: clientId,
      );
      return response.data;
    } on DioException catch (e) {
      throw AdminException(
        e.response?.data?.toString() ?? 'Failed to fetch billing export',
        statusCode: e.response?.statusCode,
      );
    }
  }

  /// Fetch billing export CSV content (A19).
  Future<String> getBillingExportCsv({
    required String month,
    String? clientId,
  }) async {
    try {
      final Response<dynamic> response = await _reportsApi.reportsBillingGet(
        month: month,
        clientId: clientId,
        format: 'csv',
      );
      return response.data?.toString() ?? '';
    } on DioException catch (e) {
      throw AdminException(
        e.response?.data?.toString() ?? 'Failed to download billing CSV export',
        statusCode: e.response?.statusCode,
      );
    }
  }

  /// Fetch operations report CSV content (A19).
  Future<String> getOperationsReportCsv({
    required DateTime from,
    required DateTime to,
    String? clientId,
  }) async {
    try {
      final Response<dynamic> response = await _reportsApi.reportsOperationsGet(
        from: api.Date(from.year, from.month, from.day),
        to: api.Date(to.year, to.month, to.day),
        clientId: clientId,
        format: 'csv',
      );
      return response.data?.toString() ?? '';
    } on DioException catch (e) {
      throw AdminException(
        e.response?.data?.toString() ?? 'Failed to download operations report CSV',
        statusCode: e.response?.statusCode,
      );
    }
  }
}

final Provider<AdminRepository> adminRepositoryProvider =
    Provider<AdminRepository>((Ref ref) {
  final Dio dio = ref.read(dioProvider);
  return AdminRepository(
    api.AdminApi(dio, api.standardSerializers),
    api.ReportsApi(dio, api.standardSerializers),
  );
});
