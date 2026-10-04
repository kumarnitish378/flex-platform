// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'vehicle_live.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$VehicleLive extends VehicleLive {
  @override
  final bool? stale;
  @override
  final int? seatsFree;
  @override
  final LatLng? position;
  @override
  final DateTime? positionAt;
  @override
  final String? activeTripId;
  @override
  final String? currentDriverId;
  @override
  final String? id;
  @override
  final VehicleStatus? status;
  @override
  final String registrationNo;
  @override
  final String? model;
  @override
  final VehicleType vehicleType;
  @override
  final int seatCapacity;
  @override
  final TrackerType? trackerType;

  factory _$VehicleLive([void Function(VehicleLiveBuilder)? updates]) =>
      (VehicleLiveBuilder()..update(updates))._build();

  _$VehicleLive._(
      {this.stale,
      this.seatsFree,
      this.position,
      this.positionAt,
      this.activeTripId,
      this.currentDriverId,
      this.id,
      this.status,
      required this.registrationNo,
      this.model,
      required this.vehicleType,
      required this.seatCapacity,
      this.trackerType})
      : super._();
  @override
  VehicleLive rebuild(void Function(VehicleLiveBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  VehicleLiveBuilder toBuilder() => VehicleLiveBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is VehicleLive &&
        stale == other.stale &&
        seatsFree == other.seatsFree &&
        position == other.position &&
        positionAt == other.positionAt &&
        activeTripId == other.activeTripId &&
        currentDriverId == other.currentDriverId &&
        id == other.id &&
        status == other.status &&
        registrationNo == other.registrationNo &&
        model == other.model &&
        vehicleType == other.vehicleType &&
        seatCapacity == other.seatCapacity &&
        trackerType == other.trackerType;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, stale.hashCode);
    _$hash = $jc(_$hash, seatsFree.hashCode);
    _$hash = $jc(_$hash, position.hashCode);
    _$hash = $jc(_$hash, positionAt.hashCode);
    _$hash = $jc(_$hash, activeTripId.hashCode);
    _$hash = $jc(_$hash, currentDriverId.hashCode);
    _$hash = $jc(_$hash, id.hashCode);
    _$hash = $jc(_$hash, status.hashCode);
    _$hash = $jc(_$hash, registrationNo.hashCode);
    _$hash = $jc(_$hash, model.hashCode);
    _$hash = $jc(_$hash, vehicleType.hashCode);
    _$hash = $jc(_$hash, seatCapacity.hashCode);
    _$hash = $jc(_$hash, trackerType.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'VehicleLive')
          ..add('stale', stale)
          ..add('seatsFree', seatsFree)
          ..add('position', position)
          ..add('positionAt', positionAt)
          ..add('activeTripId', activeTripId)
          ..add('currentDriverId', currentDriverId)
          ..add('id', id)
          ..add('status', status)
          ..add('registrationNo', registrationNo)
          ..add('model', model)
          ..add('vehicleType', vehicleType)
          ..add('seatCapacity', seatCapacity)
          ..add('trackerType', trackerType))
        .toString();
  }
}

class VehicleLiveBuilder
    implements Builder<VehicleLive, VehicleLiveBuilder>, VehicleBuilder {
  _$VehicleLive? _$v;

  bool? _stale;
  bool? get stale => _$this._stale;
  set stale(covariant bool? stale) => _$this._stale = stale;

  int? _seatsFree;
  int? get seatsFree => _$this._seatsFree;
  set seatsFree(covariant int? seatsFree) => _$this._seatsFree = seatsFree;

  LatLngBuilder? _position;
  LatLngBuilder get position => _$this._position ??= LatLngBuilder();
  set position(covariant LatLngBuilder? position) =>
      _$this._position = position;

  DateTime? _positionAt;
  DateTime? get positionAt => _$this._positionAt;
  set positionAt(covariant DateTime? positionAt) =>
      _$this._positionAt = positionAt;

  String? _activeTripId;
  String? get activeTripId => _$this._activeTripId;
  set activeTripId(covariant String? activeTripId) =>
      _$this._activeTripId = activeTripId;

  String? _currentDriverId;
  String? get currentDriverId => _$this._currentDriverId;
  set currentDriverId(covariant String? currentDriverId) =>
      _$this._currentDriverId = currentDriverId;

  String? _id;
  String? get id => _$this._id;
  set id(covariant String? id) => _$this._id = id;

  VehicleStatus? _status;
  VehicleStatus? get status => _$this._status;
  set status(covariant VehicleStatus? status) => _$this._status = status;

  String? _registrationNo;
  String? get registrationNo => _$this._registrationNo;
  set registrationNo(covariant String? registrationNo) =>
      _$this._registrationNo = registrationNo;

  String? _model;
  String? get model => _$this._model;
  set model(covariant String? model) => _$this._model = model;

  VehicleType? _vehicleType;
  VehicleType? get vehicleType => _$this._vehicleType;
  set vehicleType(covariant VehicleType? vehicleType) =>
      _$this._vehicleType = vehicleType;

  int? _seatCapacity;
  int? get seatCapacity => _$this._seatCapacity;
  set seatCapacity(covariant int? seatCapacity) =>
      _$this._seatCapacity = seatCapacity;

  TrackerType? _trackerType;
  TrackerType? get trackerType => _$this._trackerType;
  set trackerType(covariant TrackerType? trackerType) =>
      _$this._trackerType = trackerType;

  VehicleLiveBuilder() {
    VehicleLive._defaults(this);
  }

  VehicleLiveBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _stale = $v.stale;
      _seatsFree = $v.seatsFree;
      _position = $v.position?.toBuilder();
      _positionAt = $v.positionAt;
      _activeTripId = $v.activeTripId;
      _currentDriverId = $v.currentDriverId;
      _id = $v.id;
      _status = $v.status;
      _registrationNo = $v.registrationNo;
      _model = $v.model;
      _vehicleType = $v.vehicleType;
      _seatCapacity = $v.seatCapacity;
      _trackerType = $v.trackerType;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(covariant VehicleLive other) {
    _$v = other as _$VehicleLive;
  }

  @override
  void update(void Function(VehicleLiveBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  VehicleLive build() => _build();

  _$VehicleLive _build() {
    _$VehicleLive _$result;
    try {
      _$result = _$v ??
          _$VehicleLive._(
            stale: stale,
            seatsFree: seatsFree,
            position: _position?.build(),
            positionAt: positionAt,
            activeTripId: activeTripId,
            currentDriverId: currentDriverId,
            id: id,
            status: status,
            registrationNo: BuiltValueNullFieldError.checkNotNull(
                registrationNo, r'VehicleLive', 'registrationNo'),
            model: model,
            vehicleType: BuiltValueNullFieldError.checkNotNull(
                vehicleType, r'VehicleLive', 'vehicleType'),
            seatCapacity: BuiltValueNullFieldError.checkNotNull(
                seatCapacity, r'VehicleLive', 'seatCapacity'),
            trackerType: trackerType,
          );
    } catch (_) {
      late String _$failedField;
      try {
        _$failedField = 'position';
        _position?.build();
      } catch (e) {
        throw BuiltValueNestedFieldError(
            r'VehicleLive', _$failedField, e.toString());
      }
      rethrow;
    }
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
