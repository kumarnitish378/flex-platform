// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'location_ping.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$LocationPing extends LocationPing {
  @override
  final DateTime ts;
  @override
  final num lat;
  @override
  final num lng;
  @override
  final num? speedMps;
  @override
  final num? headingDeg;
  @override
  final num? accuracyM;
  @override
  final int? batteryPct;

  factory _$LocationPing([void Function(LocationPingBuilder)? updates]) =>
      (LocationPingBuilder()..update(updates))._build();

  _$LocationPing._(
      {required this.ts,
      required this.lat,
      required this.lng,
      this.speedMps,
      this.headingDeg,
      this.accuracyM,
      this.batteryPct})
      : super._();
  @override
  LocationPing rebuild(void Function(LocationPingBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  LocationPingBuilder toBuilder() => LocationPingBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is LocationPing &&
        ts == other.ts &&
        lat == other.lat &&
        lng == other.lng &&
        speedMps == other.speedMps &&
        headingDeg == other.headingDeg &&
        accuracyM == other.accuracyM &&
        batteryPct == other.batteryPct;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, ts.hashCode);
    _$hash = $jc(_$hash, lat.hashCode);
    _$hash = $jc(_$hash, lng.hashCode);
    _$hash = $jc(_$hash, speedMps.hashCode);
    _$hash = $jc(_$hash, headingDeg.hashCode);
    _$hash = $jc(_$hash, accuracyM.hashCode);
    _$hash = $jc(_$hash, batteryPct.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'LocationPing')
          ..add('ts', ts)
          ..add('lat', lat)
          ..add('lng', lng)
          ..add('speedMps', speedMps)
          ..add('headingDeg', headingDeg)
          ..add('accuracyM', accuracyM)
          ..add('batteryPct', batteryPct))
        .toString();
  }
}

class LocationPingBuilder
    implements Builder<LocationPing, LocationPingBuilder> {
  _$LocationPing? _$v;

  DateTime? _ts;
  DateTime? get ts => _$this._ts;
  set ts(DateTime? ts) => _$this._ts = ts;

  num? _lat;
  num? get lat => _$this._lat;
  set lat(num? lat) => _$this._lat = lat;

  num? _lng;
  num? get lng => _$this._lng;
  set lng(num? lng) => _$this._lng = lng;

  num? _speedMps;
  num? get speedMps => _$this._speedMps;
  set speedMps(num? speedMps) => _$this._speedMps = speedMps;

  num? _headingDeg;
  num? get headingDeg => _$this._headingDeg;
  set headingDeg(num? headingDeg) => _$this._headingDeg = headingDeg;

  num? _accuracyM;
  num? get accuracyM => _$this._accuracyM;
  set accuracyM(num? accuracyM) => _$this._accuracyM = accuracyM;

  int? _batteryPct;
  int? get batteryPct => _$this._batteryPct;
  set batteryPct(int? batteryPct) => _$this._batteryPct = batteryPct;

  LocationPingBuilder() {
    LocationPing._defaults(this);
  }

  LocationPingBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _ts = $v.ts;
      _lat = $v.lat;
      _lng = $v.lng;
      _speedMps = $v.speedMps;
      _headingDeg = $v.headingDeg;
      _accuracyM = $v.accuracyM;
      _batteryPct = $v.batteryPct;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(LocationPing other) {
    _$v = other as _$LocationPing;
  }

  @override
  void update(void Function(LocationPingBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  LocationPing build() => _build();

  _$LocationPing _build() {
    final _$result = _$v ??
        _$LocationPing._(
          ts: BuiltValueNullFieldError.checkNotNull(ts, r'LocationPing', 'ts'),
          lat: BuiltValueNullFieldError.checkNotNull(
              lat, r'LocationPing', 'lat'),
          lng: BuiltValueNullFieldError.checkNotNull(
              lng, r'LocationPing', 'lng'),
          speedMps: speedMps,
          headingDeg: headingDeg,
          accuracyM: accuracyM,
          batteryPct: batteryPct,
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
