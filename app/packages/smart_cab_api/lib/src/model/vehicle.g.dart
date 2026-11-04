// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'vehicle.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

abstract class VehicleBuilder implements VehicleInputBuilder {
  void replace(covariant Vehicle other);
  void update(void Function(VehicleBuilder) updates);
  String? get currentDriverId;
  set currentDriverId(covariant String? currentDriverId);

  String? get id;
  set id(covariant String? id);

  VehicleStatus? get status;
  set status(covariant VehicleStatus? status);

  String? get registrationNo;
  set registrationNo(covariant String? registrationNo);

  String? get model;
  set model(covariant String? model);

  VehicleType? get vehicleType;
  set vehicleType(covariant VehicleType? vehicleType);

  int? get seatCapacity;
  set seatCapacity(covariant int? seatCapacity);

  TrackerType? get trackerType;
  set trackerType(covariant TrackerType? trackerType);
}

class _$$Vehicle extends $Vehicle {
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

  factory _$$Vehicle([void Function($VehicleBuilder)? updates]) =>
      ($VehicleBuilder()..update(updates))._build();

  _$$Vehicle._(
      {this.currentDriverId,
      this.id,
      this.status,
      required this.registrationNo,
      this.model,
      required this.vehicleType,
      required this.seatCapacity,
      this.trackerType})
      : super._();
  @override
  $Vehicle rebuild(void Function($VehicleBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  $VehicleBuilder toBuilder() => $VehicleBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is $Vehicle &&
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
    return (newBuiltValueToStringHelper(r'$Vehicle')
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

class $VehicleBuilder
    implements Builder<$Vehicle, $VehicleBuilder>, VehicleBuilder {
  _$$Vehicle? _$v;

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

  $VehicleBuilder() {
    $Vehicle._defaults(this);
  }

  $VehicleBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
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
  void replace(covariant $Vehicle other) {
    _$v = other as _$$Vehicle;
  }

  @override
  void update(void Function($VehicleBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  $Vehicle build() => _build();

  _$$Vehicle _build() {
    final _$result = _$v ??
        _$$Vehicle._(
          currentDriverId: currentDriverId,
          id: id,
          status: status,
          registrationNo: BuiltValueNullFieldError.checkNotNull(
              registrationNo, r'$Vehicle', 'registrationNo'),
          model: model,
          vehicleType: BuiltValueNullFieldError.checkNotNull(
              vehicleType, r'$Vehicle', 'vehicleType'),
          seatCapacity: BuiltValueNullFieldError.checkNotNull(
              seatCapacity, r'$Vehicle', 'seatCapacity'),
          trackerType: trackerType,
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
