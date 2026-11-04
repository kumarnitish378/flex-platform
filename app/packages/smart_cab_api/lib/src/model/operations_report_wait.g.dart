// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'operations_report_wait.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$OperationsReportWait extends OperationsReportWait {
  @override
  final int? measured;
  @override
  final num? medianMinutes;
  @override
  final num? p90Minutes;
  @override
  final BuiltMap<String, int>? distribution;

  factory _$OperationsReportWait(
          [void Function(OperationsReportWaitBuilder)? updates]) =>
      (OperationsReportWaitBuilder()..update(updates))._build();

  _$OperationsReportWait._(
      {this.measured, this.medianMinutes, this.p90Minutes, this.distribution})
      : super._();
  @override
  OperationsReportWait rebuild(
          void Function(OperationsReportWaitBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  OperationsReportWaitBuilder toBuilder() =>
      OperationsReportWaitBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is OperationsReportWait &&
        measured == other.measured &&
        medianMinutes == other.medianMinutes &&
        p90Minutes == other.p90Minutes &&
        distribution == other.distribution;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, measured.hashCode);
    _$hash = $jc(_$hash, medianMinutes.hashCode);
    _$hash = $jc(_$hash, p90Minutes.hashCode);
    _$hash = $jc(_$hash, distribution.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'OperationsReportWait')
          ..add('measured', measured)
          ..add('medianMinutes', medianMinutes)
          ..add('p90Minutes', p90Minutes)
          ..add('distribution', distribution))
        .toString();
  }
}

class OperationsReportWaitBuilder
    implements Builder<OperationsReportWait, OperationsReportWaitBuilder> {
  _$OperationsReportWait? _$v;

  int? _measured;
  int? get measured => _$this._measured;
  set measured(int? measured) => _$this._measured = measured;

  num? _medianMinutes;
  num? get medianMinutes => _$this._medianMinutes;
  set medianMinutes(num? medianMinutes) =>
      _$this._medianMinutes = medianMinutes;

  num? _p90Minutes;
  num? get p90Minutes => _$this._p90Minutes;
  set p90Minutes(num? p90Minutes) => _$this._p90Minutes = p90Minutes;

  MapBuilder<String, int>? _distribution;
  MapBuilder<String, int> get distribution =>
      _$this._distribution ??= MapBuilder<String, int>();
  set distribution(MapBuilder<String, int>? distribution) =>
      _$this._distribution = distribution;

  OperationsReportWaitBuilder() {
    OperationsReportWait._defaults(this);
  }

  OperationsReportWaitBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _measured = $v.measured;
      _medianMinutes = $v.medianMinutes;
      _p90Minutes = $v.p90Minutes;
      _distribution = $v.distribution?.toBuilder();
      _$v = null;
    }
    return this;
  }

  @override
  void replace(OperationsReportWait other) {
    _$v = other as _$OperationsReportWait;
  }

  @override
  void update(void Function(OperationsReportWaitBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  OperationsReportWait build() => _build();

  _$OperationsReportWait _build() {
    _$OperationsReportWait _$result;
    try {
      _$result = _$v ??
          _$OperationsReportWait._(
            measured: measured,
            medianMinutes: medianMinutes,
            p90Minutes: p90Minutes,
            distribution: _distribution?.build(),
          );
    } catch (_) {
      late String _$failedField;
      try {
        _$failedField = 'distribution';
        _distribution?.build();
      } catch (e) {
        throw BuiltValueNestedFieldError(
            r'OperationsReportWait', _$failedField, e.toString());
      }
      rethrow;
    }
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
