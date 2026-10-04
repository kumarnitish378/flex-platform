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
import 'package:smart_cab_api/src/model/admin_drivers_get200_response.dart';
import 'package:smart_cab_api/src/model/admin_users_invite_post_request.dart';
import 'package:smart_cab_api/src/model/admin_vehicles_get200_response.dart';
import 'package:smart_cab_api/src/model/alert.dart';
import 'package:smart_cab_api/src/model/auth_refresh_post_request.dart';
import 'package:smart_cab_api/src/model/candidate.dart';
import 'package:smart_cab_api/src/model/candidate_added_minutes_existing_inner.dart';
import 'package:smart_cab_api/src/model/client.dart';
import 'package:smart_cab_api/src/model/client_input.dart';
import 'package:smart_cab_api/src/model/device_register.dart';
import 'package:smart_cab_api/src/model/direction.dart';
import 'package:smart_cab_api/src/model/dispatch_assign_post_request.dart';
import 'package:smart_cab_api/src/model/dispatch_automation_get200_response.dart';
import 'package:smart_cab_api/src/model/dispatch_automation_put_request.dart';
import 'package:smart_cab_api/src/model/dispatch_suggestions_suggestion_id_decision_post_request.dart';
import 'package:smart_cab_api/src/model/dispatch_trips_get200_response.dart';
import 'package:smart_cab_api/src/model/driver.dart';
import 'package:smart_cab_api/src/model/driver_duty_post_request.dart';
import 'package:smart_cab_api/src/model/driver_input.dart';
import 'package:smart_cab_api/src/model/driver_issues_post_request.dart';
import 'package:smart_cab_api/src/model/driver_trips_trip_id_start_post_request.dart';
import 'package:smart_cab_api/src/model/duty_state.dart';
import 'package:smart_cab_api/src/model/duty_state_mqtt.dart';
import 'package:smart_cab_api/src/model/employee.dart';
import 'package:smart_cab_api/src/model/employee_input.dart';
import 'package:smart_cab_api/src/model/error.dart';
import 'package:smart_cab_api/src/model/impact.dart';
import 'package:smart_cab_api/src/model/impact_affected_requests_inner.dart';
import 'package:smart_cab_api/src/model/import_report.dart';
import 'package:smart_cab_api/src/model/import_report_errors_inner.dart';
import 'package:smart_cab_api/src/model/lat_lng.dart';
import 'package:smart_cab_api/src/model/location_ping.dart';
import 'package:smart_cab_api/src/model/me.dart';
import 'package:smart_cab_api/src/model/me_roles_inner.dart';
import 'package:smart_cab_api/src/model/mode_setting.dart';
import 'package:smart_cab_api/src/model/office.dart';
import 'package:smart_cab_api/src/model/office_input.dart';
import 'package:smart_cab_api/src/model/otp_request.dart';
import 'package:smart_cab_api/src/model/otp_verify.dart';
import 'package:smart_cab_api/src/model/override_input.dart';
import 'package:smart_cab_api/src/model/override_result.dart';
import 'package:smart_cab_api/src/model/reason_code.dart';
import 'package:smart_cab_api/src/model/request_status.dart';
import 'package:smart_cab_api/src/model/ride_request.dart';
import 'package:smart_cab_api/src/model/ride_request_assignment.dart';
import 'package:smart_cab_api/src/model/ride_request_input.dart';
import 'package:smart_cab_api/src/model/ride_requests_mine_get200_response.dart';
import 'package:smart_cab_api/src/model/ride_requests_request_id_cancel_post_request.dart';
import 'package:smart_cab_api/src/model/ride_requests_request_id_rating_post_request.dart';
import 'package:smart_cab_api/src/model/role.dart';
import 'package:smart_cab_api/src/model/sim_clock.dart';
import 'package:smart_cab_api/src/model/simctl_release_post200_response.dart';
import 'package:smart_cab_api/src/model/simctl_release_post_request.dart';
import 'package:smart_cab_api/src/model/simctl_reset_post_request.dart';
import 'package:smart_cab_api/src/model/sos_post_request.dart';
import 'package:smart_cab_api/src/model/stop_status.dart';
import 'package:smart_cab_api/src/model/token_pair.dart';
import 'package:smart_cab_api/src/model/tracker_type.dart';
import 'package:smart_cab_api/src/model/trip.dart';
import 'package:smart_cab_api/src/model/trip_report.dart';
import 'package:smart_cab_api/src/model/trip_status.dart';
import 'package:smart_cab_api/src/model/trip_stop.dart';
import 'package:smart_cab_api/src/model/urgency.dart';
import 'package:smart_cab_api/src/model/vehicle.dart';
import 'package:smart_cab_api/src/model/vehicle_input.dart';
import 'package:smart_cab_api/src/model/vehicle_live.dart';
import 'package:smart_cab_api/src/model/vehicle_status.dart';
import 'package:smart_cab_api/src/model/vehicle_type.dart';

part 'serializers.g.dart';

@SerializersFor([
  AdminClientsClientIdEmployeesGet200Response,
  AdminDriversGet200Response,
  AdminUsersInvitePostRequest,
  AdminVehiclesGet200Response,
  Alert,
  AuthRefreshPostRequest,
  Candidate,
  CandidateAddedMinutesExistingInner,
  Client,
  ClientInput,$ClientInput,
  DeviceRegister,
  Direction,
  DispatchAssignPostRequest,
  DispatchAutomationGet200Response,
  DispatchAutomationPutRequest,
  DispatchSuggestionsSuggestionIdDecisionPostRequest,
  DispatchTripsGet200Response,
  Driver,
  DriverDutyPostRequest,
  DriverInput,$DriverInput,
  DriverIssuesPostRequest,
  DriverTripsTripIdStartPostRequest,
  DutyState,
  DutyStateMqtt,
  Employee,
  EmployeeInput,$EmployeeInput,
  Error,
  Impact,
  ImpactAffectedRequestsInner,
  ImportReport,
  ImportReportErrorsInner,
  LatLng,
  LocationPing,
  Me,
  MeRolesInner,
  ModeSetting,
  Office,
  OfficeInput,$OfficeInput,
  OtpRequest,
  OtpVerify,
  OverrideInput,
  OverrideResult,
  ReasonCode,
  RequestStatus,
  RideRequest,
  RideRequestAssignment,
  RideRequestInput,
  RideRequestsMineGet200Response,
  RideRequestsRequestIdCancelPostRequest,
  RideRequestsRequestIdRatingPostRequest,
  Role,
  SimClock,
  SimctlReleasePost200Response,
  SimctlReleasePostRequest,
  SimctlResetPostRequest,
  SosPostRequest,
  StopStatus,
  TokenPair,
  TrackerType,
  Trip,
  TripReport,
  TripStatus,
  TripStop,
  Urgency,
  Vehicle,$Vehicle,
  VehicleInput,$VehicleInput,
  VehicleLive,
  VehicleStatus,
  VehicleType,
])
Serializers serializers = (_$serializers.toBuilder()
      ..addBuilderFactory(
        const FullType(BuiltList, [FullType(RequestStatus)]),
        () => ListBuilder<RequestStatus>(),
      )
      ..addBuilderFactory(
        const FullType(BuiltList, [FullType(RideRequest)]),
        () => ListBuilder<RideRequest>(),
      )
      ..addBuilderFactory(
        const FullType(BuiltList, [FullType(TripStatus)]),
        () => ListBuilder<TripStatus>(),
      )
      ..addBuilderFactory(
        const FullType(BuiltList, [FullType(VehicleLive)]),
        () => ListBuilder<VehicleLive>(),
      )
      ..addBuilderFactory(
        const FullType(BuiltList, [FullType(Office)]),
        () => ListBuilder<Office>(),
      )
      ..addBuilderFactory(
        const FullType(BuiltList, [FullType(LocationPing)]),
        () => ListBuilder<LocationPing>(),
      )
      ..addBuilderFactory(
        const FullType(BuiltList, [FullType(ModeSetting)]),
        () => ListBuilder<ModeSetting>(),
      )
      ..addBuilderFactory(
        const FullType(BuiltList, [FullType(Client)]),
        () => ListBuilder<Client>(),
      )
      ..addBuilderFactory(
        const FullType(BuiltList, [FullType(Alert)]),
        () => ListBuilder<Alert>(),
      )
      ..addBuilderFactory(
        const FullType(BuiltMap, [FullType(String), FullType.nullable(JsonObject)]),
        () => MapBuilder<String, JsonObject>(),
      )
      ..addBuilderFactory(
        const FullType(BuiltList, [FullType(Trip)]),
        () => ListBuilder<Trip>(),
      )
      ..addBuilderFactory(
        const FullType(BuiltList, [FullType(Candidate)]),
        () => ListBuilder<Candidate>(),
      )
      ..addBuilderFactory(
        const FullType(BuiltMap, [FullType(String), FullType(JsonObject)]),
        () => MapBuilder<String, JsonObject>(),
      )
      ..add(ClientInput.serializer)
      ..add(DriverInput.serializer)
      ..add(EmployeeInput.serializer)
      ..add(OfficeInput.serializer)
      ..add(Vehicle.serializer)
      ..add(VehicleInput.serializer)
      ..add(const OneOfSerializer())
      ..add(const AnyOfSerializer())
      ..add(const DateSerializer())
      ..add(Iso8601DateTimeSerializer())
    ).build();

Serializers standardSerializers =
    (serializers.toBuilder()..addPlugin(StandardJsonPlugin())).build();
