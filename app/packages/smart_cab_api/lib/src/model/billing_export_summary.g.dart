// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'billing_export_summary.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$BillingExportSummary extends BillingExportSummary {
  @override
  final int? cabDays;
  @override
  final int? cabs;
  @override
  final num? gpsKm;
  @override
  final num? odometerKm;
  @override
  final num? billedKm;
  @override
  final num? amount;
  @override
  final int? flaggedDays;

  factory _$BillingExportSummary(
          [void Function(BillingExportSummaryBuilder)? updates]) =>
      (BillingExportSummaryBuilder()..update(updates))._build();

  _$BillingExportSummary._(
      {this.cabDays,
      this.cabs,
      this.gpsKm,
      this.odometerKm,
      this.billedKm,
      this.amount,
      this.flaggedDays})
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
        cabDays == other.cabDays &&
        cabs == other.cabs &&
        gpsKm == other.gpsKm &&
        odometerKm == other.odometerKm &&
        billedKm == other.billedKm &&
        amount == other.amount &&
        flaggedDays == other.flaggedDays;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, cabDays.hashCode);
    _$hash = $jc(_$hash, cabs.hashCode);
    _$hash = $jc(_$hash, gpsKm.hashCode);
    _$hash = $jc(_$hash, odometerKm.hashCode);
    _$hash = $jc(_$hash, billedKm.hashCode);
    _$hash = $jc(_$hash, amount.hashCode);
    _$hash = $jc(_$hash, flaggedDays.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'BillingExportSummary')
          ..add('cabDays', cabDays)
          ..add('cabs', cabs)
          ..add('gpsKm', gpsKm)
          ..add('odometerKm', odometerKm)
          ..add('billedKm', billedKm)
          ..add('amount', amount)
          ..add('flaggedDays', flaggedDays))
        .toString();
  }
}

class BillingExportSummaryBuilder
    implements Builder<BillingExportSummary, BillingExportSummaryBuilder> {
  _$BillingExportSummary? _$v;

  int? _cabDays;
  int? get cabDays => _$this._cabDays;
  set cabDays(int? cabDays) => _$this._cabDays = cabDays;

  int? _cabs;
  int? get cabs => _$this._cabs;
  set cabs(int? cabs) => _$this._cabs = cabs;

  num? _gpsKm;
  num? get gpsKm => _$this._gpsKm;
  set gpsKm(num? gpsKm) => _$this._gpsKm = gpsKm;

  num? _odometerKm;
  num? get odometerKm => _$this._odometerKm;
  set odometerKm(num? odometerKm) => _$this._odometerKm = odometerKm;

  num? _billedKm;
  num? get billedKm => _$this._billedKm;
  set billedKm(num? billedKm) => _$this._billedKm = billedKm;

  num? _amount;
  num? get amount => _$this._amount;
  set amount(num? amount) => _$this._amount = amount;

  int? _flaggedDays;
  int? get flaggedDays => _$this._flaggedDays;
  set flaggedDays(int? flaggedDays) => _$this._flaggedDays = flaggedDays;

  BillingExportSummaryBuilder() {
    BillingExportSummary._defaults(this);
  }

  BillingExportSummaryBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _cabDays = $v.cabDays;
      _cabs = $v.cabs;
      _gpsKm = $v.gpsKm;
      _odometerKm = $v.odometerKm;
      _billedKm = $v.billedKm;
      _amount = $v.amount;
      _flaggedDays = $v.flaggedDays;
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
          cabDays: cabDays,
          cabs: cabs,
          gpsKm: gpsKm,
          odometerKm: odometerKm,
          billedKm: billedKm,
          amount: amount,
          flaggedDays: flaggedDays,
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
