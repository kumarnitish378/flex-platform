// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'driver_trips_trip_id_start_post_request.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$DriverTripsTripIdStartPostRequest
    extends DriverTripsTripIdStartPostRequest {
  @override
  final String clientEventId;
  @override
  final DateTime occurredAt;
  @override
  final num? lat;
  @override
  final num? lng;

  factory _$DriverTripsTripIdStartPostRequest(
          [void Function(DriverTripsTripIdStartPostRequestBuilder)? updates]) =>
      (DriverTripsTripIdStartPostRequestBuilder()..update(updates))._build();

  _$DriverTripsTripIdStartPostRequest._(
      {required this.clientEventId,
      required this.occurredAt,
      this.lat,
      this.lng})
      : super._();
  @override
  DriverTripsTripIdStartPostRequest rebuild(
          void Function(DriverTripsTripIdStartPostRequestBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  DriverTripsTripIdStartPostRequestBuilder toBuilder() =>
      DriverTripsTripIdStartPostRequestBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is DriverTripsTripIdStartPostRequest &&
        clientEventId == other.clientEventId &&
        occurredAt == other.occurredAt &&
        lat == other.lat &&
        lng == other.lng;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, clientEventId.hashCode);
    _$hash = $jc(_$hash, occurredAt.hashCode);
    _$hash = $jc(_$hash, lat.hashCode);
    _$hash = $jc(_$hash, lng.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'DriverTripsTripIdStartPostRequest')
          ..add('clientEventId', clientEventId)
          ..add('occurredAt', occurredAt)
          ..add('lat', lat)
          ..add('lng', lng))
        .toString();
  }
}

class DriverTripsTripIdStartPostRequestBuilder
    implements
        Builder<DriverTripsTripIdStartPostRequest,
            DriverTripsTripIdStartPostRequestBuilder> {
  _$DriverTripsTripIdStartPostRequest? _$v;

  String? _clientEventId;
  String? get clientEventId => _$this._clientEventId;
  set clientEventId(String? clientEventId) =>
      _$this._clientEventId = clientEventId;

  DateTime? _occurredAt;
  DateTime? get occurredAt => _$this._occurredAt;
  set occurredAt(DateTime? occurredAt) => _$this._occurredAt = occurredAt;

  num? _lat;
  num? get lat => _$this._lat;
  set lat(num? lat) => _$this._lat = lat;

  num? _lng;
  num? get lng => _$this._lng;
  set lng(num? lng) => _$this._lng = lng;

  DriverTripsTripIdStartPostRequestBuilder() {
    DriverTripsTripIdStartPostRequest._defaults(this);
  }

  DriverTripsTripIdStartPostRequestBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _clientEventId = $v.clientEventId;
      _occurredAt = $v.occurredAt;
      _lat = $v.lat;
      _lng = $v.lng;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(DriverTripsTripIdStartPostRequest other) {
    _$v = other as _$DriverTripsTripIdStartPostRequest;
  }

  @override
  void update(
      void Function(DriverTripsTripIdStartPostRequestBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  DriverTripsTripIdStartPostRequest build() => _build();

  _$DriverTripsTripIdStartPostRequest _build() {
    final _$result = _$v ??
        _$DriverTripsTripIdStartPostRequest._(
          clientEventId: BuiltValueNullFieldError.checkNotNull(clientEventId,
              r'DriverTripsTripIdStartPostRequest', 'clientEventId'),
          occurredAt: BuiltValueNullFieldError.checkNotNull(
              occurredAt, r'DriverTripsTripIdStartPostRequest', 'occurredAt'),
          lat: lat,
          lng: lng,
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
