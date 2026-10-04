// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'impact.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$Impact extends Impact {
  @override
  final BuiltList<ImpactAffectedRequestsInner>? affectedRequests;
  @override
  final BuiltList<String>? zonesWithoutAvailableVehicle;
  @override
  final BuiltList<String>? hardRuleViolations;

  factory _$Impact([void Function(ImpactBuilder)? updates]) =>
      (ImpactBuilder()..update(updates))._build();

  _$Impact._(
      {this.affectedRequests,
      this.zonesWithoutAvailableVehicle,
      this.hardRuleViolations})
      : super._();
  @override
  Impact rebuild(void Function(ImpactBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  ImpactBuilder toBuilder() => ImpactBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is Impact &&
        affectedRequests == other.affectedRequests &&
        zonesWithoutAvailableVehicle == other.zonesWithoutAvailableVehicle &&
        hardRuleViolations == other.hardRuleViolations;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, affectedRequests.hashCode);
    _$hash = $jc(_$hash, zonesWithoutAvailableVehicle.hashCode);
    _$hash = $jc(_$hash, hardRuleViolations.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'Impact')
          ..add('affectedRequests', affectedRequests)
          ..add('zonesWithoutAvailableVehicle', zonesWithoutAvailableVehicle)
          ..add('hardRuleViolations', hardRuleViolations))
        .toString();
  }
}

class ImpactBuilder implements Builder<Impact, ImpactBuilder> {
  _$Impact? _$v;

  ListBuilder<ImpactAffectedRequestsInner>? _affectedRequests;
  ListBuilder<ImpactAffectedRequestsInner> get affectedRequests =>
      _$this._affectedRequests ??= ListBuilder<ImpactAffectedRequestsInner>();
  set affectedRequests(
          ListBuilder<ImpactAffectedRequestsInner>? affectedRequests) =>
      _$this._affectedRequests = affectedRequests;

  ListBuilder<String>? _zonesWithoutAvailableVehicle;
  ListBuilder<String> get zonesWithoutAvailableVehicle =>
      _$this._zonesWithoutAvailableVehicle ??= ListBuilder<String>();
  set zonesWithoutAvailableVehicle(
          ListBuilder<String>? zonesWithoutAvailableVehicle) =>
      _$this._zonesWithoutAvailableVehicle = zonesWithoutAvailableVehicle;

  ListBuilder<String>? _hardRuleViolations;
  ListBuilder<String> get hardRuleViolations =>
      _$this._hardRuleViolations ??= ListBuilder<String>();
  set hardRuleViolations(ListBuilder<String>? hardRuleViolations) =>
      _$this._hardRuleViolations = hardRuleViolations;

  ImpactBuilder() {
    Impact._defaults(this);
  }

  ImpactBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _affectedRequests = $v.affectedRequests?.toBuilder();
      _zonesWithoutAvailableVehicle =
          $v.zonesWithoutAvailableVehicle?.toBuilder();
      _hardRuleViolations = $v.hardRuleViolations?.toBuilder();
      _$v = null;
    }
    return this;
  }

  @override
  void replace(Impact other) {
    _$v = other as _$Impact;
  }

  @override
  void update(void Function(ImpactBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  Impact build() => _build();

  _$Impact _build() {
    _$Impact _$result;
    try {
      _$result = _$v ??
          _$Impact._(
            affectedRequests: _affectedRequests?.build(),
            zonesWithoutAvailableVehicle:
                _zonesWithoutAvailableVehicle?.build(),
            hardRuleViolations: _hardRuleViolations?.build(),
          );
    } catch (_) {
      late String _$failedField;
      try {
        _$failedField = 'affectedRequests';
        _affectedRequests?.build();
        _$failedField = 'zonesWithoutAvailableVehicle';
        _zonesWithoutAvailableVehicle?.build();
        _$failedField = 'hardRuleViolations';
        _hardRuleViolations?.build();
      } catch (e) {
        throw BuiltValueNestedFieldError(
            r'Impact', _$failedField, e.toString());
      }
      rethrow;
    }
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
