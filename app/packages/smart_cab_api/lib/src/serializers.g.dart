// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'serializers.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

Serializers _$serializers = (Serializers().toBuilder()
      ..add($ClientInput.serializer)
      ..add($DriverInput.serializer)
      ..add($EmployeeInput.serializer)
      ..add($OfficeInput.serializer)
      ..add($Vehicle.serializer)
      ..add($VehicleInput.serializer)
      ..add(AdminClientsClientIdEmployeesGet200Response.serializer)
      ..add(AdminDriversGet200Response.serializer)
      ..add(AdminUsersInvitePostRequest.serializer)
      ..add(AdminUsersInvitePostRequestRoleEnum.serializer)
      ..add(AdminVehiclesGet200Response.serializer)
      ..add(Alert.serializer)
      ..add(AlertSeverityEnum.serializer)
      ..add(AlertStatusEnum.serializer)
      ..add(AlertTypeEnum.serializer)
      ..add(AuthRefreshPostRequest.serializer)
      ..add(Candidate.serializer)
      ..add(CandidateAddedMinutesExistingInner.serializer)
      ..add(Client.serializer)
      ..add(DeviceRegister.serializer)
      ..add(DeviceRegisterPlatformEnum.serializer)
      ..add(Direction.serializer)
      ..add(DispatchAssignPostRequest.serializer)
      ..add(DispatchAutomationGet200Response.serializer)
      ..add(DispatchAutomationPutRequest.serializer)
      ..add(DispatchSuggestionsSuggestionIdDecisionPostRequest.serializer)
      ..add(DispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnum
          .serializer)
      ..add(DispatchTripsGet200Response.serializer)
      ..add(Driver.serializer)
      ..add(DriverDutyPostRequest.serializer)
      ..add(DriverIssuesPostRequest.serializer)
      ..add(DriverIssuesPostRequestTypeEnum.serializer)
      ..add(DriverTripsTripIdStartPostRequest.serializer)
      ..add(DutyState.serializer)
      ..add(DutyStateMqtt.serializer)
      ..add(Employee.serializer)
      ..add(Error.serializer)
      ..add(Impact.serializer)
      ..add(ImpactAffectedRequestsInner.serializer)
      ..add(ImportReport.serializer)
      ..add(ImportReportErrorsInner.serializer)
      ..add(LatLng.serializer)
      ..add(LocationPing.serializer)
      ..add(Me.serializer)
      ..add(MeRolesInner.serializer)
      ..add(ModeSetting.serializer)
      ..add(ModeSettingModeEnum.serializer)
      ..add(Office.serializer)
      ..add(OtpRequest.serializer)
      ..add(OtpVerify.serializer)
      ..add(OverrideInput.serializer)
      ..add(OverrideInputActionEnum.serializer)
      ..add(OverrideResult.serializer)
      ..add(ReasonCode.serializer)
      ..add(RequestStatus.serializer)
      ..add(RideRequest.serializer)
      ..add(RideRequestAssignment.serializer)
      ..add(RideRequestInput.serializer)
      ..add(RideRequestsMineGet200Response.serializer)
      ..add(RideRequestsRequestIdCancelPostRequest.serializer)
      ..add(RideRequestsRequestIdRatingPostRequest.serializer)
      ..add(Role.serializer)
      ..add(SimClock.serializer)
      ..add(SimctlReleasePost200Response.serializer)
      ..add(SimctlReleasePostRequest.serializer)
      ..add(SimctlResetPostRequest.serializer)
      ..add(SosPostRequest.serializer)
      ..add(StopStatus.serializer)
      ..add(TokenPair.serializer)
      ..add(TrackerType.serializer)
      ..add(Trip.serializer)
      ..add(TripModeUsedEnum.serializer)
      ..add(TripReport.serializer)
      ..add(TripStatus.serializer)
      ..add(TripStop.serializer)
      ..add(TripStopStopTypeEnum.serializer)
      ..add(Urgency.serializer)
      ..add(VehicleLive.serializer)
      ..add(VehicleStatus.serializer)
      ..add(VehicleType.serializer)
      ..addBuilderFactory(
          const FullType(BuiltList, const [
            const FullType(BuiltMap, const [
              const FullType(String),
              const FullType.nullable(JsonObject)
            ])
          ]),
          () => ListBuilder<BuiltMap<String, JsonObject?>>())
      ..addBuilderFactory(
          const FullType(BuiltList,
              const [const FullType(CandidateAddedMinutesExistingInner)]),
          () => ListBuilder<CandidateAddedMinutesExistingInner>())
      ..addBuilderFactory(
          const FullType(BuiltList, const [const FullType(String)]),
          () => ListBuilder<String>())
      ..addBuilderFactory(
          const FullType(BuiltList, const [const FullType(String)]),
          () => ListBuilder<String>())
      ..addBuilderFactory(
          const FullType(BuiltList, const [const FullType(Driver)]),
          () => ListBuilder<Driver>())
      ..addBuilderFactory(
          const FullType(BuiltList, const [const FullType(Employee)]),
          () => ListBuilder<Employee>())
      ..addBuilderFactory(
          const FullType(
              BuiltList, const [const FullType(ImpactAffectedRequestsInner)]),
          () => ListBuilder<ImpactAffectedRequestsInner>())
      ..addBuilderFactory(
          const FullType(BuiltList, const [const FullType(String)]),
          () => ListBuilder<String>())
      ..addBuilderFactory(
          const FullType(BuiltList, const [const FullType(String)]),
          () => ListBuilder<String>())
      ..addBuilderFactory(
          const FullType(
              BuiltList, const [const FullType(ImportReportErrorsInner)]),
          () => ListBuilder<ImportReportErrorsInner>())
      ..addBuilderFactory(
          const FullType(BuiltList, const [const FullType(MeRolesInner)]),
          () => ListBuilder<MeRolesInner>())
      ..addBuilderFactory(
          const FullType(BuiltList, const [const FullType(RideRequest)]),
          () => ListBuilder<RideRequest>())
      ..addBuilderFactory(
          const FullType(BuiltList, const [const FullType(String)]),
          () => ListBuilder<String>())
      ..addBuilderFactory(
          const FullType(BuiltList, const [const FullType(Trip)]),
          () => ListBuilder<Trip>())
      ..addBuilderFactory(
          const FullType(BuiltList, const [const FullType(TripStop)]),
          () => ListBuilder<TripStop>())
      ..addBuilderFactory(
          const FullType(BuiltList, const [const FullType(Vehicle)]),
          () => ListBuilder<Vehicle>())
      ..addBuilderFactory(
          const FullType(BuiltMap, const [
            const FullType(String),
            const FullType.nullable(JsonObject)
          ]),
          () => MapBuilder<String, JsonObject?>())
      ..addBuilderFactory(
          const FullType(BuiltMap, const [
            const FullType(String),
            const FullType.nullable(JsonObject)
          ]),
          () => MapBuilder<String, JsonObject?>()))
    .build();

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
