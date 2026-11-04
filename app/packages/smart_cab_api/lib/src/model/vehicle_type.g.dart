// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'vehicle_type.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

const VehicleType _$sedan4 = const VehicleType._('sedan4');
const VehicleType _$suv6 = const VehicleType._('suv6');
const VehicleType _$vip = const VehicleType._('vip');

VehicleType _$valueOf(String name) {
  switch (name) {
    case 'sedan4':
      return _$sedan4;
    case 'suv6':
      return _$suv6;
    case 'vip':
      return _$vip;
    default:
      throw ArgumentError(name);
  }
}

final BuiltSet<VehicleType> _$values =
    BuiltSet<VehicleType>(const <VehicleType>[
  _$sedan4,
  _$suv6,
  _$vip,
]);

class _$VehicleTypeMeta {
  const _$VehicleTypeMeta();
  VehicleType get sedan4 => _$sedan4;
  VehicleType get suv6 => _$suv6;
  VehicleType get vip => _$vip;
  VehicleType valueOf(String name) => _$valueOf(name);
  BuiltSet<VehicleType> get values => _$values;
}

abstract class _$VehicleTypeMixin {
  // ignore: non_constant_identifier_names
  _$VehicleTypeMeta get VehicleType => const _$VehicleTypeMeta();
}

Serializer<VehicleType> _$vehicleTypeSerializer = _$VehicleTypeSerializer();

class _$VehicleTypeSerializer implements PrimitiveSerializer<VehicleType> {
  static const Map<String, Object> _toWire = const <String, Object>{
    'sedan4': 'sedan_4',
    'suv6': 'suv_6',
    'vip': 'vip',
  };
  static const Map<Object, String> _fromWire = const <Object, String>{
    'sedan_4': 'sedan4',
    'suv_6': 'suv6',
    'vip': 'vip',
  };

  @override
  final Iterable<Type> types = const <Type>[VehicleType];
  @override
  final String wireName = 'VehicleType';

  @override
  Object serialize(Serializers serializers, VehicleType object,
          {FullType specifiedType = FullType.unspecified}) =>
      _toWire[object.name] ?? object.name;

  @override
  VehicleType deserialize(Serializers serializers, Object serialized,
          {FullType specifiedType = FullType.unspecified}) =>
      VehicleType.valueOf(
          _fromWire[serialized] ?? (serialized is String ? serialized : ''));
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
