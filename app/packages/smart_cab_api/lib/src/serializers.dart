//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_import

import 'package:one_of_serializer/any_of_serializer.dart';
import 'package:one_of_serializer/one_of_serializer.dart';
import 'package:built_collection/built_collection.dart';
import 'package:built_value/json_object.dart';
import 'package:built_value/serializer.dart';
import 'package:built_value/standard_json_plugin.dart';
import 'package:built_value/iso_8601_date_time_serializer.dart';
import 'package:smart_cab_api/src/date_serializer.dart';
import 'package:smart_cab_api/src/model/date.dart';

import 'package:smart_cab_api/src/model/admin_clients_client_id_employees_get200_response.dart';
import 'package:smart_cab_api/src/model/admin_clients_client_id_offices_get200_response.dart';
import 'package:smart_cab_api/src/model/admin_clients_get200_response.dart';
import 'package:smart_cab_api/src/model/admin_drivers_get200_response.dart';
import 'package:smart_cab_api/src/model/admin_mode_settings_get200_response.dart';
import 'package:smart_cab_api/src/model/admin_users_invite_post_request.dart';
import 'package:smart_cab_api/src/model/admin_vehicles_get200_response.dart';
import 'package:smart_cab_api/src/model/admin_zones_get200_response.dart';
import 'package:smart_cab_api/src/model/alert.dart';
import 'package:smart_cab_api/src/model/alerts_get200_response.dart';
import 'package:smart_cab_api/src/model/auth_refresh_post_request.dart';
import 'package:smart_cab_api/src/model/billing_export.dart';
import 'package:smart_cab_api/src/model/billing_export_rows_inner.dart';
import 'package:smart_cab_api/src/model/billing_export_summary.dart';
import 'package:smart_cab_api/src/model/billing_export_treatment.dart';
import 'package:smart_cab_api/src/model/candidate.dart';
import 'package:smart_cab_api/src/model/candidate_added_minutes_existing_inner.dart';
import 'package:smart_cab_api/src/model/client.dart';
import 'package:smart_cab_api/src/model/client_input.dart';
import 'package:smart_cab_api/src/model/client_policy.dart';
import 'package:smart_cab_api/src/model/client_policy_all_of_effective.dart';
import 'package:smart_cab_api/src/model/client_policy_input.dart';
import 'package:smart_cab_api/src/model/device_register.dart';
import 'package:smart_cab_api/src/model/direction.dart';
import 'package:smart_cab_api/src/model/dispatch_assign_post_request.dart';
import 'package:smart_cab_api/src/model/dispatch_automation_get200_response.dart';
import 'package:smart_cab_api/src/model/dispatch_automation_put_request.dart';
import 'package:smart_cab_api/src/model/dispatch_hints_get200_response.dart';
import 'package:smart_cab_api/src/model/dispatch_requests_get200_response.dart';
import 'package:smart_cab_api/src/model/dispatch_requests_request_id_candidates_get200_response.dart';
import 'package:smart_cab_api/src/model/dispatch_suggestions_get200_response.dart';
import 'package:smart_cab_api/src/model/dispatch_suggestions_suggestion_id_decision_post_request.dart';
import 'package:smart_cab_api/src/model/dispatch_trips_get200_response.dart';
import 'package:smart_cab_api/src/model/dispatch_vehicles_get200_response.dart';
import 'package:smart_cab_api/src/model/driver.dart';
import 'package:smart_cab_api/src/model/driver_duty_post_request.dart';
import 'package:smart_cab_api/src/model/driver_input.dart';
import 'package:smart_cab_api/src/model/driver_issues_post_request.dart';
import 'package:smart_cab_api/src/model/driver_trips_get200_response.dart';
import 'package:smart_cab_api/src/model/driver_trips_trip_id_start_post_request.dart';
import 'package:smart_cab_api/src/model/duty_state.dart';
import 'package:smart_cab_api/src/model/duty_state_gps.dart';
import 'package:smart_cab_api/src/model/duty_state_mqtt.dart';
import 'package:smart_cab_api/src/model/employee.dart';
import 'package:smart_cab_api/src/model/employee_input.dart';
import 'package:smart_cab_api/src/model/error.dart';
import 'package:smart_cab_api/src/model/escort_confirmation.dart';
import 'package:smart_cab_api/src/model/impact.dart';
import 'package:smart_cab_api/src/model/impact_affected_requests_inner.dart';
import 'package:smart_cab_api/src/model/import_report.dart';
import 'package:smart_cab_api/src/model/import_report_errors_inner.dart';
import 'package:smart_cab_api/src/model/lat_lng.dart';
import 'package:smart_cab_api/src/model/location_ping.dart';
import 'package:smart_cab_api/src/model/me.dart';
import 'package:smart_cab_api/src/model/me_roles_inner.dart';
import 'package:smart_cab_api/src/model/mode_resolution.dart';
import 'package:smart_cab_api/src/model/mode_setting.dart';
import 'package:smart_cab_api/src/model/mode_setting_input.dart';
import 'package:smart_cab_api/src/model/office.dart';
import 'package:smart_cab_api/src/model/office_input.dart';
import 'package:smart_cab_api/src/model/operations_report.dart';
import 'package:smart_cab_api/src/model/operations_report_distance.dart';
import 'package:smart_cab_api/src/model/operations_report_optimizer.dart';
import 'package:smart_cab_api/src/model/operations_report_overrides.dart';
import 'package:smart_cab_api/src/model/operations_report_period.dart';
import 'package:smart_cab_api/src/model/operations_report_pooling.dart';
import 'package:smart_cab_api/src/model/operations_report_requests.dart';
import 'package:smart_cab_api/src/model/operations_report_suggestions.dart';
import 'package:smart_cab_api/src/model/operations_report_wait.dart';
import 'package:smart_cab_api/src/model/otp_request.dart';
import 'package:smart_cab_api/src/model/otp_verify.dart';
import 'package:smart_cab_api/src/model/override_input.dart';
import 'package:smart_cab_api/src/model/override_result.dart';
import 'package:smart_cab_api/src/model/reason_code.dart';
import 'package:smart_cab_api/src/model/request_hint.dart';
import 'package:smart_cab_api/src/model/request_status.dart';
import 'package:smart_cab_api/src/model/ride_request.dart';
import 'package:smart_cab_api/src/model/ride_request_assignment.dart';
import 'package:smart_cab_api/src/model/ride_request_input.dart';
import 'package:smart_cab_api/src/model/ride_requests_mine_get200_response.dart';
import 'package:smart_cab_api/src/model/ride_requests_request_id_cancel_post_request.dart';
import 'package:smart_cab_api/src/model/ride_requests_request_id_rating_post_request.dart';
import 'package:smart_cab_api/src/model/role.dart';
import 'package:smart_cab_api/src/model/sim_clock.dart';
import 'package:smart_cab_api/src/model/simctl_optimizer_put_request.dart';
import 'package:smart_cab_api/src/model/simctl_release_post200_response.dart';
import 'package:smart_cab_api/src/model/simctl_release_post_request.dart';
import 'package:smart_cab_api/src/model/simctl_reset_post_request.dart';
import 'package:smart_cab_api/src/model/sos_post_request.dart';
import 'package:smart_cab_api/src/model/stop_status.dart';
import 'package:smart_cab_api/src/model/suggestion.dart';
import 'package:smart_cab_api/src/model/suggestion_decision_result.dart';
import 'package:smart_cab_api/src/model/test_login_request.dart';
import 'package:smart_cab_api/src/model/token_pair.dart';
import 'package:smart_cab_api/src/model/tracker_type.dart';
import 'package:smart_cab_api/src/model/trip.dart';
import 'package:smart_cab_api/src/model/trip_escort.dart';
import 'package:smart_cab_api/src/model/trip_report.dart';
import 'package:smart_cab_api/src/model/trip_rider.dart';
import 'package:smart_cab_api/src/model/trip_status.dart';
import 'package:smart_cab_api/src/model/trip_stop.dart';
import 'package:smart_cab_api/src/model/urgency.dart';
import 'package:smart_cab_api/src/model/vehicle.dart';
import 'package:smart_cab_api/src/model/vehicle_input.dart';
import 'package:smart_cab_api/src/model/vehicle_live.dart';
import 'package:smart_cab_api/src/model/vehicle_status.dart';
import 'package:smart_cab_api/src/model/vehicle_type.dart';
import 'package:smart_cab_api/src/model/zone.dart';
import 'package:smart_cab_api/src/model/zone_input.dart';
import 'package:smart_cab_api/src/model/zone_update.dart';

part 'serializers.g.dart';

@SerializersFor([
  AdminClientsClientIdEmployeesGet200Response,
  AdminClientsClientIdOfficesGet200Response,
  AdminClientsGet200Response,
  AdminDriversGet200Response,
  AdminModeSettingsGet200Response,
  AdminUsersInvitePostRequest,
  AdminVehiclesGet200Response,
  AdminZonesGet200Response,
  Alert,
  AlertsGet200Response,
  AuthRefreshPostRequest,
  BillingExport,
  BillingExportRowsInner,
  BillingExportSummary,
  BillingExportTreatment,
  Candidate,
  CandidateAddedMinutesExistingInner,
  Client,
  ClientInput,$ClientInput,
  ClientPolicy,
  ClientPolicyAllOfEffective,
  ClientPolicyInput,$ClientPolicyInput,
  DeviceRegister,
  Direction,
  DispatchAssignPostRequest,
  DispatchAutomationGet200Response,
  DispatchAutomationPutRequest,
  DispatchHintsGet200Response,
  DispatchRequestsGet200Response,
  DispatchRequestsRequestIdCandidatesGet200Response,
  DispatchSuggestionsGet200Response,
  DispatchSuggestionsSuggestionIdDecisionPostRequest,
  DispatchTripsGet200Response,
  DispatchVehiclesGet200Response,
  Driver,
  DriverDutyPostRequest,
  DriverInput,$DriverInput,
  DriverIssuesPostRequest,
  DriverTripsGet200Response,
  DriverTripsTripIdStartPostRequest,
  DutyState,
  DutyStateGps,
  DutyStateMqtt,
  Employee,
  EmployeeInput,$EmployeeInput,
  Error,
  EscortConfirmation,
  Impact,
  ImpactAffectedRequestsInner,
  ImportReport,
  ImportReportErrorsInner,
  LatLng,
  LocationPing,
  Me,
  MeRolesInner,
  ModeResolution,
  ModeSetting,
  ModeSettingInput,$ModeSettingInput,
  Office,
  OfficeInput,$OfficeInput,
  OperationsReport,
  OperationsReportDistance,
  OperationsReportOptimizer,
  OperationsReportOverrides,
  OperationsReportPeriod,
  OperationsReportPooling,
  OperationsReportRequests,
  OperationsReportSuggestions,
  OperationsReportWait,
  OtpRequest,
  OtpVerify,
  OverrideInput,
  OverrideResult,
  ReasonCode,
  RequestHint,
  RequestStatus,
  RideRequest,
  RideRequestAssignment,
  RideRequestInput,
  RideRequestsMineGet200Response,
  RideRequestsRequestIdCancelPostRequest,
  RideRequestsRequestIdRatingPostRequest,
  Role,
  SimClock,
  SimctlOptimizerPutRequest,
  SimctlReleasePost200Response,
  SimctlReleasePostRequest,
  SimctlResetPostRequest,
  SosPostRequest,
  StopStatus,
  Suggestion,
  SuggestionDecisionResult,
  TestLoginRequest,
  TokenPair,
  TrackerType,
  Trip,
  TripEscort,
  TripReport,
  TripRider,
  TripStatus,
  TripStop,
  Urgency,
  Vehicle,$Vehicle,
  VehicleInput,$VehicleInput,
  VehicleLive,
  VehicleStatus,
  VehicleType,
  Zone,
  ZoneInput,$ZoneInput,
  ZoneUpdate,
])
Serializers serializers = (_$serializers.toBuilder()
      ..addBuilderFactory(
        const FullType(BuiltList, [FullType(RequestStatus)]),
        () => ListBuilder<RequestStatus>(),
      )
      ..addBuilderFactory(
        const FullType(BuiltList, [FullType(TripStatus)]),
        () => ListBuilder<TripStatus>(),
      )
      ..addBuilderFactory(
        const FullType(BuiltMap, [FullType(String), FullType.nullable(JsonObject)]),
        () => MapBuilder<String, JsonObject>(),
      )
      ..addBuilderFactory(
        const FullType(BuiltList, [FullType(LocationPing)]),
        () => ListBuilder<LocationPing>(),
      )
      ..addBuilderFactory(
        const FullType(BuiltMap, [FullType(String), FullType(JsonObject)]),
        () => MapBuilder<String, JsonObject>(),
      )
      ..add(ClientInput.serializer)
      ..add(ClientPolicyInput.serializer)
      ..add(DriverInput.serializer)
      ..add(EmployeeInput.serializer)
      ..add(ModeSettingInput.serializer)
      ..add(OfficeInput.serializer)
      ..add(Vehicle.serializer)
      ..add(VehicleInput.serializer)
      ..add(ZoneInput.serializer)
      ..add(const OneOfSerializer())
      ..add(const AnyOfSerializer())
      ..add(const DateSerializer())
      ..add(Iso8601DateTimeSerializer())
    ).build();

Serializers standardSerializers =
    (serializers.toBuilder()..addPlugin(StandardJsonPlugin())).build();
