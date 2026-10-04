// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'alert.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

const AlertTypeEnum _$alertTypeEnum_sos = const AlertTypeEnum._('sos');
const AlertTypeEnum _$alertTypeEnum_driverIssue =
    const AlertTypeEnum._('driverIssue');
const AlertTypeEnum _$alertTypeEnum_requestUnassigned =
    const AlertTypeEnum._('requestUnassigned');
const AlertTypeEnum _$alertTypeEnum_requestNearExpiry =
    const AlertTypeEnum._('requestNearExpiry');
const AlertTypeEnum _$alertTypeEnum_vipNoVehicle =
    const AlertTypeEnum._('vipNoVehicle');
const AlertTypeEnum _$alertTypeEnum_failsafe =
    const AlertTypeEnum._('failsafe');
const AlertTypeEnum _$alertTypeEnum_staleVehicle =
    const AlertTypeEnum._('staleVehicle');
const AlertTypeEnum _$alertTypeEnum_modePrompt =
    const AlertTypeEnum._('modePrompt');
const AlertTypeEnum _$alertTypeEnum_system = const AlertTypeEnum._('system');

AlertTypeEnum _$alertTypeEnumValueOf(String name) {
  switch (name) {
    case 'sos':
      return _$alertTypeEnum_sos;
    case 'driverIssue':
      return _$alertTypeEnum_driverIssue;
    case 'requestUnassigned':
      return _$alertTypeEnum_requestUnassigned;
    case 'requestNearExpiry':
      return _$alertTypeEnum_requestNearExpiry;
    case 'vipNoVehicle':
      return _$alertTypeEnum_vipNoVehicle;
    case 'failsafe':
      return _$alertTypeEnum_failsafe;
    case 'staleVehicle':
      return _$alertTypeEnum_staleVehicle;
    case 'modePrompt':
      return _$alertTypeEnum_modePrompt;
    case 'system':
      return _$alertTypeEnum_system;
    default:
      throw ArgumentError(name);
  }
}

final BuiltSet<AlertTypeEnum> _$alertTypeEnumValues =
    BuiltSet<AlertTypeEnum>(const <AlertTypeEnum>[
  _$alertTypeEnum_sos,
  _$alertTypeEnum_driverIssue,
  _$alertTypeEnum_requestUnassigned,
  _$alertTypeEnum_requestNearExpiry,
  _$alertTypeEnum_vipNoVehicle,
  _$alertTypeEnum_failsafe,
  _$alertTypeEnum_staleVehicle,
  _$alertTypeEnum_modePrompt,
  _$alertTypeEnum_system,
]);

const AlertSeverityEnum _$alertSeverityEnum_critical =
    const AlertSeverityEnum._('critical');
const AlertSeverityEnum _$alertSeverityEnum_warning =
    const AlertSeverityEnum._('warning');
const AlertSeverityEnum _$alertSeverityEnum_info =
    const AlertSeverityEnum._('info');

AlertSeverityEnum _$alertSeverityEnumValueOf(String name) {
  switch (name) {
    case 'critical':
      return _$alertSeverityEnum_critical;
    case 'warning':
      return _$alertSeverityEnum_warning;
    case 'info':
      return _$alertSeverityEnum_info;
    default:
      throw ArgumentError(name);
  }
}

final BuiltSet<AlertSeverityEnum> _$alertSeverityEnumValues =
    BuiltSet<AlertSeverityEnum>(const <AlertSeverityEnum>[
  _$alertSeverityEnum_critical,
  _$alertSeverityEnum_warning,
  _$alertSeverityEnum_info,
]);

const AlertStatusEnum _$alertStatusEnum_open = const AlertStatusEnum._('open');
const AlertStatusEnum _$alertStatusEnum_acknowledged =
    const AlertStatusEnum._('acknowledged');
const AlertStatusEnum _$alertStatusEnum_resolved =
    const AlertStatusEnum._('resolved');

AlertStatusEnum _$alertStatusEnumValueOf(String name) {
  switch (name) {
    case 'open':
      return _$alertStatusEnum_open;
    case 'acknowledged':
      return _$alertStatusEnum_acknowledged;
    case 'resolved':
      return _$alertStatusEnum_resolved;
    default:
      throw ArgumentError(name);
  }
}

final BuiltSet<AlertStatusEnum> _$alertStatusEnumValues =
    BuiltSet<AlertStatusEnum>(const <AlertStatusEnum>[
  _$alertStatusEnum_open,
  _$alertStatusEnum_acknowledged,
  _$alertStatusEnum_resolved,
]);

Serializer<AlertTypeEnum> _$alertTypeEnumSerializer =
    _$AlertTypeEnumSerializer();
Serializer<AlertSeverityEnum> _$alertSeverityEnumSerializer =
    _$AlertSeverityEnumSerializer();
Serializer<AlertStatusEnum> _$alertStatusEnumSerializer =
    _$AlertStatusEnumSerializer();

class _$AlertTypeEnumSerializer implements PrimitiveSerializer<AlertTypeEnum> {
  static const Map<String, Object> _toWire = const <String, Object>{
    'sos': 'sos',
    'driverIssue': 'driver_issue',
    'requestUnassigned': 'request_unassigned',
    'requestNearExpiry': 'request_near_expiry',
    'vipNoVehicle': 'vip_no_vehicle',
    'failsafe': 'failsafe',
    'staleVehicle': 'stale_vehicle',
    'modePrompt': 'mode_prompt',
    'system': 'system',
  };
  static const Map<Object, String> _fromWire = const <Object, String>{
    'sos': 'sos',
    'driver_issue': 'driverIssue',
    'request_unassigned': 'requestUnassigned',
    'request_near_expiry': 'requestNearExpiry',
    'vip_no_vehicle': 'vipNoVehicle',
    'failsafe': 'failsafe',
    'stale_vehicle': 'staleVehicle',
    'mode_prompt': 'modePrompt',
    'system': 'system',
  };

  @override
  final Iterable<Type> types = const <Type>[AlertTypeEnum];
  @override
  final String wireName = 'AlertTypeEnum';

  @override
  Object serialize(Serializers serializers, AlertTypeEnum object,
          {FullType specifiedType = FullType.unspecified}) =>
      _toWire[object.name] ?? object.name;

  @override
  AlertTypeEnum deserialize(Serializers serializers, Object serialized,
          {FullType specifiedType = FullType.unspecified}) =>
      AlertTypeEnum.valueOf(
          _fromWire[serialized] ?? (serialized is String ? serialized : ''));
}

class _$AlertSeverityEnumSerializer
    implements PrimitiveSerializer<AlertSeverityEnum> {
  static const Map<String, Object> _toWire = const <String, Object>{
    'critical': 'critical',
    'warning': 'warning',
    'info': 'info',
  };
  static const Map<Object, String> _fromWire = const <Object, String>{
    'critical': 'critical',
    'warning': 'warning',
    'info': 'info',
  };

  @override
  final Iterable<Type> types = const <Type>[AlertSeverityEnum];
  @override
  final String wireName = 'AlertSeverityEnum';

  @override
  Object serialize(Serializers serializers, AlertSeverityEnum object,
          {FullType specifiedType = FullType.unspecified}) =>
      _toWire[object.name] ?? object.name;

  @override
  AlertSeverityEnum deserialize(Serializers serializers, Object serialized,
          {FullType specifiedType = FullType.unspecified}) =>
      AlertSeverityEnum.valueOf(
          _fromWire[serialized] ?? (serialized is String ? serialized : ''));
}

class _$AlertStatusEnumSerializer
    implements PrimitiveSerializer<AlertStatusEnum> {
  static const Map<String, Object> _toWire = const <String, Object>{
    'open': 'open',
    'acknowledged': 'acknowledged',
    'resolved': 'resolved',
  };
  static const Map<Object, String> _fromWire = const <Object, String>{
    'open': 'open',
    'acknowledged': 'acknowledged',
    'resolved': 'resolved',
  };

  @override
  final Iterable<Type> types = const <Type>[AlertStatusEnum];
  @override
  final String wireName = 'AlertStatusEnum';

  @override
  Object serialize(Serializers serializers, AlertStatusEnum object,
          {FullType specifiedType = FullType.unspecified}) =>
      _toWire[object.name] ?? object.name;

  @override
  AlertStatusEnum deserialize(Serializers serializers, Object serialized,
          {FullType specifiedType = FullType.unspecified}) =>
      AlertStatusEnum.valueOf(
          _fromWire[serialized] ?? (serialized is String ? serialized : ''));
}

class _$Alert extends Alert {
  @override
  final String? id;
  @override
  final AlertTypeEnum? type;
  @override
  final AlertSeverityEnum? severity;
  @override
  final AlertStatusEnum? status;
  @override
  final DateTime? createdAt;
  @override
  final String? requestId;
  @override
  final String? tripId;
  @override
  final String? vehicleId;
  @override
  final BuiltMap<String, JsonObject?>? data;

  factory _$Alert([void Function(AlertBuilder)? updates]) =>
      (AlertBuilder()..update(updates))._build();

  _$Alert._(
      {this.id,
      this.type,
      this.severity,
      this.status,
      this.createdAt,
      this.requestId,
      this.tripId,
      this.vehicleId,
      this.data})
      : super._();
  @override
  Alert rebuild(void Function(AlertBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  AlertBuilder toBuilder() => AlertBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is Alert &&
        id == other.id &&
        type == other.type &&
        severity == other.severity &&
        status == other.status &&
        createdAt == other.createdAt &&
        requestId == other.requestId &&
        tripId == other.tripId &&
        vehicleId == other.vehicleId &&
        data == other.data;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, id.hashCode);
    _$hash = $jc(_$hash, type.hashCode);
    _$hash = $jc(_$hash, severity.hashCode);
    _$hash = $jc(_$hash, status.hashCode);
    _$hash = $jc(_$hash, createdAt.hashCode);
    _$hash = $jc(_$hash, requestId.hashCode);
    _$hash = $jc(_$hash, tripId.hashCode);
    _$hash = $jc(_$hash, vehicleId.hashCode);
    _$hash = $jc(_$hash, data.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'Alert')
          ..add('id', id)
          ..add('type', type)
          ..add('severity', severity)
          ..add('status', status)
          ..add('createdAt', createdAt)
          ..add('requestId', requestId)
          ..add('tripId', tripId)
          ..add('vehicleId', vehicleId)
          ..add('data', data))
        .toString();
  }
}

class AlertBuilder implements Builder<Alert, AlertBuilder> {
  _$Alert? _$v;

  String? _id;
  String? get id => _$this._id;
  set id(String? id) => _$this._id = id;

  AlertTypeEnum? _type;
  AlertTypeEnum? get type => _$this._type;
  set type(AlertTypeEnum? type) => _$this._type = type;

  AlertSeverityEnum? _severity;
  AlertSeverityEnum? get severity => _$this._severity;
  set severity(AlertSeverityEnum? severity) => _$this._severity = severity;

  AlertStatusEnum? _status;
  AlertStatusEnum? get status => _$this._status;
  set status(AlertStatusEnum? status) => _$this._status = status;

  DateTime? _createdAt;
  DateTime? get createdAt => _$this._createdAt;
  set createdAt(DateTime? createdAt) => _$this._createdAt = createdAt;

  String? _requestId;
  String? get requestId => _$this._requestId;
  set requestId(String? requestId) => _$this._requestId = requestId;

  String? _tripId;
  String? get tripId => _$this._tripId;
  set tripId(String? tripId) => _$this._tripId = tripId;

  String? _vehicleId;
  String? get vehicleId => _$this._vehicleId;
  set vehicleId(String? vehicleId) => _$this._vehicleId = vehicleId;

  MapBuilder<String, JsonObject?>? _data;
  MapBuilder<String, JsonObject?> get data =>
      _$this._data ??= MapBuilder<String, JsonObject?>();
  set data(MapBuilder<String, JsonObject?>? data) => _$this._data = data;

  AlertBuilder() {
    Alert._defaults(this);
  }

  AlertBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _id = $v.id;
      _type = $v.type;
      _severity = $v.severity;
      _status = $v.status;
      _createdAt = $v.createdAt;
      _requestId = $v.requestId;
      _tripId = $v.tripId;
      _vehicleId = $v.vehicleId;
      _data = $v.data?.toBuilder();
      _$v = null;
    }
    return this;
  }

  @override
  void replace(Alert other) {
    _$v = other as _$Alert;
  }

  @override
  void update(void Function(AlertBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  Alert build() => _build();

  _$Alert _build() {
    _$Alert _$result;
    try {
      _$result = _$v ??
          _$Alert._(
            id: id,
            type: type,
            severity: severity,
            status: status,
            createdAt: createdAt,
            requestId: requestId,
            tripId: tripId,
            vehicleId: vehicleId,
            data: _data?.build(),
          );
    } catch (_) {
      late String _$failedField;
      try {
        _$failedField = 'data';
        _data?.build();
      } catch (e) {
        throw BuiltValueNestedFieldError(r'Alert', _$failedField, e.toString());
      }
      rethrow;
    }
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
