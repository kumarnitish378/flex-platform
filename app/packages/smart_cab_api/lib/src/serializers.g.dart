// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'serializers.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

Serializers _$serializers = (Serializers().toBuilder()
      ..add($ClientInput.serializer)
      ..add($ClientPolicyInput.serializer)
      ..add($DriverInput.serializer)
      ..add($EmployeeInput.serializer)
      ..add($ModeSettingInput.serializer)
      ..add($OfficeInput.serializer)
      ..add($Vehicle.serializer)
      ..add($VehicleInput.serializer)
      ..add($ZoneInput.serializer)
      ..add(AdminClientsClientIdEmployeesGet200Response.serializer)
      ..add(AdminClientsClientIdOfficesGet200Response.serializer)
      ..add(AdminClientsGet200Response.serializer)
      ..add(AdminDriversGet200Response.serializer)
      ..add(AdminModeSettingsGet200Response.serializer)
      ..add(AdminUsersInvitePostRequest.serializer)
      ..add(AdminUsersInvitePostRequestRoleEnum.serializer)
      ..add(AdminVehiclesGet200Response.serializer)
      ..add(AdminZonesGet200Response.serializer)
      ..add(Alert.serializer)
      ..add(AlertSeverityEnum.serializer)
      ..add(AlertStatusEnum.serializer)
      ..add(AlertTypeEnum.serializer)
      ..add(AlertsGet200Response.serializer)
      ..add(AuthRefreshPostRequest.serializer)
      ..add(BillingExport.serializer)
      ..add(BillingExportRowsInner.serializer)
      ..add(BillingExportSummary.serializer)
      ..add(BillingExportTreatment.serializer)
      ..add(BillingExportTreatmentBasisEnum.serializer)
      ..add(BillingExportTreatmentDistanceBasisEnum.serializer)
      ..add(Candidate.serializer)
      ..add(CandidateAddedMinutesExistingInner.serializer)
      ..add(Client.serializer)
      ..add(ClientPolicy.serializer)
      ..add(ClientPolicyAllOfEffective.serializer)
      ..add(DeviceRegister.serializer)
      ..add(DeviceRegisterPlatformEnum.serializer)
      ..add(Direction.serializer)
      ..add(DispatchAssignPostRequest.serializer)
      ..add(DispatchAutomationGet200Response.serializer)
      ..add(DispatchAutomationPutRequest.serializer)
      ..add(DispatchHintsGet200Response.serializer)
      ..add(DispatchRequestsGet200Response.serializer)
      ..add(DispatchRequestsRequestIdCandidatesGet200Response.serializer)
      ..add(DispatchSuggestionsGet200Response.serializer)
      ..add(DispatchSuggestionsSuggestionIdDecisionPostRequest.serializer)
      ..add(DispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnum
          .serializer)
      ..add(DispatchTripsGet200Response.serializer)
      ..add(DispatchVehiclesGet200Response.serializer)
      ..add(Driver.serializer)
      ..add(DriverDutyPostRequest.serializer)
      ..add(DriverIssuesPostRequest.serializer)
      ..add(DriverIssuesPostRequestTypeEnum.serializer)
      ..add(DriverTripsGet200Response.serializer)
      ..add(DriverTripsTripIdStartPostRequest.serializer)
      ..add(DutyState.serializer)
      ..add(DutyStateGps.serializer)
      ..add(DutyStateMqtt.serializer)
      ..add(Employee.serializer)
      ..add(EmployeeInputGenderEnum.serializer)
      ..add(Error.serializer)
      ..add(EscortConfirmation.serializer)
      ..add(EscortConfirmationBasisEnum.serializer)
      ..add(Impact.serializer)
      ..add(ImpactAffectedRequestsInner.serializer)
      ..add(ImportReport.serializer)
      ..add(ImportReportErrorsInner.serializer)
      ..add(LatLng.serializer)
      ..add(LocationPing.serializer)
      ..add(Me.serializer)
      ..add(MeRolesInner.serializer)
      ..add(ModeResolution.serializer)
      ..add(ModeResolutionModeEnum.serializer)
      ..add(ModeResolutionReasonEnum.serializer)
      ..add(ModeSetting.serializer)
      ..add(ModeSettingInputDirectionEnum.serializer)
      ..add(ModeSettingInputModeEnum.serializer)
      ..add(Office.serializer)
      ..add(OperationsReport.serializer)
      ..add(OperationsReportDistance.serializer)
      ..add(OperationsReportOptimizer.serializer)
      ..add(OperationsReportOverrides.serializer)
      ..add(OperationsReportPeriod.serializer)
      ..add(OperationsReportPooling.serializer)
      ..add(OperationsReportRequests.serializer)
      ..add(OperationsReportSuggestions.serializer)
      ..add(OperationsReportWait.serializer)
      ..add(OtpRequest.serializer)
      ..add(OtpVerify.serializer)
      ..add(OverrideInput.serializer)
      ..add(OverrideInputActionEnum.serializer)
      ..add(OverrideResult.serializer)
      ..add(ReasonCode.serializer)
      ..add(RequestHint.serializer)
      ..add(RequestStatus.serializer)
      ..add(RideRequest.serializer)
      ..add(RideRequestAssignment.serializer)
      ..add(RideRequestInput.serializer)
      ..add(RideRequestsMineGet200Response.serializer)
      ..add(RideRequestsRequestIdCancelPostRequest.serializer)
      ..add(RideRequestsRequestIdRatingPostRequest.serializer)
      ..add(Role.serializer)
      ..add(SimClock.serializer)
      ..add(SimctlOptimizerPutRequest.serializer)
      ..add(SimctlReleasePost200Response.serializer)
      ..add(SimctlReleasePostRequest.serializer)
      ..add(SimctlResetPostRequest.serializer)
      ..add(SosPostRequest.serializer)
      ..add(StopStatus.serializer)
      ..add(Suggestion.serializer)
      ..add(SuggestionDecisionResult.serializer)
      ..add(SuggestionDecisionResultDecisionEnum.serializer)
      ..add(SuggestionDecisionResultStatusEnum.serializer)
      ..add(SuggestionStatusEnum.serializer)
      ..add(TestLoginRequest.serializer)
      ..add(TokenPair.serializer)
      ..add(TrackerType.serializer)
      ..add(Trip.serializer)
      ..add(TripEscort.serializer)
      ..add(TripEscortBasisEnum.serializer)
      ..add(TripModeUsedEnum.serializer)
      ..add(TripReport.serializer)
      ..add(TripRider.serializer)
      ..add(TripStatus.serializer)
      ..add(TripStop.serializer)
      ..add(TripStopStopTypeEnum.serializer)
      ..add(Urgency.serializer)
      ..add(VehicleLive.serializer)
      ..add(VehicleStatus.serializer)
      ..add(VehicleType.serializer)
      ..add(Zone.serializer)
      ..add(ZoneUpdate.serializer)
      ..addBuilderFactory(
          const FullType(BuiltList, const [const FullType(Alert)]),
          () => ListBuilder<Alert>())
      ..addBuilderFactory(
          const FullType(
              BuiltList, const [const FullType(BillingExportRowsInner)]),
          () => ListBuilder<BillingExportRowsInner>())
      ..addBuilderFactory(
          const FullType(BuiltList, const [const FullType(Candidate)]),
          () => ListBuilder<Candidate>())
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
          const FullType(BuiltList, const [const FullType(Client)]),
          () => ListBuilder<Client>())
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
          const FullType(BuiltList, const [const FullType(LatLng)]),
          () => ListBuilder<LatLng>())
      ..addBuilderFactory(
          const FullType(BuiltList, const [const FullType(LatLng)]),
          () => ListBuilder<LatLng>())
      ..addBuilderFactory(
          const FullType(BuiltList, const [const FullType(LatLng)]),
          () => ListBuilder<LatLng>())
      ..addBuilderFactory(
          const FullType(BuiltList, const [const FullType(MeRolesInner)]),
          () => ListBuilder<MeRolesInner>())
      ..addBuilderFactory(
          const FullType(BuiltList, const [const FullType(ModeSetting)]),
          () => ListBuilder<ModeSetting>())
      ..addBuilderFactory(
          const FullType(BuiltList, const [
            const FullType(BuiltList, const [const FullType(String)])
          ]),
          () => ListBuilder<BuiltList<String>>())
      ..addBuilderFactory(
          const FullType(BuiltList, const [const FullType(Office)]),
          () => ListBuilder<Office>())
      ..addBuilderFactory(
          const FullType(BuiltList, const [const FullType(RequestHint)]),
          () => ListBuilder<RequestHint>())
      ..addBuilderFactory(
          const FullType(BuiltList, const [const FullType(RideRequest)]),
          () => ListBuilder<RideRequest>())
      ..addBuilderFactory(
          const FullType(BuiltList, const [const FullType(RideRequest)]),
          () => ListBuilder<RideRequest>())
      ..addBuilderFactory(
          const FullType(BuiltList, const [const FullType(String)]),
          () => ListBuilder<String>())
      ..addBuilderFactory(
          const FullType(BuiltList, const [const FullType(String)]),
          () => ListBuilder<String>())
      ..addBuilderFactory(
          const FullType(BuiltList, const [const FullType(String)]),
          () => ListBuilder<String>())
      ..addBuilderFactory(
          const FullType(BuiltList, const [const FullType(String)]),
          () => ListBuilder<String>())
      ..addBuilderFactory(
          const FullType(BuiltList, const [const FullType(Suggestion)]),
          () => ListBuilder<Suggestion>())
      ..addBuilderFactory(
          const FullType(BuiltList, const [const FullType(Trip)]),
          () => ListBuilder<Trip>())
      ..addBuilderFactory(
          const FullType(BuiltList, const [const FullType(Trip)]),
          () => ListBuilder<Trip>())
      ..addBuilderFactory(
          const FullType(BuiltList, const [const FullType(TripStop)]),
          () => ListBuilder<TripStop>())
      ..addBuilderFactory(
          const FullType(BuiltList, const [const FullType(TripRider)]),
          () => ListBuilder<TripRider>())
      ..addBuilderFactory(
          const FullType(BuiltList, const [const FullType(Vehicle)]),
          () => ListBuilder<Vehicle>())
      ..addBuilderFactory(
          const FullType(BuiltList, const [const FullType(VehicleLive)]),
          () => ListBuilder<VehicleLive>())
      ..addBuilderFactory(
          const FullType(BuiltList, const [const FullType(Zone)]),
          () => ListBuilder<Zone>())
      ..addBuilderFactory(
          const FullType(BuiltList, const [const FullType(int)]),
          () => ListBuilder<int>())
      ..addBuilderFactory(
          const FullType(BuiltList, const [const FullType(int)]),
          () => ListBuilder<int>())
      ..addBuilderFactory(
          const FullType(
              BuiltMap, const [const FullType(String), const FullType(int)]),
          () => MapBuilder<String, int>())
      ..addBuilderFactory(
          const FullType(
              BuiltMap, const [const FullType(String), const FullType(int)]),
          () => MapBuilder<String, int>())
      ..addBuilderFactory(
          const FullType(
              BuiltMap, const [const FullType(String), const FullType(int)]),
          () => MapBuilder<String, int>())
      ..addBuilderFactory(
          const FullType(BuiltList, const [
            const FullType(BuiltMap, const [
              const FullType(String),
              const FullType.nullable(JsonObject)
            ])
          ]),
          () => ListBuilder<BuiltMap<String, JsonObject?>>())
      ..addBuilderFactory(
          const FullType(
              BuiltMap, const [const FullType(String), const FullType(int)]),
          () => MapBuilder<String, int>())
      ..addBuilderFactory(
          const FullType(
              BuiltMap, const [const FullType(String), const FullType(int)]),
          () => MapBuilder<String, int>())
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
