library;

import 'package:built_collection/built_collection.dart';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:smart_cab_api/smart_cab_api.dart' as api;

import '../../core/session_controller.dart';

class SupervisorException implements Exception {
  const SupervisorException(this.message, {this.statusCode});

  final String message;
  final int? statusCode;

  @override
  String toString() => message;
}

class SupervisorRepository {
  SupervisorRepository(this._dispatchApi, this._alertsApi);

  final api.DispatchApi _dispatchApi;
  final api.AlertsApi _alertsApi;

  /// Fetch live vehicles for map display.
  Future<List<api.VehicleLive>> getLiveVehicles() async {
    try {
      final Response<BuiltList<api.VehicleLive>> response =
          await _dispatchApi.dispatchVehiclesGet();
      return response.data?.toList() ?? <api.VehicleLive>[];
    } on DioException catch (e) {
      throw SupervisorException(
        e.response?.data?.toString() ?? 'Failed to fetch live vehicles',
        statusCode: e.response?.statusCode,
      );
    }
  }

  /// Fetch candidate cabs for a request.
  Future<List<api.Candidate>> getCandidates(String requestId) async {
    try {
      final Response<BuiltList<api.Candidate>> response =
          await _dispatchApi.dispatchRequestsRequestIdCandidatesGet(requestId: requestId);
      return response.data?.toList() ?? <api.Candidate>[];
    } on DioException catch (e) {
      throw SupervisorException(
        'Failed to fetch candidates for request $requestId',
        statusCode: e.response?.statusCode,
      );
    }
  }

  /// Fetch top scored suggestions for a request (A13).
  Future<List<api.Candidate>> getSuggestions(String requestId) async {
    try {
      final Response<BuiltList<api.Candidate>> response =
          await _dispatchApi.dispatchRequestsRequestIdSuggestionsGet(requestId: requestId);
      return response.data?.toList() ?? <api.Candidate>[];
    } on DioException catch (e) {
      throw SupervisorException(
        'Failed to fetch suggestions for request $requestId',
        statusCode: e.response?.statusCode,
      );
    }
  }

  /// Submit decision for a suggestion (approve, choose_other, or reject) (A13).
  Future<void> submitSuggestionDecision(
    String suggestionId, {
    required String decision,
    String? vehicleId,
    String? reasonCode,
    String? note,
  }) async {
    try {
      api.DispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnum decisionEnum;
      switch (decision) {
        case 'choose_other':
          decisionEnum =
              api.DispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnum.chooseOther;
          break;
        case 'reject':
          decisionEnum =
              api.DispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnum.reject;
          break;
        case 'approve':
        default:
          decisionEnum =
              api.DispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnum.approve;
          break;
      }

      api.ReasonCode? codeEnum;
      if (reasonCode != null) {
        switch (reasonCode) {
          case 'driver_issue':
            codeEnum = api.ReasonCode.driverIssue;
            break;
          case 'local_knowledge':
            codeEnum = api.ReasonCode.localKnowledge;
            break;
          case 'client_request':
            codeEnum = api.ReasonCode.clientRequest;
            break;
          case 'traffic':
            codeEnum = api.ReasonCode.traffic;
            break;
          case 'vehicle_issue':
            codeEnum = api.ReasonCode.vehicleIssue;
            break;
          case 'safety':
            codeEnum = api.ReasonCode.safety;
            break;
          case 'other':
          default:
            codeEnum = api.ReasonCode.other;
            break;
        }
      }

      final api.DispatchSuggestionsSuggestionIdDecisionPostRequest request =
          api.DispatchSuggestionsSuggestionIdDecisionPostRequest(
        (api.DispatchSuggestionsSuggestionIdDecisionPostRequestBuilder b) => b
          ..decision = decisionEnum
          ..vehicleId = vehicleId
          ..reasonCode = codeEnum
          ..note = note,
      );

      await _dispatchApi.dispatchSuggestionsSuggestionIdDecisionPost(
        suggestionId: suggestionId,
        dispatchSuggestionsSuggestionIdDecisionPostRequest: request,
      );
    } on DioException catch (e) {
      throw SupervisorException(
        'Failed to submit suggestion decision for $suggestionId',
        statusCode: e.response?.statusCode,
      );
    }
  }

  /// Manually assign a request to a vehicle or trip.
  Future<api.Trip> assignRequest({
    required String requestId,
    String? vehicleId,
    String? tripId,
  }) async {
    try {
      final api.DispatchAssignPostRequest request = api.DispatchAssignPostRequest(
        (api.DispatchAssignPostRequestBuilder b) => b
          ..requestId = requestId
          ..vehicleId = vehicleId
          ..tripId = tripId,
      );
      final Response<api.Trip> response = await _dispatchApi.dispatchAssignPost(
        dispatchAssignPostRequest: request,
      );
      final api.Trip? trip = response.data;
      if (trip == null) {
        throw const SupervisorException('Failed to assign request');
      }
      return trip;
    } on DioException catch (e) {
      throw SupervisorException(
        'Failed to assign request $requestId',
        statusCode: e.response?.statusCode,
      );
    }
  }

  /// Fetch alerts and SOS notifications.
  Future<List<api.Alert>> getAlerts() async {
    try {
      final Response<BuiltList<api.Alert>> response = await _alertsApi.alertsGet();
      return response.data?.toList() ?? <api.Alert>[];
    } on DioException catch (e) {
      throw SupervisorException(
        e.response?.data?.toString() ?? 'Failed to fetch alerts',
        statusCode: e.response?.statusCode,
      );
    }
  }

  /// Acknowledge an alert.
  Future<void> acknowledgeAlert(String alertId) async {
    try {
      await _alertsApi.alertsAlertIdActionPost(
        alertId: alertId,
        action: 'acknowledge',
      );
    } on DioException catch (e) {
      throw SupervisorException(
        'Failed to acknowledge alert $alertId',
        statusCode: e.response?.statusCode,
      );
    }
  }

  /// Resolve an alert.
  Future<void> resolveAlert(String alertId) async {
    try {
      await _alertsApi.alertsAlertIdActionPost(
        alertId: alertId,
        action: 'resolve',
      );
    } on DioException catch (e) {
      throw SupervisorException(
        'Failed to resolve alert $alertId',
        statusCode: e.response?.statusCode,
      );
    }
  }
}

final Provider<SupervisorRepository> supervisorRepositoryProvider =
    Provider<SupervisorRepository>((Ref ref) {
  final Dio dio = ref.read(dioProvider);
  return SupervisorRepository(
    api.DispatchApi(dio, api.standardSerializers),
    api.AlertsApi(dio, api.standardSerializers),
  );
});
