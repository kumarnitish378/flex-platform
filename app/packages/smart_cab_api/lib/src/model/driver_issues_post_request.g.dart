// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'driver_issues_post_request.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

const DriverIssuesPostRequestTypeEnum
    _$driverIssuesPostRequestTypeEnum_breakdown =
    const DriverIssuesPostRequestTypeEnum._('breakdown');
const DriverIssuesPostRequestTypeEnum
    _$driverIssuesPostRequestTypeEnum_accident =
    const DriverIssuesPostRequestTypeEnum._('accident');
const DriverIssuesPostRequestTypeEnum
    _$driverIssuesPostRequestTypeEnum_trafficBlock =
    const DriverIssuesPostRequestTypeEnum._('trafficBlock');
const DriverIssuesPostRequestTypeEnum
    _$driverIssuesPostRequestTypeEnum_riderIssue =
    const DriverIssuesPostRequestTypeEnum._('riderIssue');
const DriverIssuesPostRequestTypeEnum _$driverIssuesPostRequestTypeEnum_other =
    const DriverIssuesPostRequestTypeEnum._('other');

DriverIssuesPostRequestTypeEnum _$driverIssuesPostRequestTypeEnumValueOf(
    String name) {
  switch (name) {
    case 'breakdown':
      return _$driverIssuesPostRequestTypeEnum_breakdown;
    case 'accident':
      return _$driverIssuesPostRequestTypeEnum_accident;
    case 'trafficBlock':
      return _$driverIssuesPostRequestTypeEnum_trafficBlock;
    case 'riderIssue':
      return _$driverIssuesPostRequestTypeEnum_riderIssue;
    case 'other':
      return _$driverIssuesPostRequestTypeEnum_other;
    default:
      throw ArgumentError(name);
  }
}

final BuiltSet<DriverIssuesPostRequestTypeEnum>
    _$driverIssuesPostRequestTypeEnumValues = BuiltSet<
        DriverIssuesPostRequestTypeEnum>(const <DriverIssuesPostRequestTypeEnum>[
  _$driverIssuesPostRequestTypeEnum_breakdown,
  _$driverIssuesPostRequestTypeEnum_accident,
  _$driverIssuesPostRequestTypeEnum_trafficBlock,
  _$driverIssuesPostRequestTypeEnum_riderIssue,
  _$driverIssuesPostRequestTypeEnum_other,
]);

Serializer<DriverIssuesPostRequestTypeEnum>
    _$driverIssuesPostRequestTypeEnumSerializer =
    _$DriverIssuesPostRequestTypeEnumSerializer();

class _$DriverIssuesPostRequestTypeEnumSerializer
    implements PrimitiveSerializer<DriverIssuesPostRequestTypeEnum> {
  static const Map<String, Object> _toWire = const <String, Object>{
    'breakdown': 'breakdown',
    'accident': 'accident',
    'trafficBlock': 'traffic_block',
    'riderIssue': 'rider_issue',
    'other': 'other',
  };
  static const Map<Object, String> _fromWire = const <Object, String>{
    'breakdown': 'breakdown',
    'accident': 'accident',
    'traffic_block': 'trafficBlock',
    'rider_issue': 'riderIssue',
    'other': 'other',
  };

  @override
  final Iterable<Type> types = const <Type>[DriverIssuesPostRequestTypeEnum];
  @override
  final String wireName = 'DriverIssuesPostRequestTypeEnum';

  @override
  Object serialize(
          Serializers serializers, DriverIssuesPostRequestTypeEnum object,
          {FullType specifiedType = FullType.unspecified}) =>
      _toWire[object.name] ?? object.name;

  @override
  DriverIssuesPostRequestTypeEnum deserialize(
          Serializers serializers, Object serialized,
          {FullType specifiedType = FullType.unspecified}) =>
      DriverIssuesPostRequestTypeEnum.valueOf(
          _fromWire[serialized] ?? (serialized is String ? serialized : ''));
}

class _$DriverIssuesPostRequest extends DriverIssuesPostRequest {
  @override
  final DriverIssuesPostRequestTypeEnum type;
  @override
  final String? note;
  @override
  final String? tripId;
  @override
  final num? lat;
  @override
  final num? lng;

  factory _$DriverIssuesPostRequest(
          [void Function(DriverIssuesPostRequestBuilder)? updates]) =>
      (DriverIssuesPostRequestBuilder()..update(updates))._build();

  _$DriverIssuesPostRequest._(
      {required this.type, this.note, this.tripId, this.lat, this.lng})
      : super._();
  @override
  DriverIssuesPostRequest rebuild(
          void Function(DriverIssuesPostRequestBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  DriverIssuesPostRequestBuilder toBuilder() =>
      DriverIssuesPostRequestBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is DriverIssuesPostRequest &&
        type == other.type &&
        note == other.note &&
        tripId == other.tripId &&
        lat == other.lat &&
        lng == other.lng;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, type.hashCode);
    _$hash = $jc(_$hash, note.hashCode);
    _$hash = $jc(_$hash, tripId.hashCode);
    _$hash = $jc(_$hash, lat.hashCode);
    _$hash = $jc(_$hash, lng.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'DriverIssuesPostRequest')
          ..add('type', type)
          ..add('note', note)
          ..add('tripId', tripId)
          ..add('lat', lat)
          ..add('lng', lng))
        .toString();
  }
}

class DriverIssuesPostRequestBuilder
    implements
        Builder<DriverIssuesPostRequest, DriverIssuesPostRequestBuilder> {
  _$DriverIssuesPostRequest? _$v;

  DriverIssuesPostRequestTypeEnum? _type;
  DriverIssuesPostRequestTypeEnum? get type => _$this._type;
  set type(DriverIssuesPostRequestTypeEnum? type) => _$this._type = type;

  String? _note;
  String? get note => _$this._note;
  set note(String? note) => _$this._note = note;

  String? _tripId;
  String? get tripId => _$this._tripId;
  set tripId(String? tripId) => _$this._tripId = tripId;

  num? _lat;
  num? get lat => _$this._lat;
  set lat(num? lat) => _$this._lat = lat;

  num? _lng;
  num? get lng => _$this._lng;
  set lng(num? lng) => _$this._lng = lng;

  DriverIssuesPostRequestBuilder() {
    DriverIssuesPostRequest._defaults(this);
  }

  DriverIssuesPostRequestBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _type = $v.type;
      _note = $v.note;
      _tripId = $v.tripId;
      _lat = $v.lat;
      _lng = $v.lng;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(DriverIssuesPostRequest other) {
    _$v = other as _$DriverIssuesPostRequest;
  }

  @override
  void update(void Function(DriverIssuesPostRequestBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  DriverIssuesPostRequest build() => _build();

  _$DriverIssuesPostRequest _build() {
    final _$result = _$v ??
        _$DriverIssuesPostRequest._(
          type: BuiltValueNullFieldError.checkNotNull(
              type, r'DriverIssuesPostRequest', 'type'),
          note: note,
          tripId: tripId,
          lat: lat,
          lng: lng,
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
