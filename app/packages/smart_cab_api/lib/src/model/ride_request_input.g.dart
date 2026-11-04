// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'ride_request_input.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$RideRequestInput extends RideRequestInput {
  @override
  final String? employeeId;
  @override
  final Direction direction;
  @override
  final DateTime requestedTime;
  @override
  final LatLng? location;
  @override
  final String? landmark;
  @override
  final Urgency? urgency;
  @override
  final bool? noSharing;

  factory _$RideRequestInput(
          [void Function(RideRequestInputBuilder)? updates]) =>
      (RideRequestInputBuilder()..update(updates))._build();

  _$RideRequestInput._(
      {this.employeeId,
      required this.direction,
      required this.requestedTime,
      this.location,
      this.landmark,
      this.urgency,
      this.noSharing})
      : super._();
  @override
  RideRequestInput rebuild(void Function(RideRequestInputBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  RideRequestInputBuilder toBuilder() =>
      RideRequestInputBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is RideRequestInput &&
        employeeId == other.employeeId &&
        direction == other.direction &&
        requestedTime == other.requestedTime &&
        location == other.location &&
        landmark == other.landmark &&
        urgency == other.urgency &&
        noSharing == other.noSharing;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, employeeId.hashCode);
    _$hash = $jc(_$hash, direction.hashCode);
    _$hash = $jc(_$hash, requestedTime.hashCode);
    _$hash = $jc(_$hash, location.hashCode);
    _$hash = $jc(_$hash, landmark.hashCode);
    _$hash = $jc(_$hash, urgency.hashCode);
    _$hash = $jc(_$hash, noSharing.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'RideRequestInput')
          ..add('employeeId', employeeId)
          ..add('direction', direction)
          ..add('requestedTime', requestedTime)
          ..add('location', location)
          ..add('landmark', landmark)
          ..add('urgency', urgency)
          ..add('noSharing', noSharing))
        .toString();
  }
}

class RideRequestInputBuilder
    implements Builder<RideRequestInput, RideRequestInputBuilder> {
  _$RideRequestInput? _$v;

  String? _employeeId;
  String? get employeeId => _$this._employeeId;
  set employeeId(String? employeeId) => _$this._employeeId = employeeId;

  Direction? _direction;
  Direction? get direction => _$this._direction;
  set direction(Direction? direction) => _$this._direction = direction;

  DateTime? _requestedTime;
  DateTime? get requestedTime => _$this._requestedTime;
  set requestedTime(DateTime? requestedTime) =>
      _$this._requestedTime = requestedTime;

  LatLngBuilder? _location;
  LatLngBuilder get location => _$this._location ??= LatLngBuilder();
  set location(LatLngBuilder? location) => _$this._location = location;

  String? _landmark;
  String? get landmark => _$this._landmark;
  set landmark(String? landmark) => _$this._landmark = landmark;

  Urgency? _urgency;
  Urgency? get urgency => _$this._urgency;
  set urgency(Urgency? urgency) => _$this._urgency = urgency;

  bool? _noSharing;
  bool? get noSharing => _$this._noSharing;
  set noSharing(bool? noSharing) => _$this._noSharing = noSharing;

  RideRequestInputBuilder() {
    RideRequestInput._defaults(this);
  }

  RideRequestInputBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _employeeId = $v.employeeId;
      _direction = $v.direction;
      _requestedTime = $v.requestedTime;
      _location = $v.location?.toBuilder();
      _landmark = $v.landmark;
      _urgency = $v.urgency;
      _noSharing = $v.noSharing;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(RideRequestInput other) {
    _$v = other as _$RideRequestInput;
  }

  @override
  void update(void Function(RideRequestInputBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  RideRequestInput build() => _build();

  _$RideRequestInput _build() {
    _$RideRequestInput _$result;
    try {
      _$result = _$v ??
          _$RideRequestInput._(
            employeeId: employeeId,
            direction: BuiltValueNullFieldError.checkNotNull(
                direction, r'RideRequestInput', 'direction'),
            requestedTime: BuiltValueNullFieldError.checkNotNull(
                requestedTime, r'RideRequestInput', 'requestedTime'),
            location: _location?.build(),
            landmark: landmark,
            urgency: urgency,
            noSharing: noSharing,
          );
    } catch (_) {
      late String _$failedField;
      try {
        _$failedField = 'location';
        _location?.build();
      } catch (e) {
        throw BuiltValueNestedFieldError(
            r'RideRequestInput', _$failedField, e.toString());
      }
      rethrow;
    }
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
