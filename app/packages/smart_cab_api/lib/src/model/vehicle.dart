//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:smart_cab_api/src/model/vehicle_input.dart';
import 'package:smart_cab_api/src/model/vehicle_type.dart';
import 'package:smart_cab_api/src/model/tracker_type.dart';
import 'package:smart_cab_api/src/model/vehicle_status.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'vehicle.g.dart';

/// Vehicle
///
/// Properties:
/// * [registrationNo] 
/// * [model] 
/// * [vehicleType] 
/// * [seatCapacity] 
/// * [trackerType] 
/// * [id] 
/// * [status] 
/// * [currentDriverId] 
@BuiltValue(instantiable: false)
abstract class Vehicle implements VehicleInput {
  @BuiltValueField(wireName: r'current_driver_id')
  String? get currentDriverId;

  @BuiltValueField(wireName: r'id')
  String? get id;

  @BuiltValueField(wireName: r'status')
  VehicleStatus? get status;
  // enum statusEnum {  off_duty,  available,  on_trip,  out_of_service,  };

  @BuiltValueSerializer(custom: true)
  static Serializer<Vehicle> get serializer => _$VehicleSerializer();
}

class _$VehicleSerializer implements PrimitiveSerializer<Vehicle> {
  @override
  final Iterable<Type> types = const [Vehicle];

  @override
  final String wireName = r'Vehicle';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    Vehicle object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    yield r'seat_capacity';
    yield serializers.serialize(
      object.seatCapacity,
      specifiedType: const FullType(int),
    );
    if (object.currentDriverId != null) {
      yield r'current_driver_id';
      yield serializers.serialize(
        object.currentDriverId,
        specifiedType: const FullType.nullable(String),
      );
    }
    yield r'registration_no';
    yield serializers.serialize(
      object.registrationNo,
      specifiedType: const FullType(String),
    );
    if (object.trackerType != null) {
      yield r'tracker_type';
      yield serializers.serialize(
        object.trackerType,
        specifiedType: const FullType(TrackerType),
      );
    }
    if (object.model != null) {
      yield r'model';
      yield serializers.serialize(
        object.model,
        specifiedType: const FullType(String),
      );
    }
    if (object.id != null) {
      yield r'id';
      yield serializers.serialize(
        object.id,
        specifiedType: const FullType(String),
      );
    }
    yield r'vehicle_type';
    yield serializers.serialize(
      object.vehicleType,
      specifiedType: const FullType(VehicleType),
    );
    if (object.status != null) {
      yield r'status';
      yield serializers.serialize(
        object.status,
        specifiedType: const FullType(VehicleStatus),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    Vehicle object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  @override
  Vehicle deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return serializers.deserialize(serialized, specifiedType: FullType($Vehicle)) as $Vehicle;
  }
}

/// a concrete implementation of [Vehicle], since [Vehicle] is not instantiable
@BuiltValue(instantiable: true)
abstract class $Vehicle implements Vehicle, Built<$Vehicle, $VehicleBuilder> {
  $Vehicle._();

  factory $Vehicle([void Function($VehicleBuilder)? updates]) = _$$Vehicle;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults($VehicleBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<$Vehicle> get serializer => _$$VehicleSerializer();
}

class _$$VehicleSerializer implements PrimitiveSerializer<$Vehicle> {
  @override
  final Iterable<Type> types = const [$Vehicle, _$$Vehicle];

  @override
  final String wireName = r'$Vehicle';

  @override
  Object serialize(
    Serializers serializers,
    $Vehicle object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return serializers.serialize(object, specifiedType: FullType(Vehicle))!;
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required VehicleBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'seat_capacity':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.seatCapacity = valueDes;
          break;
        case r'current_driver_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(String),
          ) as String?;
          if (valueDes == null) continue;
          result.currentDriverId = valueDes;
          break;
        case r'registration_no':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.registrationNo = valueDes;
          break;
        case r'tracker_type':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(TrackerType),
          ) as TrackerType;
          result.trackerType = valueDes;
          break;
        case r'model':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.model = valueDes;
          break;
        case r'id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.id = valueDes;
          break;
        case r'vehicle_type':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(VehicleType),
          ) as VehicleType;
          result.vehicleType = valueDes;
          break;
        case r'status':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(VehicleStatus),
          ) as VehicleStatus;
          result.status = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  $Vehicle deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = $VehicleBuilder();
    final serializedList = (serialized as Iterable<Object?>).toList();
    final unhandled = <Object?>[];
    _deserializeProperties(
      serializers,
      serialized,
      specifiedType: specifiedType,
      serializedList: serializedList,
      unhandled: unhandled,
      result: result,
    );
    return result.build();
  }
}

