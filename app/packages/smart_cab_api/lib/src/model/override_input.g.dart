// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'override_input.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

const OverrideInputActionEnum _$overrideInputActionEnum_reassign =
    const OverrideInputActionEnum._('reassign');
const OverrideInputActionEnum _$overrideInputActionEnum_lock =
    const OverrideInputActionEnum._('lock');
const OverrideInputActionEnum _$overrideInputActionEnum_unlock =
    const OverrideInputActionEnum._('unlock');
const OverrideInputActionEnum _$overrideInputActionEnum_forcePriority =
    const OverrideInputActionEnum._('forcePriority');
const OverrideInputActionEnum _$overrideInputActionEnum_blockPooling =
    const OverrideInputActionEnum._('blockPooling');
const OverrideInputActionEnum _$overrideInputActionEnum_hold =
    const OverrideInputActionEnum._('hold');
const OverrideInputActionEnum _$overrideInputActionEnum_cancel =
    const OverrideInputActionEnum._('cancel');
const OverrideInputActionEnum _$overrideInputActionEnum_vehicleOutOfService =
    const OverrideInputActionEnum._('vehicleOutOfService');

OverrideInputActionEnum _$overrideInputActionEnumValueOf(String name) {
  switch (name) {
    case 'reassign':
      return _$overrideInputActionEnum_reassign;
    case 'lock':
      return _$overrideInputActionEnum_lock;
    case 'unlock':
      return _$overrideInputActionEnum_unlock;
    case 'forcePriority':
      return _$overrideInputActionEnum_forcePriority;
    case 'blockPooling':
      return _$overrideInputActionEnum_blockPooling;
    case 'hold':
      return _$overrideInputActionEnum_hold;
    case 'cancel':
      return _$overrideInputActionEnum_cancel;
    case 'vehicleOutOfService':
      return _$overrideInputActionEnum_vehicleOutOfService;
    default:
      throw ArgumentError(name);
  }
}

final BuiltSet<OverrideInputActionEnum> _$overrideInputActionEnumValues =
    BuiltSet<OverrideInputActionEnum>(const <OverrideInputActionEnum>[
  _$overrideInputActionEnum_reassign,
  _$overrideInputActionEnum_lock,
  _$overrideInputActionEnum_unlock,
  _$overrideInputActionEnum_forcePriority,
  _$overrideInputActionEnum_blockPooling,
  _$overrideInputActionEnum_hold,
  _$overrideInputActionEnum_cancel,
  _$overrideInputActionEnum_vehicleOutOfService,
]);

Serializer<OverrideInputActionEnum> _$overrideInputActionEnumSerializer =
    _$OverrideInputActionEnumSerializer();

class _$OverrideInputActionEnumSerializer
    implements PrimitiveSerializer<OverrideInputActionEnum> {
  static const Map<String, Object> _toWire = const <String, Object>{
    'reassign': 'reassign',
    'lock': 'lock',
    'unlock': 'unlock',
    'forcePriority': 'force_priority',
    'blockPooling': 'block_pooling',
    'hold': 'hold',
    'cancel': 'cancel',
    'vehicleOutOfService': 'vehicle_out_of_service',
  };
  static const Map<Object, String> _fromWire = const <Object, String>{
    'reassign': 'reassign',
    'lock': 'lock',
    'unlock': 'unlock',
    'force_priority': 'forcePriority',
    'block_pooling': 'blockPooling',
    'hold': 'hold',
    'cancel': 'cancel',
    'vehicle_out_of_service': 'vehicleOutOfService',
  };

  @override
  final Iterable<Type> types = const <Type>[OverrideInputActionEnum];
  @override
  final String wireName = 'OverrideInputActionEnum';

  @override
  Object serialize(Serializers serializers, OverrideInputActionEnum object,
          {FullType specifiedType = FullType.unspecified}) =>
      _toWire[object.name] ?? object.name;

  @override
  OverrideInputActionEnum deserialize(
          Serializers serializers, Object serialized,
          {FullType specifiedType = FullType.unspecified}) =>
      OverrideInputActionEnum.valueOf(
          _fromWire[serialized] ?? (serialized is String ? serialized : ''));
}

class _$OverrideInput extends OverrideInput {
  @override
  final OverrideInputActionEnum action;
  @override
  final String? requestId;
  @override
  final String? tripId;
  @override
  final String? vehicleId;
  @override
  final String? targetVehicleId;
  @override
  final DateTime? holdUntil;
  @override
  final DateTime? expiresAt;
  @override
  final ReasonCode reasonCode;
  @override
  final String? note;

  factory _$OverrideInput([void Function(OverrideInputBuilder)? updates]) =>
      (OverrideInputBuilder()..update(updates))._build();

  _$OverrideInput._(
      {required this.action,
      this.requestId,
      this.tripId,
      this.vehicleId,
      this.targetVehicleId,
      this.holdUntil,
      this.expiresAt,
      required this.reasonCode,
      this.note})
      : super._();
  @override
  OverrideInput rebuild(void Function(OverrideInputBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  OverrideInputBuilder toBuilder() => OverrideInputBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is OverrideInput &&
        action == other.action &&
        requestId == other.requestId &&
        tripId == other.tripId &&
        vehicleId == other.vehicleId &&
        targetVehicleId == other.targetVehicleId &&
        holdUntil == other.holdUntil &&
        expiresAt == other.expiresAt &&
        reasonCode == other.reasonCode &&
        note == other.note;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, action.hashCode);
    _$hash = $jc(_$hash, requestId.hashCode);
    _$hash = $jc(_$hash, tripId.hashCode);
    _$hash = $jc(_$hash, vehicleId.hashCode);
    _$hash = $jc(_$hash, targetVehicleId.hashCode);
    _$hash = $jc(_$hash, holdUntil.hashCode);
    _$hash = $jc(_$hash, expiresAt.hashCode);
    _$hash = $jc(_$hash, reasonCode.hashCode);
    _$hash = $jc(_$hash, note.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'OverrideInput')
          ..add('action', action)
          ..add('requestId', requestId)
          ..add('tripId', tripId)
          ..add('vehicleId', vehicleId)
          ..add('targetVehicleId', targetVehicleId)
          ..add('holdUntil', holdUntil)
          ..add('expiresAt', expiresAt)
          ..add('reasonCode', reasonCode)
          ..add('note', note))
        .toString();
  }
}

class OverrideInputBuilder
    implements Builder<OverrideInput, OverrideInputBuilder> {
  _$OverrideInput? _$v;

  OverrideInputActionEnum? _action;
  OverrideInputActionEnum? get action => _$this._action;
  set action(OverrideInputActionEnum? action) => _$this._action = action;

  String? _requestId;
  String? get requestId => _$this._requestId;
  set requestId(String? requestId) => _$this._requestId = requestId;

  String? _tripId;
  String? get tripId => _$this._tripId;
  set tripId(String? tripId) => _$this._tripId = tripId;

  String? _vehicleId;
  String? get vehicleId => _$this._vehicleId;
  set vehicleId(String? vehicleId) => _$this._vehicleId = vehicleId;

  String? _targetVehicleId;
  String? get targetVehicleId => _$this._targetVehicleId;
  set targetVehicleId(String? targetVehicleId) =>
      _$this._targetVehicleId = targetVehicleId;

  DateTime? _holdUntil;
  DateTime? get holdUntil => _$this._holdUntil;
  set holdUntil(DateTime? holdUntil) => _$this._holdUntil = holdUntil;

  DateTime? _expiresAt;
  DateTime? get expiresAt => _$this._expiresAt;
  set expiresAt(DateTime? expiresAt) => _$this._expiresAt = expiresAt;

  ReasonCode? _reasonCode;
  ReasonCode? get reasonCode => _$this._reasonCode;
  set reasonCode(ReasonCode? reasonCode) => _$this._reasonCode = reasonCode;

  String? _note;
  String? get note => _$this._note;
  set note(String? note) => _$this._note = note;

  OverrideInputBuilder() {
    OverrideInput._defaults(this);
  }

  OverrideInputBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _action = $v.action;
      _requestId = $v.requestId;
      _tripId = $v.tripId;
      _vehicleId = $v.vehicleId;
      _targetVehicleId = $v.targetVehicleId;
      _holdUntil = $v.holdUntil;
      _expiresAt = $v.expiresAt;
      _reasonCode = $v.reasonCode;
      _note = $v.note;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(OverrideInput other) {
    _$v = other as _$OverrideInput;
  }

  @override
  void update(void Function(OverrideInputBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  OverrideInput build() => _build();

  _$OverrideInput _build() {
    final _$result = _$v ??
        _$OverrideInput._(
          action: BuiltValueNullFieldError.checkNotNull(
              action, r'OverrideInput', 'action'),
          requestId: requestId,
          tripId: tripId,
          vehicleId: vehicleId,
          targetVehicleId: targetVehicleId,
          holdUntil: holdUntil,
          expiresAt: expiresAt,
          reasonCode: BuiltValueNullFieldError.checkNotNull(
              reasonCode, r'OverrideInput', 'reasonCode'),
          note: note,
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
