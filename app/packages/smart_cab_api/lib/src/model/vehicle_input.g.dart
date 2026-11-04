// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'vehicle_input.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

abstract class VehicleInputBuilder {
  void replace(VehicleInput other);
  void update(void Function(VehicleInputBuilder) updates);
  String? get registrationNo;
  set registrationNo(String? registrationNo);

  String? get model;
  set model(String? model);

  VehicleType? get vehicleType;
  set vehicleType(VehicleType? vehicleType);

  int? get seatCapacity;
  set seatCapacity(int? seatCapacity);

  TrackerType? get trackerType;
  set trackerType(TrackerType? trackerType);
}

class _$$VehicleInput extends $VehicleInput {
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

  factory _$$VehicleInput([void Function($VehicleInputBuilder)? updates]) =>
      ($VehicleInputBuilder()..update(updates))._build();

  _$$VehicleInput._(
      {required this.registrationNo,
      this.model,
      required this.vehicleType,
      required this.seatCapacity,
      this.trackerType})
      : super._();
  @override
  $VehicleInput rebuild(void Function($VehicleInputBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  $VehicleInputBuilder toBuilder() => $VehicleInputBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is $VehicleInput &&
        registrationNo == other.registrationNo &&
        model == other.model &&
        vehicleType == other.vehicleType &&
        seatCapacity == other.seatCapacity &&
        trackerType == other.trackerType;
  }

  @override
  int get hashCode {
    var _$hash = 0;
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
    return (newBuiltValueToStringHelper(r'$VehicleInput')
          ..add('registrationNo', registrationNo)
          ..add('model', model)
          ..add('vehicleType', vehicleType)
          ..add('seatCapacity', seatCapacity)
          ..add('trackerType', trackerType))
        .toString();
  }
}

class $VehicleInputBuilder
    implements
        Builder<$VehicleInput, $VehicleInputBuilder>,
        VehicleInputBuilder {
  _$$VehicleInput? _$v;

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

  $VehicleInputBuilder() {
    $VehicleInput._defaults(this);
  }

  $VehicleInputBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
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
  void replace(covariant $VehicleInput other) {
    _$v = other as _$$VehicleInput;
  }

  @override
  void update(void Function($VehicleInputBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  $VehicleInput build() => _build();

  _$$VehicleInput _build() {
    final _$result = _$v ??
        _$$VehicleInput._(
          registrationNo: BuiltValueNullFieldError.checkNotNull(
              registrationNo, r'$VehicleInput', 'registrationNo'),
          model: model,
          vehicleType: BuiltValueNullFieldError.checkNotNull(
              vehicleType, r'$VehicleInput', 'vehicleType'),
          seatCapacity: BuiltValueNullFieldError.checkNotNull(
              seatCapacity, r'$VehicleInput', 'seatCapacity'),
          trackerType: trackerType,
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
