// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'duty_state_gps.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$DutyStateGps extends DutyStateGps {
  @override
  final int distanceFilterM;
  @override
  final int heartbeatSeconds;

  factory _$DutyStateGps([void Function(DutyStateGpsBuilder)? updates]) =>
      (DutyStateGpsBuilder()..update(updates))._build();

  _$DutyStateGps._(
      {required this.distanceFilterM, required this.heartbeatSeconds})
      : super._();
  @override
  DutyStateGps rebuild(void Function(DutyStateGpsBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  DutyStateGpsBuilder toBuilder() => DutyStateGpsBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is DutyStateGps &&
        distanceFilterM == other.distanceFilterM &&
        heartbeatSeconds == other.heartbeatSeconds;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, distanceFilterM.hashCode);
    _$hash = $jc(_$hash, heartbeatSeconds.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'DutyStateGps')
          ..add('distanceFilterM', distanceFilterM)
          ..add('heartbeatSeconds', heartbeatSeconds))
        .toString();
  }
}

class DutyStateGpsBuilder
    implements Builder<DutyStateGps, DutyStateGpsBuilder> {
  _$DutyStateGps? _$v;

  int? _distanceFilterM;
  int? get distanceFilterM => _$this._distanceFilterM;
  set distanceFilterM(int? distanceFilterM) =>
      _$this._distanceFilterM = distanceFilterM;

  int? _heartbeatSeconds;
  int? get heartbeatSeconds => _$this._heartbeatSeconds;
  set heartbeatSeconds(int? heartbeatSeconds) =>
      _$this._heartbeatSeconds = heartbeatSeconds;

  DutyStateGpsBuilder() {
    DutyStateGps._defaults(this);
  }

  DutyStateGpsBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _distanceFilterM = $v.distanceFilterM;
      _heartbeatSeconds = $v.heartbeatSeconds;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(DutyStateGps other) {
    _$v = other as _$DutyStateGps;
  }

  @override
  void update(void Function(DutyStateGpsBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  DutyStateGps build() => _build();

  _$DutyStateGps _build() {
    final _$result = _$v ??
        _$DutyStateGps._(
          distanceFilterM: BuiltValueNullFieldError.checkNotNull(
              distanceFilterM, r'DutyStateGps', 'distanceFilterM'),
          heartbeatSeconds: BuiltValueNullFieldError.checkNotNull(
              heartbeatSeconds, r'DutyStateGps', 'heartbeatSeconds'),
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
