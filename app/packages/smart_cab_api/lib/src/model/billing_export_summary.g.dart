// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'billing_export_summary.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$BillingExportSummary extends BillingExportSummary {
  @override
  final int? rides;
  @override
  final int? billableRides;
  @override
  final int? completed;
  @override
  final int? noShows;
  @override
  final int? cancellations;
  @override
  final int? billableTrips;
  @override
  final int? riders;
  @override
  final num? billableKm;

  factory _$BillingExportSummary(
          [void Function(BillingExportSummaryBuilder)? updates]) =>
      (BillingExportSummaryBuilder()..update(updates))._build();

  _$BillingExportSummary._(
      {this.rides,
      this.billableRides,
      this.completed,
      this.noShows,
      this.cancellations,
      this.billableTrips,
      this.riders,
      this.billableKm})
      : super._();
  @override
  BillingExportSummary rebuild(
          void Function(BillingExportSummaryBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  BillingExportSummaryBuilder toBuilder() =>
      BillingExportSummaryBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is BillingExportSummary &&
        rides == other.rides &&
        billableRides == other.billableRides &&
        completed == other.completed &&
        noShows == other.noShows &&
        cancellations == other.cancellations &&
        billableTrips == other.billableTrips &&
        riders == other.riders &&
        billableKm == other.billableKm;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, rides.hashCode);
    _$hash = $jc(_$hash, billableRides.hashCode);
    _$hash = $jc(_$hash, completed.hashCode);
    _$hash = $jc(_$hash, noShows.hashCode);
    _$hash = $jc(_$hash, cancellations.hashCode);
    _$hash = $jc(_$hash, billableTrips.hashCode);
    _$hash = $jc(_$hash, riders.hashCode);
    _$hash = $jc(_$hash, billableKm.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'BillingExportSummary')
          ..add('rides', rides)
          ..add('billableRides', billableRides)
          ..add('completed', completed)
          ..add('noShows', noShows)
          ..add('cancellations', cancellations)
          ..add('billableTrips', billableTrips)
          ..add('riders', riders)
          ..add('billableKm', billableKm))
        .toString();
  }
}

class BillingExportSummaryBuilder
    implements Builder<BillingExportSummary, BillingExportSummaryBuilder> {
  _$BillingExportSummary? _$v;

  int? _rides;
  int? get rides => _$this._rides;
  set rides(int? rides) => _$this._rides = rides;

  int? _billableRides;
  int? get billableRides => _$this._billableRides;
  set billableRides(int? billableRides) =>
      _$this._billableRides = billableRides;

  int? _completed;
  int? get completed => _$this._completed;
  set completed(int? completed) => _$this._completed = completed;

  int? _noShows;
  int? get noShows => _$this._noShows;
  set noShows(int? noShows) => _$this._noShows = noShows;

  int? _cancellations;
  int? get cancellations => _$this._cancellations;
  set cancellations(int? cancellations) =>
      _$this._cancellations = cancellations;

  int? _billableTrips;
  int? get billableTrips => _$this._billableTrips;
  set billableTrips(int? billableTrips) =>
      _$this._billableTrips = billableTrips;

  int? _riders;
  int? get riders => _$this._riders;
  set riders(int? riders) => _$this._riders = riders;

  num? _billableKm;
  num? get billableKm => _$this._billableKm;
  set billableKm(num? billableKm) => _$this._billableKm = billableKm;

  BillingExportSummaryBuilder() {
    BillingExportSummary._defaults(this);
  }

  BillingExportSummaryBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _rides = $v.rides;
      _billableRides = $v.billableRides;
      _completed = $v.completed;
      _noShows = $v.noShows;
      _cancellations = $v.cancellations;
      _billableTrips = $v.billableTrips;
      _riders = $v.riders;
      _billableKm = $v.billableKm;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(BillingExportSummary other) {
    _$v = other as _$BillingExportSummary;
  }

  @override
  void update(void Function(BillingExportSummaryBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  BillingExportSummary build() => _build();

  _$BillingExportSummary _build() {
    final _$result = _$v ??
        _$BillingExportSummary._(
          rides: rides,
          billableRides: billableRides,
          completed: completed,
          noShows: noShows,
          cancellations: cancellations,
          billableTrips: billableTrips,
          riders: riders,
          billableKm: billableKm,
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
