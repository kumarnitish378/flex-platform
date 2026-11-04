// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'ride_request.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$RideRequest extends RideRequest {
  @override
  final String? id;
  @override
  final String? employeeId;
  @override
  final String? employeeName;
  @override
  final String? clientId;
  @override
  final Direction? direction;
  @override
  final String? officeId;
  @override
  final LatLng? location;
  @override
  final LatLng? pickupLocation;
  @override
  final String? landmark;
  @override
  final DateTime? requestedTime;
  @override
  final Urgency? urgency;
  @override
  final bool? noSharing;
  @override
  final RequestStatus? status;
  @override
  final DateTime? waitingSince;
  @override
  final String? tripId;
  @override
  final RideRequestAssignment? assignment;
  @override
  final bool? locked;
  @override
  final DateTime? escalatedAt;
  @override
  final String? cancelReason;

  factory _$RideRequest([void Function(RideRequestBuilder)? updates]) =>
      (RideRequestBuilder()..update(updates))._build();

  _$RideRequest._(
      {this.id,
      this.employeeId,
      this.employeeName,
      this.clientId,
      this.direction,
      this.officeId,
      this.location,
      this.pickupLocation,
      this.landmark,
      this.requestedTime,
      this.urgency,
      this.noSharing,
      this.status,
      this.waitingSince,
      this.tripId,
      this.assignment,
      this.locked,
      this.escalatedAt,
      this.cancelReason})
      : super._();
  @override
  RideRequest rebuild(void Function(RideRequestBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  RideRequestBuilder toBuilder() => RideRequestBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is RideRequest &&
        id == other.id &&
        employeeId == other.employeeId &&
        employeeName == other.employeeName &&
        clientId == other.clientId &&
        direction == other.direction &&
        officeId == other.officeId &&
        location == other.location &&
        pickupLocation == other.pickupLocation &&
        landmark == other.landmark &&
        requestedTime == other.requestedTime &&
        urgency == other.urgency &&
        noSharing == other.noSharing &&
        status == other.status &&
        waitingSince == other.waitingSince &&
        tripId == other.tripId &&
        assignment == other.assignment &&
        locked == other.locked &&
        escalatedAt == other.escalatedAt &&
        cancelReason == other.cancelReason;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, id.hashCode);
    _$hash = $jc(_$hash, employeeId.hashCode);
    _$hash = $jc(_$hash, employeeName.hashCode);
    _$hash = $jc(_$hash, clientId.hashCode);
    _$hash = $jc(_$hash, direction.hashCode);
    _$hash = $jc(_$hash, officeId.hashCode);
    _$hash = $jc(_$hash, location.hashCode);
    _$hash = $jc(_$hash, pickupLocation.hashCode);
    _$hash = $jc(_$hash, landmark.hashCode);
    _$hash = $jc(_$hash, requestedTime.hashCode);
    _$hash = $jc(_$hash, urgency.hashCode);
    _$hash = $jc(_$hash, noSharing.hashCode);
    _$hash = $jc(_$hash, status.hashCode);
    _$hash = $jc(_$hash, waitingSince.hashCode);
    _$hash = $jc(_$hash, tripId.hashCode);
    _$hash = $jc(_$hash, assignment.hashCode);
    _$hash = $jc(_$hash, locked.hashCode);
    _$hash = $jc(_$hash, escalatedAt.hashCode);
    _$hash = $jc(_$hash, cancelReason.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'RideRequest')
          ..add('id', id)
          ..add('employeeId', employeeId)
          ..add('employeeName', employeeName)
          ..add('clientId', clientId)
          ..add('direction', direction)
          ..add('officeId', officeId)
          ..add('location', location)
          ..add('pickupLocation', pickupLocation)
          ..add('landmark', landmark)
          ..add('requestedTime', requestedTime)
          ..add('urgency', urgency)
          ..add('noSharing', noSharing)
          ..add('status', status)
          ..add('waitingSince', waitingSince)
          ..add('tripId', tripId)
          ..add('assignment', assignment)
          ..add('locked', locked)
          ..add('escalatedAt', escalatedAt)
          ..add('cancelReason', cancelReason))
        .toString();
  }
}

class RideRequestBuilder implements Builder<RideRequest, RideRequestBuilder> {
  _$RideRequest? _$v;

  String? _id;
  String? get id => _$this._id;
  set id(String? id) => _$this._id = id;

  String? _employeeId;
  String? get employeeId => _$this._employeeId;
  set employeeId(String? employeeId) => _$this._employeeId = employeeId;

  String? _employeeName;
  String? get employeeName => _$this._employeeName;
  set employeeName(String? employeeName) => _$this._employeeName = employeeName;

  String? _clientId;
  String? get clientId => _$this._clientId;
  set clientId(String? clientId) => _$this._clientId = clientId;

  Direction? _direction;
  Direction? get direction => _$this._direction;
  set direction(Direction? direction) => _$this._direction = direction;

  String? _officeId;
  String? get officeId => _$this._officeId;
  set officeId(String? officeId) => _$this._officeId = officeId;

  LatLngBuilder? _location;
  LatLngBuilder get location => _$this._location ??= LatLngBuilder();
  set location(LatLngBuilder? location) => _$this._location = location;

  LatLngBuilder? _pickupLocation;
  LatLngBuilder get pickupLocation =>
      _$this._pickupLocation ??= LatLngBuilder();
  set pickupLocation(LatLngBuilder? pickupLocation) =>
      _$this._pickupLocation = pickupLocation;

  String? _landmark;
  String? get landmark => _$this._landmark;
  set landmark(String? landmark) => _$this._landmark = landmark;

  DateTime? _requestedTime;
  DateTime? get requestedTime => _$this._requestedTime;
  set requestedTime(DateTime? requestedTime) =>
      _$this._requestedTime = requestedTime;

  Urgency? _urgency;
  Urgency? get urgency => _$this._urgency;
  set urgency(Urgency? urgency) => _$this._urgency = urgency;

  bool? _noSharing;
  bool? get noSharing => _$this._noSharing;
  set noSharing(bool? noSharing) => _$this._noSharing = noSharing;

  RequestStatus? _status;
  RequestStatus? get status => _$this._status;
  set status(RequestStatus? status) => _$this._status = status;

  DateTime? _waitingSince;
  DateTime? get waitingSince => _$this._waitingSince;
  set waitingSince(DateTime? waitingSince) =>
      _$this._waitingSince = waitingSince;

  String? _tripId;
  String? get tripId => _$this._tripId;
  set tripId(String? tripId) => _$this._tripId = tripId;

  RideRequestAssignmentBuilder? _assignment;
  RideRequestAssignmentBuilder get assignment =>
      _$this._assignment ??= RideRequestAssignmentBuilder();
  set assignment(RideRequestAssignmentBuilder? assignment) =>
      _$this._assignment = assignment;

  bool? _locked;
  bool? get locked => _$this._locked;
  set locked(bool? locked) => _$this._locked = locked;

  DateTime? _escalatedAt;
  DateTime? get escalatedAt => _$this._escalatedAt;
  set escalatedAt(DateTime? escalatedAt) => _$this._escalatedAt = escalatedAt;

  String? _cancelReason;
  String? get cancelReason => _$this._cancelReason;
  set cancelReason(String? cancelReason) => _$this._cancelReason = cancelReason;

  RideRequestBuilder() {
    RideRequest._defaults(this);
  }

  RideRequestBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _id = $v.id;
      _employeeId = $v.employeeId;
      _employeeName = $v.employeeName;
      _clientId = $v.clientId;
      _direction = $v.direction;
      _officeId = $v.officeId;
      _location = $v.location?.toBuilder();
      _pickupLocation = $v.pickupLocation?.toBuilder();
      _landmark = $v.landmark;
      _requestedTime = $v.requestedTime;
      _urgency = $v.urgency;
      _noSharing = $v.noSharing;
      _status = $v.status;
      _waitingSince = $v.waitingSince;
      _tripId = $v.tripId;
      _assignment = $v.assignment?.toBuilder();
      _locked = $v.locked;
      _escalatedAt = $v.escalatedAt;
      _cancelReason = $v.cancelReason;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(RideRequest other) {
    _$v = other as _$RideRequest;
  }

  @override
  void update(void Function(RideRequestBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  RideRequest build() => _build();

  _$RideRequest _build() {
    _$RideRequest _$result;
    try {
      _$result = _$v ??
          _$RideRequest._(
            id: id,
            employeeId: employeeId,
            employeeName: employeeName,
            clientId: clientId,
            direction: direction,
            officeId: officeId,
            location: _location?.build(),
            pickupLocation: _pickupLocation?.build(),
            landmark: landmark,
            requestedTime: requestedTime,
            urgency: urgency,
            noSharing: noSharing,
            status: status,
            waitingSince: waitingSince,
            tripId: tripId,
            assignment: _assignment?.build(),
            locked: locked,
            escalatedAt: escalatedAt,
            cancelReason: cancelReason,
          );
    } catch (_) {
      late String _$failedField;
      try {
        _$failedField = 'location';
        _location?.build();
        _$failedField = 'pickupLocation';
        _pickupLocation?.build();

        _$failedField = 'assignment';
        _assignment?.build();
      } catch (e) {
        throw BuiltValueNestedFieldError(
            r'RideRequest', _$failedField, e.toString());
      }
      rethrow;
    }
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
