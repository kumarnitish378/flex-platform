// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'duty_state.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$DutyState extends DutyState {
  @override
  final bool? onDuty;
  @override
  final String? vehicleId;
  @override
  final DutyStateMqtt? mqtt;
  @override
  final DutyStateGps? gps;

  factory _$DutyState([void Function(DutyStateBuilder)? updates]) =>
      (DutyStateBuilder()..update(updates))._build();

  _$DutyState._({this.onDuty, this.vehicleId, this.mqtt, this.gps}) : super._();
  @override
  DutyState rebuild(void Function(DutyStateBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  DutyStateBuilder toBuilder() => DutyStateBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is DutyState &&
        onDuty == other.onDuty &&
        vehicleId == other.vehicleId &&
        mqtt == other.mqtt &&
        gps == other.gps;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, onDuty.hashCode);
    _$hash = $jc(_$hash, vehicleId.hashCode);
    _$hash = $jc(_$hash, mqtt.hashCode);
    _$hash = $jc(_$hash, gps.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'DutyState')
          ..add('onDuty', onDuty)
          ..add('vehicleId', vehicleId)
          ..add('mqtt', mqtt)
          ..add('gps', gps))
        .toString();
  }
}

class DutyStateBuilder implements Builder<DutyState, DutyStateBuilder> {
  _$DutyState? _$v;

  bool? _onDuty;
  bool? get onDuty => _$this._onDuty;
  set onDuty(bool? onDuty) => _$this._onDuty = onDuty;

  String? _vehicleId;
  String? get vehicleId => _$this._vehicleId;
  set vehicleId(String? vehicleId) => _$this._vehicleId = vehicleId;

  DutyStateMqttBuilder? _mqtt;
  DutyStateMqttBuilder get mqtt => _$this._mqtt ??= DutyStateMqttBuilder();
  set mqtt(DutyStateMqttBuilder? mqtt) => _$this._mqtt = mqtt;

  DutyStateGpsBuilder? _gps;
  DutyStateGpsBuilder get gps => _$this._gps ??= DutyStateGpsBuilder();
  set gps(DutyStateGpsBuilder? gps) => _$this._gps = gps;

  DutyStateBuilder() {
    DutyState._defaults(this);
  }

  DutyStateBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _onDuty = $v.onDuty;
      _vehicleId = $v.vehicleId;
      _mqtt = $v.mqtt?.toBuilder();
      _gps = $v.gps?.toBuilder();
      _$v = null;
    }
    return this;
  }

  @override
  void replace(DutyState other) {
    _$v = other as _$DutyState;
  }

  @override
  void update(void Function(DutyStateBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  DutyState build() => _build();

  _$DutyState _build() {
    _$DutyState _$result;
    try {
      _$result = _$v ??
          _$DutyState._(
            onDuty: onDuty,
            vehicleId: vehicleId,
            mqtt: _mqtt?.build(),
            gps: _gps?.build(),
          );
    } catch (_) {
      late String _$failedField;
      try {
        _$failedField = 'mqtt';
        _mqtt?.build();
        _$failedField = 'gps';
        _gps?.build();
      } catch (e) {
        throw BuiltValueNestedFieldError(
            r'DutyState', _$failedField, e.toString());
      }
      rethrow;
    }
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
