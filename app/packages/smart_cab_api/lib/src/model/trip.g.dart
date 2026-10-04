// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'trip.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

const TripModeUsedEnum _$tripModeUsedEnum_manual =
    const TripModeUsedEnum._('manual');
const TripModeUsedEnum _$tripModeUsedEnum_semiAuto =
    const TripModeUsedEnum._('semiAuto');
const TripModeUsedEnum _$tripModeUsedEnum_fullAuto =
    const TripModeUsedEnum._('fullAuto');
const TripModeUsedEnum _$tripModeUsedEnum_failsafe =
    const TripModeUsedEnum._('failsafe');

TripModeUsedEnum _$tripModeUsedEnumValueOf(String name) {
  switch (name) {
    case 'manual':
      return _$tripModeUsedEnum_manual;
    case 'semiAuto':
      return _$tripModeUsedEnum_semiAuto;
    case 'fullAuto':
      return _$tripModeUsedEnum_fullAuto;
    case 'failsafe':
      return _$tripModeUsedEnum_failsafe;
    default:
      throw ArgumentError(name);
  }
}

final BuiltSet<TripModeUsedEnum> _$tripModeUsedEnumValues =
    BuiltSet<TripModeUsedEnum>(const <TripModeUsedEnum>[
  _$tripModeUsedEnum_manual,
  _$tripModeUsedEnum_semiAuto,
  _$tripModeUsedEnum_fullAuto,
  _$tripModeUsedEnum_failsafe,
]);

Serializer<TripModeUsedEnum> _$tripModeUsedEnumSerializer =
    _$TripModeUsedEnumSerializer();

class _$TripModeUsedEnumSerializer
    implements PrimitiveSerializer<TripModeUsedEnum> {
  static const Map<String, Object> _toWire = const <String, Object>{
    'manual': 'manual',
    'semiAuto': 'semi_auto',
    'fullAuto': 'full_auto',
    'failsafe': 'failsafe',
  };
  static const Map<Object, String> _fromWire = const <Object, String>{
    'manual': 'manual',
    'semi_auto': 'semiAuto',
    'full_auto': 'fullAuto',
    'failsafe': 'failsafe',
  };

  @override
  final Iterable<Type> types = const <Type>[TripModeUsedEnum];
  @override
  final String wireName = 'TripModeUsedEnum';

  @override
  Object serialize(Serializers serializers, TripModeUsedEnum object,
          {FullType specifiedType = FullType.unspecified}) =>
      _toWire[object.name] ?? object.name;

  @override
  TripModeUsedEnum deserialize(Serializers serializers, Object serialized,
          {FullType specifiedType = FullType.unspecified}) =>
      TripModeUsedEnum.valueOf(
          _fromWire[serialized] ?? (serialized is String ? serialized : ''));
}

class _$Trip extends Trip {
  @override
  final String? id;
  @override
  final String? vehicleId;
  @override
  final String? driverId;
  @override
  final Direction? direction;
  @override
  final TripStatus? status;
  @override
  final bool? poolingBlocked;
  @override
  final TripModeUsedEnum? modeUsed;
  @override
  final BuiltList<TripStop>? stops;

  factory _$Trip([void Function(TripBuilder)? updates]) =>
      (TripBuilder()..update(updates))._build();

  _$Trip._(
      {this.id,
      this.vehicleId,
      this.driverId,
      this.direction,
      this.status,
      this.poolingBlocked,
      this.modeUsed,
      this.stops})
      : super._();
  @override
  Trip rebuild(void Function(TripBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  TripBuilder toBuilder() => TripBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is Trip &&
        id == other.id &&
        vehicleId == other.vehicleId &&
        driverId == other.driverId &&
        direction == other.direction &&
        status == other.status &&
        poolingBlocked == other.poolingBlocked &&
        modeUsed == other.modeUsed &&
        stops == other.stops;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, id.hashCode);
    _$hash = $jc(_$hash, vehicleId.hashCode);
    _$hash = $jc(_$hash, driverId.hashCode);
    _$hash = $jc(_$hash, direction.hashCode);
    _$hash = $jc(_$hash, status.hashCode);
    _$hash = $jc(_$hash, poolingBlocked.hashCode);
    _$hash = $jc(_$hash, modeUsed.hashCode);
    _$hash = $jc(_$hash, stops.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'Trip')
          ..add('id', id)
          ..add('vehicleId', vehicleId)
          ..add('driverId', driverId)
          ..add('direction', direction)
          ..add('status', status)
          ..add('poolingBlocked', poolingBlocked)
          ..add('modeUsed', modeUsed)
          ..add('stops', stops))
        .toString();
  }
}

class TripBuilder implements Builder<Trip, TripBuilder> {
  _$Trip? _$v;

  String? _id;
  String? get id => _$this._id;
  set id(String? id) => _$this._id = id;

  String? _vehicleId;
  String? get vehicleId => _$this._vehicleId;
  set vehicleId(String? vehicleId) => _$this._vehicleId = vehicleId;

  String? _driverId;
  String? get driverId => _$this._driverId;
  set driverId(String? driverId) => _$this._driverId = driverId;

  Direction? _direction;
  Direction? get direction => _$this._direction;
  set direction(Direction? direction) => _$this._direction = direction;

  TripStatus? _status;
  TripStatus? get status => _$this._status;
  set status(TripStatus? status) => _$this._status = status;

  bool? _poolingBlocked;
  bool? get poolingBlocked => _$this._poolingBlocked;
  set poolingBlocked(bool? poolingBlocked) =>
      _$this._poolingBlocked = poolingBlocked;

  TripModeUsedEnum? _modeUsed;
  TripModeUsedEnum? get modeUsed => _$this._modeUsed;
  set modeUsed(TripModeUsedEnum? modeUsed) => _$this._modeUsed = modeUsed;

  ListBuilder<TripStop>? _stops;
  ListBuilder<TripStop> get stops => _$this._stops ??= ListBuilder<TripStop>();
  set stops(ListBuilder<TripStop>? stops) => _$this._stops = stops;

  TripBuilder() {
    Trip._defaults(this);
  }

  TripBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _id = $v.id;
      _vehicleId = $v.vehicleId;
      _driverId = $v.driverId;
      _direction = $v.direction;
      _status = $v.status;
      _poolingBlocked = $v.poolingBlocked;
      _modeUsed = $v.modeUsed;
      _stops = $v.stops?.toBuilder();
      _$v = null;
    }
    return this;
  }

  @override
  void replace(Trip other) {
    _$v = other as _$Trip;
  }

  @override
  void update(void Function(TripBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  Trip build() => _build();

  _$Trip _build() {
    _$Trip _$result;
    try {
      _$result = _$v ??
          _$Trip._(
            id: id,
            vehicleId: vehicleId,
            driverId: driverId,
            direction: direction,
            status: status,
            poolingBlocked: poolingBlocked,
            modeUsed: modeUsed,
            stops: _stops?.build(),
          );
    } catch (_) {
      late String _$failedField;
      try {
        _$failedField = 'stops';
        _stops?.build();
      } catch (e) {
        throw BuiltValueNestedFieldError(r'Trip', _$failedField, e.toString());
      }
      rethrow;
    }
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
