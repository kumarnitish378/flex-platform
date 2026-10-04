//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_collection/built_collection.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'vehicle_status.g.dart';

class VehicleStatus extends EnumClass {

  @BuiltValueEnumConst(wireName: r'off_duty')
  static const VehicleStatus offDuty = _$offDuty;
  @BuiltValueEnumConst(wireName: r'available')
  static const VehicleStatus available = _$available;
  @BuiltValueEnumConst(wireName: r'on_trip')
  static const VehicleStatus onTrip = _$onTrip;
  @BuiltValueEnumConst(wireName: r'out_of_service')
  static const VehicleStatus outOfService = _$outOfService;

  static Serializer<VehicleStatus> get serializer => _$vehicleStatusSerializer;

  const VehicleStatus._(String name): super(name);

  static BuiltSet<VehicleStatus> get values => _$values;
  static VehicleStatus valueOf(String name) => _$valueOf(name);
}

/// Optionally, enum_class can generate a mixin to go with your enum for use
/// with Angular. It exposes your enum constants as getters. So, if you mix it
/// in to your Dart component class, the values become available to the
/// corresponding Angular template.
///
/// Trigger mixin generation by writing a line like this one next to your enum.
abstract class VehicleStatusMixin = Object with _$VehicleStatusMixin;

