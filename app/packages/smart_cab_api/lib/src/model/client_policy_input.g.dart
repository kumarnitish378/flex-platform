// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'client_policy_input.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

abstract class ClientPolicyInputBuilder {
  void replace(ClientPolicyInput other);
  void update(void Function(ClientPolicyInputBuilder) updates);
  bool? get poolingAllowed;
  set poolingAllowed(bool? poolingAllowed);

  bool? get employeeOptOutAllowed;
  set employeeOptOutAllowed(bool? employeeOptOutAllowed);

  bool? get nightSafetyEnabled;
  set nightSafetyEnabled(bool? nightSafetyEnabled);

  String? get nightStart;
  set nightStart(String? nightStart);

  String? get nightEnd;
  set nightEnd(String? nightEnd);

  num? get maxDetourFactor;
  set maxDetourFactor(num? maxDetourFactor);

  int? get maxDetourMinutes;
  set maxDetourMinutes(int? maxDetourMinutes);

  int? get pickupWindowMinutes;
  set pickupWindowMinutes(int? pickupWindowMinutes);

  int? get noShowWaitMinutes;
  set noShowWaitMinutes(int? noShowWaitMinutes);
}

class _$$ClientPolicyInput extends $ClientPolicyInput {
  @override
  final bool? poolingAllowed;
  @override
  final bool? employeeOptOutAllowed;
  @override
  final bool? nightSafetyEnabled;
  @override
  final String? nightStart;
  @override
  final String? nightEnd;
  @override
  final num? maxDetourFactor;
  @override
  final int? maxDetourMinutes;
  @override
  final int? pickupWindowMinutes;
  @override
  final int? noShowWaitMinutes;

  factory _$$ClientPolicyInput(
          [void Function($ClientPolicyInputBuilder)? updates]) =>
      ($ClientPolicyInputBuilder()..update(updates))._build();

  _$$ClientPolicyInput._(
      {this.poolingAllowed,
      this.employeeOptOutAllowed,
      this.nightSafetyEnabled,
      this.nightStart,
      this.nightEnd,
      this.maxDetourFactor,
      this.maxDetourMinutes,
      this.pickupWindowMinutes,
      this.noShowWaitMinutes})
      : super._();
  @override
  $ClientPolicyInput rebuild(
          void Function($ClientPolicyInputBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  $ClientPolicyInputBuilder toBuilder() =>
      $ClientPolicyInputBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is $ClientPolicyInput &&
        poolingAllowed == other.poolingAllowed &&
        employeeOptOutAllowed == other.employeeOptOutAllowed &&
        nightSafetyEnabled == other.nightSafetyEnabled &&
        nightStart == other.nightStart &&
        nightEnd == other.nightEnd &&
        maxDetourFactor == other.maxDetourFactor &&
        maxDetourMinutes == other.maxDetourMinutes &&
        pickupWindowMinutes == other.pickupWindowMinutes &&
        noShowWaitMinutes == other.noShowWaitMinutes;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, poolingAllowed.hashCode);
    _$hash = $jc(_$hash, employeeOptOutAllowed.hashCode);
    _$hash = $jc(_$hash, nightSafetyEnabled.hashCode);
    _$hash = $jc(_$hash, nightStart.hashCode);
    _$hash = $jc(_$hash, nightEnd.hashCode);
    _$hash = $jc(_$hash, maxDetourFactor.hashCode);
    _$hash = $jc(_$hash, maxDetourMinutes.hashCode);
    _$hash = $jc(_$hash, pickupWindowMinutes.hashCode);
    _$hash = $jc(_$hash, noShowWaitMinutes.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'$ClientPolicyInput')
          ..add('poolingAllowed', poolingAllowed)
          ..add('employeeOptOutAllowed', employeeOptOutAllowed)
          ..add('nightSafetyEnabled', nightSafetyEnabled)
          ..add('nightStart', nightStart)
          ..add('nightEnd', nightEnd)
          ..add('maxDetourFactor', maxDetourFactor)
          ..add('maxDetourMinutes', maxDetourMinutes)
          ..add('pickupWindowMinutes', pickupWindowMinutes)
          ..add('noShowWaitMinutes', noShowWaitMinutes))
        .toString();
  }
}

class $ClientPolicyInputBuilder
    implements
        Builder<$ClientPolicyInput, $ClientPolicyInputBuilder>,
        ClientPolicyInputBuilder {
  _$$ClientPolicyInput? _$v;

  bool? _poolingAllowed;
  bool? get poolingAllowed => _$this._poolingAllowed;
  set poolingAllowed(covariant bool? poolingAllowed) =>
      _$this._poolingAllowed = poolingAllowed;

  bool? _employeeOptOutAllowed;
  bool? get employeeOptOutAllowed => _$this._employeeOptOutAllowed;
  set employeeOptOutAllowed(covariant bool? employeeOptOutAllowed) =>
      _$this._employeeOptOutAllowed = employeeOptOutAllowed;

  bool? _nightSafetyEnabled;
  bool? get nightSafetyEnabled => _$this._nightSafetyEnabled;
  set nightSafetyEnabled(covariant bool? nightSafetyEnabled) =>
      _$this._nightSafetyEnabled = nightSafetyEnabled;

  String? _nightStart;
  String? get nightStart => _$this._nightStart;
  set nightStart(covariant String? nightStart) =>
      _$this._nightStart = nightStart;

  String? _nightEnd;
  String? get nightEnd => _$this._nightEnd;
  set nightEnd(covariant String? nightEnd) => _$this._nightEnd = nightEnd;

  num? _maxDetourFactor;
  num? get maxDetourFactor => _$this._maxDetourFactor;
  set maxDetourFactor(covariant num? maxDetourFactor) =>
      _$this._maxDetourFactor = maxDetourFactor;

  int? _maxDetourMinutes;
  int? get maxDetourMinutes => _$this._maxDetourMinutes;
  set maxDetourMinutes(covariant int? maxDetourMinutes) =>
      _$this._maxDetourMinutes = maxDetourMinutes;

  int? _pickupWindowMinutes;
  int? get pickupWindowMinutes => _$this._pickupWindowMinutes;
  set pickupWindowMinutes(covariant int? pickupWindowMinutes) =>
      _$this._pickupWindowMinutes = pickupWindowMinutes;

  int? _noShowWaitMinutes;
  int? get noShowWaitMinutes => _$this._noShowWaitMinutes;
  set noShowWaitMinutes(covariant int? noShowWaitMinutes) =>
      _$this._noShowWaitMinutes = noShowWaitMinutes;

  $ClientPolicyInputBuilder() {
    $ClientPolicyInput._defaults(this);
  }

  $ClientPolicyInputBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _poolingAllowed = $v.poolingAllowed;
      _employeeOptOutAllowed = $v.employeeOptOutAllowed;
      _nightSafetyEnabled = $v.nightSafetyEnabled;
      _nightStart = $v.nightStart;
      _nightEnd = $v.nightEnd;
      _maxDetourFactor = $v.maxDetourFactor;
      _maxDetourMinutes = $v.maxDetourMinutes;
      _pickupWindowMinutes = $v.pickupWindowMinutes;
      _noShowWaitMinutes = $v.noShowWaitMinutes;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(covariant $ClientPolicyInput other) {
    _$v = other as _$$ClientPolicyInput;
  }

  @override
  void update(void Function($ClientPolicyInputBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  $ClientPolicyInput build() => _build();

  _$$ClientPolicyInput _build() {
    final _$result = _$v ??
        _$$ClientPolicyInput._(
          poolingAllowed: poolingAllowed,
          employeeOptOutAllowed: employeeOptOutAllowed,
          nightSafetyEnabled: nightSafetyEnabled,
          nightStart: nightStart,
          nightEnd: nightEnd,
          maxDetourFactor: maxDetourFactor,
          maxDetourMinutes: maxDetourMinutes,
          pickupWindowMinutes: pickupWindowMinutes,
          noShowWaitMinutes: noShowWaitMinutes,
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
