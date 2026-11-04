// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'operations_report_optimizer.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$OperationsReportOptimizer extends OperationsReportOptimizer {
  @override
  final int? runs;
  @override
  final int? failed;
  @override
  final int? applied;
  @override
  final int? suggested;
  @override
  final int? hinted;

  factory _$OperationsReportOptimizer(
          [void Function(OperationsReportOptimizerBuilder)? updates]) =>
      (OperationsReportOptimizerBuilder()..update(updates))._build();

  _$OperationsReportOptimizer._(
      {this.runs, this.failed, this.applied, this.suggested, this.hinted})
      : super._();
  @override
  OperationsReportOptimizer rebuild(
          void Function(OperationsReportOptimizerBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  OperationsReportOptimizerBuilder toBuilder() =>
      OperationsReportOptimizerBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is OperationsReportOptimizer &&
        runs == other.runs &&
        failed == other.failed &&
        applied == other.applied &&
        suggested == other.suggested &&
        hinted == other.hinted;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, runs.hashCode);
    _$hash = $jc(_$hash, failed.hashCode);
    _$hash = $jc(_$hash, applied.hashCode);
    _$hash = $jc(_$hash, suggested.hashCode);
    _$hash = $jc(_$hash, hinted.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'OperationsReportOptimizer')
          ..add('runs', runs)
          ..add('failed', failed)
          ..add('applied', applied)
          ..add('suggested', suggested)
          ..add('hinted', hinted))
        .toString();
  }
}

class OperationsReportOptimizerBuilder
    implements
        Builder<OperationsReportOptimizer, OperationsReportOptimizerBuilder> {
  _$OperationsReportOptimizer? _$v;

  int? _runs;
  int? get runs => _$this._runs;
  set runs(int? runs) => _$this._runs = runs;

  int? _failed;
  int? get failed => _$this._failed;
  set failed(int? failed) => _$this._failed = failed;

  int? _applied;
  int? get applied => _$this._applied;
  set applied(int? applied) => _$this._applied = applied;

  int? _suggested;
  int? get suggested => _$this._suggested;
  set suggested(int? suggested) => _$this._suggested = suggested;

  int? _hinted;
  int? get hinted => _$this._hinted;
  set hinted(int? hinted) => _$this._hinted = hinted;

  OperationsReportOptimizerBuilder() {
    OperationsReportOptimizer._defaults(this);
  }

  OperationsReportOptimizerBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _runs = $v.runs;
      _failed = $v.failed;
      _applied = $v.applied;
      _suggested = $v.suggested;
      _hinted = $v.hinted;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(OperationsReportOptimizer other) {
    _$v = other as _$OperationsReportOptimizer;
  }

  @override
  void update(void Function(OperationsReportOptimizerBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  OperationsReportOptimizer build() => _build();

  _$OperationsReportOptimizer _build() {
    final _$result = _$v ??
        _$OperationsReportOptimizer._(
          runs: runs,
          failed: failed,
          applied: applied,
          suggested: suggested,
          hinted: hinted,
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
