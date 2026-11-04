// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'trip_stop.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

const TripStopStopTypeEnum _$tripStopStopTypeEnum_pickup =
    const TripStopStopTypeEnum._('pickup');
const TripStopStopTypeEnum _$tripStopStopTypeEnum_drop =
    const TripStopStopTypeEnum._('drop');

TripStopStopTypeEnum _$tripStopStopTypeEnumValueOf(String name) {
  switch (name) {
    case 'pickup':
      return _$tripStopStopTypeEnum_pickup;
    case 'drop':
      return _$tripStopStopTypeEnum_drop;
    default:
      throw ArgumentError(name);
  }
}

final BuiltSet<TripStopStopTypeEnum> _$tripStopStopTypeEnumValues =
    BuiltSet<TripStopStopTypeEnum>(const <TripStopStopTypeEnum>[
  _$tripStopStopTypeEnum_pickup,
  _$tripStopStopTypeEnum_drop,
]);

Serializer<TripStopStopTypeEnum> _$tripStopStopTypeEnumSerializer =
    _$TripStopStopTypeEnumSerializer();

class _$TripStopStopTypeEnumSerializer
    implements PrimitiveSerializer<TripStopStopTypeEnum> {
  static const Map<String, Object> _toWire = const <String, Object>{
    'pickup': 'pickup',
    'drop': 'drop',
  };
  static const Map<Object, String> _fromWire = const <Object, String>{
    'pickup': 'pickup',
    'drop': 'drop',
  };

  @override
  final Iterable<Type> types = const <Type>[TripStopStopTypeEnum];
  @override
  final String wireName = 'TripStopStopTypeEnum';

  @override
  Object serialize(Serializers serializers, TripStopStopTypeEnum object,
          {FullType specifiedType = FullType.unspecified}) =>
      _toWire[object.name] ?? object.name;

  @override
  TripStopStopTypeEnum deserialize(Serializers serializers, Object serialized,
          {FullType specifiedType = FullType.unspecified}) =>
      TripStopStopTypeEnum.valueOf(
          _fromWire[serialized] ?? (serialized is String ? serialized : ''));
}

class _$TripStop extends TripStop {
  @override
  final String? id;
  @override
  final int? sequence;
  @override
  final TripStopStopTypeEnum? stopType;
  @override
  final String? requestId;
  @override
  final String? riderFirstName;
  @override
  final String? riderPhone;
  @override
  final LatLng? location;
  @override
  final String? landmark;
  @override
  final StopStatus? status;
  @override
  final DateTime? plannedEta;
  @override
  final DateTime? latestEta;
  @override
  final bool? etaApproximate;
  @override
  final DateTime? arrivedAt;
  @override
  final DateTime? doneAt;

  factory _$TripStop([void Function(TripStopBuilder)? updates]) =>
      (TripStopBuilder()..update(updates))._build();

  _$TripStop._(
      {this.id,
      this.sequence,
      this.stopType,
      this.requestId,
      this.riderFirstName,
      this.riderPhone,
      this.location,
      this.landmark,
      this.status,
      this.plannedEta,
      this.latestEta,
      this.etaApproximate,
      this.arrivedAt,
      this.doneAt})
      : super._();
  @override
  TripStop rebuild(void Function(TripStopBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  TripStopBuilder toBuilder() => TripStopBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is TripStop &&
        id == other.id &&
        sequence == other.sequence &&
        stopType == other.stopType &&
        requestId == other.requestId &&
        riderFirstName == other.riderFirstName &&
        riderPhone == other.riderPhone &&
        location == other.location &&
        landmark == other.landmark &&
        status == other.status &&
        plannedEta == other.plannedEta &&
        latestEta == other.latestEta &&
        etaApproximate == other.etaApproximate &&
        arrivedAt == other.arrivedAt &&
        doneAt == other.doneAt;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, id.hashCode);
    _$hash = $jc(_$hash, sequence.hashCode);
    _$hash = $jc(_$hash, stopType.hashCode);
    _$hash = $jc(_$hash, requestId.hashCode);
    _$hash = $jc(_$hash, riderFirstName.hashCode);
    _$hash = $jc(_$hash, riderPhone.hashCode);
    _$hash = $jc(_$hash, location.hashCode);
    _$hash = $jc(_$hash, landmark.hashCode);
    _$hash = $jc(_$hash, status.hashCode);
    _$hash = $jc(_$hash, plannedEta.hashCode);
    _$hash = $jc(_$hash, latestEta.hashCode);
    _$hash = $jc(_$hash, etaApproximate.hashCode);
    _$hash = $jc(_$hash, arrivedAt.hashCode);
    _$hash = $jc(_$hash, doneAt.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'TripStop')
          ..add('id', id)
          ..add('sequence', sequence)
          ..add('stopType', stopType)
          ..add('requestId', requestId)
          ..add('riderFirstName', riderFirstName)
          ..add('riderPhone', riderPhone)
          ..add('location', location)
          ..add('landmark', landmark)
          ..add('status', status)
          ..add('plannedEta', plannedEta)
          ..add('latestEta', latestEta)
          ..add('etaApproximate', etaApproximate)
          ..add('arrivedAt', arrivedAt)
          ..add('doneAt', doneAt))
        .toString();
  }
}

class TripStopBuilder implements Builder<TripStop, TripStopBuilder> {
  _$TripStop? _$v;

  String? _id;
  String? get id => _$this._id;
  set id(String? id) => _$this._id = id;

  int? _sequence;
  int? get sequence => _$this._sequence;
  set sequence(int? sequence) => _$this._sequence = sequence;

  TripStopStopTypeEnum? _stopType;
  TripStopStopTypeEnum? get stopType => _$this._stopType;
  set stopType(TripStopStopTypeEnum? stopType) => _$this._stopType = stopType;

  String? _requestId;
  String? get requestId => _$this._requestId;
  set requestId(String? requestId) => _$this._requestId = requestId;

  String? _riderFirstName;
  String? get riderFirstName => _$this._riderFirstName;
  set riderFirstName(String? riderFirstName) =>
      _$this._riderFirstName = riderFirstName;

  String? _riderPhone;
  String? get riderPhone => _$this._riderPhone;
  set riderPhone(String? riderPhone) => _$this._riderPhone = riderPhone;

  LatLngBuilder? _location;
  LatLngBuilder get location => _$this._location ??= LatLngBuilder();
  set location(LatLngBuilder? location) => _$this._location = location;

  String? _landmark;
  String? get landmark => _$this._landmark;
  set landmark(String? landmark) => _$this._landmark = landmark;

  StopStatus? _status;
  StopStatus? get status => _$this._status;
  set status(StopStatus? status) => _$this._status = status;

  DateTime? _plannedEta;
  DateTime? get plannedEta => _$this._plannedEta;
  set plannedEta(DateTime? plannedEta) => _$this._plannedEta = plannedEta;

  DateTime? _latestEta;
  DateTime? get latestEta => _$this._latestEta;
  set latestEta(DateTime? latestEta) => _$this._latestEta = latestEta;

  bool? _etaApproximate;
  bool? get etaApproximate => _$this._etaApproximate;
  set etaApproximate(bool? etaApproximate) =>
      _$this._etaApproximate = etaApproximate;

  DateTime? _arrivedAt;
  DateTime? get arrivedAt => _$this._arrivedAt;
  set arrivedAt(DateTime? arrivedAt) => _$this._arrivedAt = arrivedAt;

  DateTime? _doneAt;
  DateTime? get doneAt => _$this._doneAt;
  set doneAt(DateTime? doneAt) => _$this._doneAt = doneAt;

  TripStopBuilder() {
    TripStop._defaults(this);
  }

  TripStopBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _id = $v.id;
      _sequence = $v.sequence;
      _stopType = $v.stopType;
      _requestId = $v.requestId;
      _riderFirstName = $v.riderFirstName;
      _riderPhone = $v.riderPhone;
      _location = $v.location?.toBuilder();
      _landmark = $v.landmark;
      _status = $v.status;
      _plannedEta = $v.plannedEta;
      _latestEta = $v.latestEta;
      _etaApproximate = $v.etaApproximate;
      _arrivedAt = $v.arrivedAt;
      _doneAt = $v.doneAt;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(TripStop other) {
    _$v = other as _$TripStop;
  }

  @override
  void update(void Function(TripStopBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  TripStop build() => _build();

  _$TripStop _build() {
    _$TripStop _$result;
    try {
      _$result = _$v ??
          _$TripStop._(
            id: id,
            sequence: sequence,
            stopType: stopType,
            requestId: requestId,
            riderFirstName: riderFirstName,
            riderPhone: riderPhone,
            location: _location?.build(),
            landmark: landmark,
            status: status,
            plannedEta: plannedEta,
            latestEta: latestEta,
            etaApproximate: etaApproximate,
            arrivedAt: arrivedAt,
            doneAt: doneAt,
          );
    } catch (_) {
      late String _$failedField;
      try {
        _$failedField = 'location';
        _location?.build();
      } catch (e) {
        throw BuiltValueNestedFieldError(
            r'TripStop', _$failedField, e.toString());
      }
      rethrow;
    }
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
