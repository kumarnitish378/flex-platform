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

  factory _$DutyState([void Function(DutyStateBuilder)? updates]) =>
      (DutyStateBuilder()..update(updates))._build();

  _$DutyState._({this.onDuty, this.vehicleId, this.mqtt}) : super._();
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
        mqtt == other.mqtt;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, onDuty.hashCode);
    _$hash = $jc(_$hash, vehicleId.hashCode);
    _$hash = $jc(_$hash, mqtt.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'DutyState')
          ..add('onDuty', onDuty)
          ..add('vehicleId', vehicleId)
          ..add('mqtt', mqtt))
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

  DutyStateBuilder() {
    DutyState._defaults(this);
  }

  DutyStateBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _onDuty = $v.onDuty;
      _vehicleId = $v.vehicleId;
      _mqtt = $v.mqtt?.toBuilder();
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
          );
    } catch (_) {
      late String _$failedField;
      try {
        _$failedField = 'mqtt';
        _mqtt?.build();
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
