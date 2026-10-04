// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'lat_lng.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$LatLng extends LatLng {
  @override
  final num lat;
  @override
  final num lng;

  factory _$LatLng([void Function(LatLngBuilder)? updates]) =>
      (LatLngBuilder()..update(updates))._build();

  _$LatLng._({required this.lat, required this.lng}) : super._();
  @override
  LatLng rebuild(void Function(LatLngBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  LatLngBuilder toBuilder() => LatLngBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is LatLng && lat == other.lat && lng == other.lng;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, lat.hashCode);
    _$hash = $jc(_$hash, lng.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'LatLng')
          ..add('lat', lat)
          ..add('lng', lng))
        .toString();
  }
}

class LatLngBuilder implements Builder<LatLng, LatLngBuilder> {
  _$LatLng? _$v;

  num? _lat;
  num? get lat => _$this._lat;
  set lat(num? lat) => _$this._lat = lat;

  num? _lng;
  num? get lng => _$this._lng;
  set lng(num? lng) => _$this._lng = lng;

  LatLngBuilder() {
    LatLng._defaults(this);
  }

  LatLngBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _lat = $v.lat;
      _lng = $v.lng;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(LatLng other) {
    _$v = other as _$LatLng;
  }

  @override
  void update(void Function(LatLngBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  LatLng build() => _build();

  _$LatLng _build() {
    final _$result = _$v ??
        _$LatLng._(
          lat: BuiltValueNullFieldError.checkNotNull(lat, r'LatLng', 'lat'),
          lng: BuiltValueNullFieldError.checkNotNull(lng, r'LatLng', 'lng'),
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
