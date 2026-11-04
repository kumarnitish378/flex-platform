// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'operations_report_pooling.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$OperationsReportPooling extends OperationsReportPooling {
  @override
  final int? trips;
  @override
  final int? ridersCarried;
  @override
  final num? ridersPerTrip;
  @override
  final int? pooledTrips;
  @override
  final num? poolingRate;
  @override
  final int? vehiclesUsed;

  factory _$OperationsReportPooling(
          [void Function(OperationsReportPoolingBuilder)? updates]) =>
      (OperationsReportPoolingBuilder()..update(updates))._build();

  _$OperationsReportPooling._(
      {this.trips,
      this.ridersCarried,
      this.ridersPerTrip,
      this.pooledTrips,
      this.poolingRate,
      this.vehiclesUsed})
      : super._();
  @override
  OperationsReportPooling rebuild(
          void Function(OperationsReportPoolingBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  OperationsReportPoolingBuilder toBuilder() =>
      OperationsReportPoolingBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is OperationsReportPooling &&
        trips == other.trips &&
        ridersCarried == other.ridersCarried &&
        ridersPerTrip == other.ridersPerTrip &&
        pooledTrips == other.pooledTrips &&
        poolingRate == other.poolingRate &&
        vehiclesUsed == other.vehiclesUsed;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, trips.hashCode);
    _$hash = $jc(_$hash, ridersCarried.hashCode);
    _$hash = $jc(_$hash, ridersPerTrip.hashCode);
    _$hash = $jc(_$hash, pooledTrips.hashCode);
    _$hash = $jc(_$hash, poolingRate.hashCode);
    _$hash = $jc(_$hash, vehiclesUsed.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'OperationsReportPooling')
          ..add('trips', trips)
          ..add('ridersCarried', ridersCarried)
          ..add('ridersPerTrip', ridersPerTrip)
          ..add('pooledTrips', pooledTrips)
          ..add('poolingRate', poolingRate)
          ..add('vehiclesUsed', vehiclesUsed))
        .toString();
  }
}

class OperationsReportPoolingBuilder
    implements
        Builder<OperationsReportPooling, OperationsReportPoolingBuilder> {
  _$OperationsReportPooling? _$v;

  int? _trips;
  int? get trips => _$this._trips;
  set trips(int? trips) => _$this._trips = trips;

  int? _ridersCarried;
  int? get ridersCarried => _$this._ridersCarried;
  set ridersCarried(int? ridersCarried) =>
      _$this._ridersCarried = ridersCarried;

  num? _ridersPerTrip;
  num? get ridersPerTrip => _$this._ridersPerTrip;
  set ridersPerTrip(num? ridersPerTrip) =>
      _$this._ridersPerTrip = ridersPerTrip;

  int? _pooledTrips;
  int? get pooledTrips => _$this._pooledTrips;
  set pooledTrips(int? pooledTrips) => _$this._pooledTrips = pooledTrips;

  num? _poolingRate;
  num? get poolingRate => _$this._poolingRate;
  set poolingRate(num? poolingRate) => _$this._poolingRate = poolingRate;

  int? _vehiclesUsed;
  int? get vehiclesUsed => _$this._vehiclesUsed;
  set vehiclesUsed(int? vehiclesUsed) => _$this._vehiclesUsed = vehiclesUsed;

  OperationsReportPoolingBuilder() {
    OperationsReportPooling._defaults(this);
  }

  OperationsReportPoolingBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _trips = $v.trips;
      _ridersCarried = $v.ridersCarried;
      _ridersPerTrip = $v.ridersPerTrip;
      _pooledTrips = $v.pooledTrips;
      _poolingRate = $v.poolingRate;
      _vehiclesUsed = $v.vehiclesUsed;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(OperationsReportPooling other) {
    _$v = other as _$OperationsReportPooling;
  }

  @override
  void update(void Function(OperationsReportPoolingBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  OperationsReportPooling build() => _build();

  _$OperationsReportPooling _build() {
    final _$result = _$v ??
        _$OperationsReportPooling._(
          trips: trips,
          ridersCarried: ridersCarried,
          ridersPerTrip: ridersPerTrip,
          pooledTrips: pooledTrips,
          poolingRate: poolingRate,
          vehiclesUsed: vehiclesUsed,
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
