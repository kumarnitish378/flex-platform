// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'override_result.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$OverrideResult extends OverrideResult {
  @override
  final String? overrideId;
  @override
  final Impact? impact;

  factory _$OverrideResult([void Function(OverrideResultBuilder)? updates]) =>
      (OverrideResultBuilder()..update(updates))._build();

  _$OverrideResult._({this.overrideId, this.impact}) : super._();
  @override
  OverrideResult rebuild(void Function(OverrideResultBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  OverrideResultBuilder toBuilder() => OverrideResultBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is OverrideResult &&
        overrideId == other.overrideId &&
        impact == other.impact;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, overrideId.hashCode);
    _$hash = $jc(_$hash, impact.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'OverrideResult')
          ..add('overrideId', overrideId)
          ..add('impact', impact))
        .toString();
  }
}

class OverrideResultBuilder
    implements Builder<OverrideResult, OverrideResultBuilder> {
  _$OverrideResult? _$v;

  String? _overrideId;
  String? get overrideId => _$this._overrideId;
  set overrideId(String? overrideId) => _$this._overrideId = overrideId;

  ImpactBuilder? _impact;
  ImpactBuilder get impact => _$this._impact ??= ImpactBuilder();
  set impact(ImpactBuilder? impact) => _$this._impact = impact;

  OverrideResultBuilder() {
    OverrideResult._defaults(this);
  }

  OverrideResultBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _overrideId = $v.overrideId;
      _impact = $v.impact?.toBuilder();
      _$v = null;
    }
    return this;
  }

  @override
  void replace(OverrideResult other) {
    _$v = other as _$OverrideResult;
  }

  @override
  void update(void Function(OverrideResultBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  OverrideResult build() => _build();

  _$OverrideResult _build() {
    _$OverrideResult _$result;
    try {
      _$result = _$v ??
          _$OverrideResult._(
            overrideId: overrideId,
            impact: _impact?.build(),
          );
    } catch (_) {
      late String _$failedField;
      try {
        _$failedField = 'impact';
        _impact?.build();
      } catch (e) {
        throw BuiltValueNestedFieldError(
            r'OverrideResult', _$failedField, e.toString());
      }
      rethrow;
    }
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
