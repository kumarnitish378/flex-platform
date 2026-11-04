// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'client_policy_all_of_effective.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$ClientPolicyAllOfEffective extends ClientPolicyAllOfEffective {
  @override
  final num? maxDetourFactor;
  @override
  final int? maxDetourMinutes;
  @override
  final int? pickupWindowMinutes;
  @override
  final int? noShowWaitMinutes;
  @override
  final bool? nightSafetyEnabled;
  @override
  final String? nightStart;
  @override
  final String? nightEnd;

  factory _$ClientPolicyAllOfEffective(
          [void Function(ClientPolicyAllOfEffectiveBuilder)? updates]) =>
      (ClientPolicyAllOfEffectiveBuilder()..update(updates))._build();

  _$ClientPolicyAllOfEffective._(
      {this.maxDetourFactor,
      this.maxDetourMinutes,
      this.pickupWindowMinutes,
      this.noShowWaitMinutes,
      this.nightSafetyEnabled,
      this.nightStart,
      this.nightEnd})
      : super._();
  @override
  ClientPolicyAllOfEffective rebuild(
          void Function(ClientPolicyAllOfEffectiveBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  ClientPolicyAllOfEffectiveBuilder toBuilder() =>
      ClientPolicyAllOfEffectiveBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is ClientPolicyAllOfEffective &&
        maxDetourFactor == other.maxDetourFactor &&
        maxDetourMinutes == other.maxDetourMinutes &&
        pickupWindowMinutes == other.pickupWindowMinutes &&
        noShowWaitMinutes == other.noShowWaitMinutes &&
        nightSafetyEnabled == other.nightSafetyEnabled &&
        nightStart == other.nightStart &&
        nightEnd == other.nightEnd;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, maxDetourFactor.hashCode);
    _$hash = $jc(_$hash, maxDetourMinutes.hashCode);
    _$hash = $jc(_$hash, pickupWindowMinutes.hashCode);
    _$hash = $jc(_$hash, noShowWaitMinutes.hashCode);
    _$hash = $jc(_$hash, nightSafetyEnabled.hashCode);
    _$hash = $jc(_$hash, nightStart.hashCode);
    _$hash = $jc(_$hash, nightEnd.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'ClientPolicyAllOfEffective')
          ..add('maxDetourFactor', maxDetourFactor)
          ..add('maxDetourMinutes', maxDetourMinutes)
          ..add('pickupWindowMinutes', pickupWindowMinutes)
          ..add('noShowWaitMinutes', noShowWaitMinutes)
          ..add('nightSafetyEnabled', nightSafetyEnabled)
          ..add('nightStart', nightStart)
          ..add('nightEnd', nightEnd))
        .toString();
  }
}

class ClientPolicyAllOfEffectiveBuilder
    implements
        Builder<ClientPolicyAllOfEffective, ClientPolicyAllOfEffectiveBuilder> {
  _$ClientPolicyAllOfEffective? _$v;

  num? _maxDetourFactor;
  num? get maxDetourFactor => _$this._maxDetourFactor;
  set maxDetourFactor(num? maxDetourFactor) =>
      _$this._maxDetourFactor = maxDetourFactor;

  int? _maxDetourMinutes;
  int? get maxDetourMinutes => _$this._maxDetourMinutes;
  set maxDetourMinutes(int? maxDetourMinutes) =>
      _$this._maxDetourMinutes = maxDetourMinutes;

  int? _pickupWindowMinutes;
  int? get pickupWindowMinutes => _$this._pickupWindowMinutes;
  set pickupWindowMinutes(int? pickupWindowMinutes) =>
      _$this._pickupWindowMinutes = pickupWindowMinutes;

  int? _noShowWaitMinutes;
  int? get noShowWaitMinutes => _$this._noShowWaitMinutes;
  set noShowWaitMinutes(int? noShowWaitMinutes) =>
      _$this._noShowWaitMinutes = noShowWaitMinutes;

  bool? _nightSafetyEnabled;
  bool? get nightSafetyEnabled => _$this._nightSafetyEnabled;
  set nightSafetyEnabled(bool? nightSafetyEnabled) =>
      _$this._nightSafetyEnabled = nightSafetyEnabled;

  String? _nightStart;
  String? get nightStart => _$this._nightStart;
  set nightStart(String? nightStart) => _$this._nightStart = nightStart;

  String? _nightEnd;
  String? get nightEnd => _$this._nightEnd;
  set nightEnd(String? nightEnd) => _$this._nightEnd = nightEnd;

  ClientPolicyAllOfEffectiveBuilder() {
    ClientPolicyAllOfEffective._defaults(this);
  }

  ClientPolicyAllOfEffectiveBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _maxDetourFactor = $v.maxDetourFactor;
      _maxDetourMinutes = $v.maxDetourMinutes;
      _pickupWindowMinutes = $v.pickupWindowMinutes;
      _noShowWaitMinutes = $v.noShowWaitMinutes;
      _nightSafetyEnabled = $v.nightSafetyEnabled;
      _nightStart = $v.nightStart;
      _nightEnd = $v.nightEnd;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(ClientPolicyAllOfEffective other) {
    _$v = other as _$ClientPolicyAllOfEffective;
  }

  @override
  void update(void Function(ClientPolicyAllOfEffectiveBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  ClientPolicyAllOfEffective build() => _build();

  _$ClientPolicyAllOfEffective _build() {
    final _$result = _$v ??
        _$ClientPolicyAllOfEffective._(
          maxDetourFactor: maxDetourFactor,
          maxDetourMinutes: maxDetourMinutes,
          pickupWindowMinutes: pickupWindowMinutes,
          noShowWaitMinutes: noShowWaitMinutes,
          nightSafetyEnabled: nightSafetyEnabled,
          nightStart: nightStart,
          nightEnd: nightEnd,
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
