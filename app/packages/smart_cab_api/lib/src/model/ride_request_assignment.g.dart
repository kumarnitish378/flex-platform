// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'ride_request_assignment.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$RideRequestAssignment extends RideRequestAssignment {
  @override
  final String? vehicleRegistrationNo;
  @override
  final String? vehicleModel;
  @override
  final String? driverName;
  @override
  final String? driverPhone;
  @override
  final DateTime? pickupEta;
  @override
  final bool? pickupEtaApproximate;

  factory _$RideRequestAssignment(
          [void Function(RideRequestAssignmentBuilder)? updates]) =>
      (RideRequestAssignmentBuilder()..update(updates))._build();

  _$RideRequestAssignment._(
      {this.vehicleRegistrationNo,
      this.vehicleModel,
      this.driverName,
      this.driverPhone,
      this.pickupEta,
      this.pickupEtaApproximate})
      : super._();
  @override
  RideRequestAssignment rebuild(
          void Function(RideRequestAssignmentBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  RideRequestAssignmentBuilder toBuilder() =>
      RideRequestAssignmentBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is RideRequestAssignment &&
        vehicleRegistrationNo == other.vehicleRegistrationNo &&
        vehicleModel == other.vehicleModel &&
        driverName == other.driverName &&
        driverPhone == other.driverPhone &&
        pickupEta == other.pickupEta &&
        pickupEtaApproximate == other.pickupEtaApproximate;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, vehicleRegistrationNo.hashCode);
    _$hash = $jc(_$hash, vehicleModel.hashCode);
    _$hash = $jc(_$hash, driverName.hashCode);
    _$hash = $jc(_$hash, driverPhone.hashCode);
    _$hash = $jc(_$hash, pickupEta.hashCode);
    _$hash = $jc(_$hash, pickupEtaApproximate.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'RideRequestAssignment')
          ..add('vehicleRegistrationNo', vehicleRegistrationNo)
          ..add('vehicleModel', vehicleModel)
          ..add('driverName', driverName)
          ..add('driverPhone', driverPhone)
          ..add('pickupEta', pickupEta)
          ..add('pickupEtaApproximate', pickupEtaApproximate))
        .toString();
  }
}

class RideRequestAssignmentBuilder
    implements Builder<RideRequestAssignment, RideRequestAssignmentBuilder> {
  _$RideRequestAssignment? _$v;

  String? _vehicleRegistrationNo;
  String? get vehicleRegistrationNo => _$this._vehicleRegistrationNo;
  set vehicleRegistrationNo(String? vehicleRegistrationNo) =>
      _$this._vehicleRegistrationNo = vehicleRegistrationNo;

  String? _vehicleModel;
  String? get vehicleModel => _$this._vehicleModel;
  set vehicleModel(String? vehicleModel) => _$this._vehicleModel = vehicleModel;

  String? _driverName;
  String? get driverName => _$this._driverName;
  set driverName(String? driverName) => _$this._driverName = driverName;

  String? _driverPhone;
  String? get driverPhone => _$this._driverPhone;
  set driverPhone(String? driverPhone) => _$this._driverPhone = driverPhone;

  DateTime? _pickupEta;
  DateTime? get pickupEta => _$this._pickupEta;
  set pickupEta(DateTime? pickupEta) => _$this._pickupEta = pickupEta;

  bool? _pickupEtaApproximate;
  bool? get pickupEtaApproximate => _$this._pickupEtaApproximate;
  set pickupEtaApproximate(bool? pickupEtaApproximate) =>
      _$this._pickupEtaApproximate = pickupEtaApproximate;

  RideRequestAssignmentBuilder() {
    RideRequestAssignment._defaults(this);
  }

  RideRequestAssignmentBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _vehicleRegistrationNo = $v.vehicleRegistrationNo;
      _vehicleModel = $v.vehicleModel;
      _driverName = $v.driverName;
      _driverPhone = $v.driverPhone;
      _pickupEta = $v.pickupEta;
      _pickupEtaApproximate = $v.pickupEtaApproximate;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(RideRequestAssignment other) {
    _$v = other as _$RideRequestAssignment;
  }

  @override
  void update(void Function(RideRequestAssignmentBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  RideRequestAssignment build() => _build();

  _$RideRequestAssignment _build() {
    final _$result = _$v ??
        _$RideRequestAssignment._(
          vehicleRegistrationNo: vehicleRegistrationNo,
          vehicleModel: vehicleModel,
          driverName: driverName,
          driverPhone: driverPhone,
          pickupEta: pickupEta,
          pickupEtaApproximate: pickupEtaApproximate,
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
