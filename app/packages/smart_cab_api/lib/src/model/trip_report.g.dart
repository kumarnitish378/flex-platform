// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'trip_report.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$TripReport extends TripReport {
  @override
  final int? trips;
  @override
  final int? requests;
  @override
  final num? medianWaitMinutes;
  @override
  final num? p90WaitMinutes;
  @override
  final int? noShows;
  @override
  final int? cancellations;
  @override
  final BuiltList<BuiltMap<String, JsonObject?>>? rows;

  factory _$TripReport([void Function(TripReportBuilder)? updates]) =>
      (TripReportBuilder()..update(updates))._build();

  _$TripReport._(
      {this.trips,
      this.requests,
      this.medianWaitMinutes,
      this.p90WaitMinutes,
      this.noShows,
      this.cancellations,
      this.rows})
      : super._();
  @override
  TripReport rebuild(void Function(TripReportBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  TripReportBuilder toBuilder() => TripReportBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is TripReport &&
        trips == other.trips &&
        requests == other.requests &&
        medianWaitMinutes == other.medianWaitMinutes &&
        p90WaitMinutes == other.p90WaitMinutes &&
        noShows == other.noShows &&
        cancellations == other.cancellations &&
        rows == other.rows;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, trips.hashCode);
    _$hash = $jc(_$hash, requests.hashCode);
    _$hash = $jc(_$hash, medianWaitMinutes.hashCode);
    _$hash = $jc(_$hash, p90WaitMinutes.hashCode);
    _$hash = $jc(_$hash, noShows.hashCode);
    _$hash = $jc(_$hash, cancellations.hashCode);
    _$hash = $jc(_$hash, rows.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'TripReport')
          ..add('trips', trips)
          ..add('requests', requests)
          ..add('medianWaitMinutes', medianWaitMinutes)
          ..add('p90WaitMinutes', p90WaitMinutes)
          ..add('noShows', noShows)
          ..add('cancellations', cancellations)
          ..add('rows', rows))
        .toString();
  }
}

class TripReportBuilder implements Builder<TripReport, TripReportBuilder> {
  _$TripReport? _$v;

  int? _trips;
  int? get trips => _$this._trips;
  set trips(int? trips) => _$this._trips = trips;

  int? _requests;
  int? get requests => _$this._requests;
  set requests(int? requests) => _$this._requests = requests;

  num? _medianWaitMinutes;
  num? get medianWaitMinutes => _$this._medianWaitMinutes;
  set medianWaitMinutes(num? medianWaitMinutes) =>
      _$this._medianWaitMinutes = medianWaitMinutes;

  num? _p90WaitMinutes;
  num? get p90WaitMinutes => _$this._p90WaitMinutes;
  set p90WaitMinutes(num? p90WaitMinutes) =>
      _$this._p90WaitMinutes = p90WaitMinutes;

  int? _noShows;
  int? get noShows => _$this._noShows;
  set noShows(int? noShows) => _$this._noShows = noShows;

  int? _cancellations;
  int? get cancellations => _$this._cancellations;
  set cancellations(int? cancellations) =>
      _$this._cancellations = cancellations;

  ListBuilder<BuiltMap<String, JsonObject?>>? _rows;
  ListBuilder<BuiltMap<String, JsonObject?>> get rows =>
      _$this._rows ??= ListBuilder<BuiltMap<String, JsonObject?>>();
  set rows(ListBuilder<BuiltMap<String, JsonObject?>>? rows) =>
      _$this._rows = rows;

  TripReportBuilder() {
    TripReport._defaults(this);
  }

  TripReportBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _trips = $v.trips;
      _requests = $v.requests;
      _medianWaitMinutes = $v.medianWaitMinutes;
      _p90WaitMinutes = $v.p90WaitMinutes;
      _noShows = $v.noShows;
      _cancellations = $v.cancellations;
      _rows = $v.rows?.toBuilder();
      _$v = null;
    }
    return this;
  }

  @override
  void replace(TripReport other) {
    _$v = other as _$TripReport;
  }

  @override
  void update(void Function(TripReportBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  TripReport build() => _build();

  _$TripReport _build() {
    _$TripReport _$result;
    try {
      _$result = _$v ??
          _$TripReport._(
            trips: trips,
            requests: requests,
            medianWaitMinutes: medianWaitMinutes,
            p90WaitMinutes: p90WaitMinutes,
            noShows: noShows,
            cancellations: cancellations,
            rows: _rows?.build(),
          );
    } catch (_) {
      late String _$failedField;
      try {
        _$failedField = 'rows';
        _rows?.build();
      } catch (e) {
        throw BuiltValueNestedFieldError(
            r'TripReport', _$failedField, e.toString());
      }
      rethrow;
    }
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
