// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'operations_report_distance.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$OperationsReportDistance extends OperationsReportDistance {
  @override
  final int? tripsMeasured;
  @override
  final num? cabKmTotal;
  @override
  final num? cabKmPerTrip;
  @override
  final num? cabKmPerRider;

  factory _$OperationsReportDistance(
          [void Function(OperationsReportDistanceBuilder)? updates]) =>
      (OperationsReportDistanceBuilder()..update(updates))._build();

  _$OperationsReportDistance._(
      {this.tripsMeasured,
      this.cabKmTotal,
      this.cabKmPerTrip,
      this.cabKmPerRider})
      : super._();
  @override
  OperationsReportDistance rebuild(
          void Function(OperationsReportDistanceBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  OperationsReportDistanceBuilder toBuilder() =>
      OperationsReportDistanceBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is OperationsReportDistance &&
        tripsMeasured == other.tripsMeasured &&
        cabKmTotal == other.cabKmTotal &&
        cabKmPerTrip == other.cabKmPerTrip &&
        cabKmPerRider == other.cabKmPerRider;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, tripsMeasured.hashCode);
    _$hash = $jc(_$hash, cabKmTotal.hashCode);
    _$hash = $jc(_$hash, cabKmPerTrip.hashCode);
    _$hash = $jc(_$hash, cabKmPerRider.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'OperationsReportDistance')
          ..add('tripsMeasured', tripsMeasured)
          ..add('cabKmTotal', cabKmTotal)
          ..add('cabKmPerTrip', cabKmPerTrip)
          ..add('cabKmPerRider', cabKmPerRider))
        .toString();
  }
}

class OperationsReportDistanceBuilder
    implements
        Builder<OperationsReportDistance, OperationsReportDistanceBuilder> {
  _$OperationsReportDistance? _$v;

  int? _tripsMeasured;
  int? get tripsMeasured => _$this._tripsMeasured;
  set tripsMeasured(int? tripsMeasured) =>
      _$this._tripsMeasured = tripsMeasured;

  num? _cabKmTotal;
  num? get cabKmTotal => _$this._cabKmTotal;
  set cabKmTotal(num? cabKmTotal) => _$this._cabKmTotal = cabKmTotal;

  num? _cabKmPerTrip;
  num? get cabKmPerTrip => _$this._cabKmPerTrip;
  set cabKmPerTrip(num? cabKmPerTrip) => _$this._cabKmPerTrip = cabKmPerTrip;

  num? _cabKmPerRider;
  num? get cabKmPerRider => _$this._cabKmPerRider;
  set cabKmPerRider(num? cabKmPerRider) =>
      _$this._cabKmPerRider = cabKmPerRider;

  OperationsReportDistanceBuilder() {
    OperationsReportDistance._defaults(this);
  }

  OperationsReportDistanceBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _tripsMeasured = $v.tripsMeasured;
      _cabKmTotal = $v.cabKmTotal;
      _cabKmPerTrip = $v.cabKmPerTrip;
      _cabKmPerRider = $v.cabKmPerRider;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(OperationsReportDistance other) {
    _$v = other as _$OperationsReportDistance;
  }

  @override
  void update(void Function(OperationsReportDistanceBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  OperationsReportDistance build() => _build();

  _$OperationsReportDistance _build() {
    final _$result = _$v ??
        _$OperationsReportDistance._(
          tripsMeasured: tripsMeasured,
          cabKmTotal: cabKmTotal,
          cabKmPerTrip: cabKmPerTrip,
          cabKmPerRider: cabKmPerRider,
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
