// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'operations_report_overrides.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$OperationsReportOverrides extends OperationsReportOverrides {
  @override
  final int? total;
  @override
  final int? hardRuleOverrides;
  @override
  final BuiltMap<String, int>? byReason;
  @override
  final BuiltMap<String, int>? byAction;

  factory _$OperationsReportOverrides(
          [void Function(OperationsReportOverridesBuilder)? updates]) =>
      (OperationsReportOverridesBuilder()..update(updates))._build();

  _$OperationsReportOverrides._(
      {this.total, this.hardRuleOverrides, this.byReason, this.byAction})
      : super._();
  @override
  OperationsReportOverrides rebuild(
          void Function(OperationsReportOverridesBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  OperationsReportOverridesBuilder toBuilder() =>
      OperationsReportOverridesBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is OperationsReportOverrides &&
        total == other.total &&
        hardRuleOverrides == other.hardRuleOverrides &&
        byReason == other.byReason &&
        byAction == other.byAction;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, total.hashCode);
    _$hash = $jc(_$hash, hardRuleOverrides.hashCode);
    _$hash = $jc(_$hash, byReason.hashCode);
    _$hash = $jc(_$hash, byAction.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'OperationsReportOverrides')
          ..add('total', total)
          ..add('hardRuleOverrides', hardRuleOverrides)
          ..add('byReason', byReason)
          ..add('byAction', byAction))
        .toString();
  }
}

class OperationsReportOverridesBuilder
    implements
        Builder<OperationsReportOverrides, OperationsReportOverridesBuilder> {
  _$OperationsReportOverrides? _$v;

  int? _total;
  int? get total => _$this._total;
  set total(int? total) => _$this._total = total;

  int? _hardRuleOverrides;
  int? get hardRuleOverrides => _$this._hardRuleOverrides;
  set hardRuleOverrides(int? hardRuleOverrides) =>
      _$this._hardRuleOverrides = hardRuleOverrides;

  MapBuilder<String, int>? _byReason;
  MapBuilder<String, int> get byReason =>
      _$this._byReason ??= MapBuilder<String, int>();
  set byReason(MapBuilder<String, int>? byReason) =>
      _$this._byReason = byReason;

  MapBuilder<String, int>? _byAction;
  MapBuilder<String, int> get byAction =>
      _$this._byAction ??= MapBuilder<String, int>();
  set byAction(MapBuilder<String, int>? byAction) =>
      _$this._byAction = byAction;

  OperationsReportOverridesBuilder() {
    OperationsReportOverrides._defaults(this);
  }

  OperationsReportOverridesBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _total = $v.total;
      _hardRuleOverrides = $v.hardRuleOverrides;
      _byReason = $v.byReason?.toBuilder();
      _byAction = $v.byAction?.toBuilder();
      _$v = null;
    }
    return this;
  }

  @override
  void replace(OperationsReportOverrides other) {
    _$v = other as _$OperationsReportOverrides;
  }

  @override
  void update(void Function(OperationsReportOverridesBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  OperationsReportOverrides build() => _build();

  _$OperationsReportOverrides _build() {
    _$OperationsReportOverrides _$result;
    try {
      _$result = _$v ??
          _$OperationsReportOverrides._(
            total: total,
            hardRuleOverrides: hardRuleOverrides,
            byReason: _byReason?.build(),
            byAction: _byAction?.build(),
          );
    } catch (_) {
      late String _$failedField;
      try {
        _$failedField = 'byReason';
        _byReason?.build();
        _$failedField = 'byAction';
        _byAction?.build();
      } catch (e) {
        throw BuiltValueNestedFieldError(
            r'OperationsReportOverrides', _$failedField, e.toString());
      }
      rethrow;
    }
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
