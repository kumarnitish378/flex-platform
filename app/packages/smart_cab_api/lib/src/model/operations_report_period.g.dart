// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'operations_report_period.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$OperationsReportPeriod extends OperationsReportPeriod {
  @override
  final Date? from;
  @override
  final Date? to;

  factory _$OperationsReportPeriod(
          [void Function(OperationsReportPeriodBuilder)? updates]) =>
      (OperationsReportPeriodBuilder()..update(updates))._build();

  _$OperationsReportPeriod._({this.from, this.to}) : super._();
  @override
  OperationsReportPeriod rebuild(
          void Function(OperationsReportPeriodBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  OperationsReportPeriodBuilder toBuilder() =>
      OperationsReportPeriodBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is OperationsReportPeriod &&
        from == other.from &&
        to == other.to;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, from.hashCode);
    _$hash = $jc(_$hash, to.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'OperationsReportPeriod')
          ..add('from', from)
          ..add('to', to))
        .toString();
  }
}

class OperationsReportPeriodBuilder
    implements Builder<OperationsReportPeriod, OperationsReportPeriodBuilder> {
  _$OperationsReportPeriod? _$v;

  Date? _from;
  Date? get from => _$this._from;
  set from(Date? from) => _$this._from = from;

  Date? _to;
  Date? get to => _$this._to;
  set to(Date? to) => _$this._to = to;

  OperationsReportPeriodBuilder() {
    OperationsReportPeriod._defaults(this);
  }

  OperationsReportPeriodBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _from = $v.from;
      _to = $v.to;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(OperationsReportPeriod other) {
    _$v = other as _$OperationsReportPeriod;
  }

  @override
  void update(void Function(OperationsReportPeriodBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  OperationsReportPeriod build() => _build();

  _$OperationsReportPeriod _build() {
    final _$result = _$v ??
        _$OperationsReportPeriod._(
          from: from,
          to: to,
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
