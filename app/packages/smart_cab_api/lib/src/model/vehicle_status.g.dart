// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'vehicle_status.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

const VehicleStatus _$offDuty = const VehicleStatus._('offDuty');
const VehicleStatus _$available = const VehicleStatus._('available');
const VehicleStatus _$onTrip = const VehicleStatus._('onTrip');
const VehicleStatus _$outOfService = const VehicleStatus._('outOfService');

VehicleStatus _$valueOf(String name) {
  switch (name) {
    case 'offDuty':
      return _$offDuty;
    case 'available':
      return _$available;
    case 'onTrip':
      return _$onTrip;
    case 'outOfService':
      return _$outOfService;
    default:
      throw ArgumentError(name);
  }
}

final BuiltSet<VehicleStatus> _$values =
    BuiltSet<VehicleStatus>(const <VehicleStatus>[
  _$offDuty,
  _$available,
  _$onTrip,
  _$outOfService,
]);

class _$VehicleStatusMeta {
  const _$VehicleStatusMeta();
  VehicleStatus get offDuty => _$offDuty;
  VehicleStatus get available => _$available;
  VehicleStatus get onTrip => _$onTrip;
  VehicleStatus get outOfService => _$outOfService;
  VehicleStatus valueOf(String name) => _$valueOf(name);
  BuiltSet<VehicleStatus> get values => _$values;
}

abstract class _$VehicleStatusMixin {
  // ignore: non_constant_identifier_names
  _$VehicleStatusMeta get VehicleStatus => const _$VehicleStatusMeta();
}

Serializer<VehicleStatus> _$vehicleStatusSerializer =
    _$VehicleStatusSerializer();

class _$VehicleStatusSerializer implements PrimitiveSerializer<VehicleStatus> {
  static const Map<String, Object> _toWire = const <String, Object>{
    'offDuty': 'off_duty',
    'available': 'available',
    'onTrip': 'on_trip',
    'outOfService': 'out_of_service',
  };
  static const Map<Object, String> _fromWire = const <Object, String>{
    'off_duty': 'offDuty',
    'available': 'available',
    'on_trip': 'onTrip',
    'out_of_service': 'outOfService',
  };

  @override
  final Iterable<Type> types = const <Type>[VehicleStatus];
  @override
  final String wireName = 'VehicleStatus';

  @override
  Object serialize(Serializers serializers, VehicleStatus object,
          {FullType specifiedType = FullType.unspecified}) =>
      _toWire[object.name] ?? object.name;

  @override
  VehicleStatus deserialize(Serializers serializers, Object serialized,
          {FullType specifiedType = FullType.unspecified}) =>
      VehicleStatus.valueOf(
          _fromWire[serialized] ?? (serialized is String ? serialized : ''));
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
