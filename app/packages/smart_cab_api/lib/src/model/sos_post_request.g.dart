// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'sos_post_request.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$SosPostRequest extends SosPostRequest {
  @override
  final String? tripId;
  @override
  final num lat;
  @override
  final num lng;

  factory _$SosPostRequest([void Function(SosPostRequestBuilder)? updates]) =>
      (SosPostRequestBuilder()..update(updates))._build();

  _$SosPostRequest._({this.tripId, required this.lat, required this.lng})
      : super._();
  @override
  SosPostRequest rebuild(void Function(SosPostRequestBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  SosPostRequestBuilder toBuilder() => SosPostRequestBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is SosPostRequest &&
        tripId == other.tripId &&
        lat == other.lat &&
        lng == other.lng;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, tripId.hashCode);
    _$hash = $jc(_$hash, lat.hashCode);
    _$hash = $jc(_$hash, lng.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'SosPostRequest')
          ..add('tripId', tripId)
          ..add('lat', lat)
          ..add('lng', lng))
        .toString();
  }
}

class SosPostRequestBuilder
    implements Builder<SosPostRequest, SosPostRequestBuilder> {
  _$SosPostRequest? _$v;

  String? _tripId;
  String? get tripId => _$this._tripId;
  set tripId(String? tripId) => _$this._tripId = tripId;

  num? _lat;
  num? get lat => _$this._lat;
  set lat(num? lat) => _$this._lat = lat;

  num? _lng;
  num? get lng => _$this._lng;
  set lng(num? lng) => _$this._lng = lng;

  SosPostRequestBuilder() {
    SosPostRequest._defaults(this);
  }

  SosPostRequestBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _tripId = $v.tripId;
      _lat = $v.lat;
      _lng = $v.lng;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(SosPostRequest other) {
    _$v = other as _$SosPostRequest;
  }

  @override
  void update(void Function(SosPostRequestBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  SosPostRequest build() => _build();

  _$SosPostRequest _build() {
    final _$result = _$v ??
        _$SosPostRequest._(
          tripId: tripId,
          lat: BuiltValueNullFieldError.checkNotNull(
              lat, r'SosPostRequest', 'lat'),
          lng: BuiltValueNullFieldError.checkNotNull(
              lng, r'SosPostRequest', 'lng'),
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
