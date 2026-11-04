//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:smart_cab_api/src/model/vehicle_type.dart';
import 'package:smart_cab_api/src/model/tracker_type.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'vehicle_input.g.dart';

/// VehicleInput
///
/// Properties:
/// * [registrationNo] 
/// * [model] 
/// * [vehicleType] 
/// * [seatCapacity] 
/// * [trackerType] 
@BuiltValue(instantiable: false)
abstract class VehicleInput  {
  @BuiltValueField(wireName: r'registration_no')
  String get registrationNo;

  @BuiltValueField(wireName: r'model')
  String? get model;

  @BuiltValueField(wireName: r'vehicle_type')
  VehicleType get vehicleType;
  // enum vehicleTypeEnum {  sedan_4,  suv_6,  vip,  };

  @BuiltValueField(wireName: r'seat_capacity')
  int get seatCapacity;

  @BuiltValueField(wireName: r'tracker_type')
  TrackerType? get trackerType;
  // enum trackerTypeEnum {  app,  esp32,  };

  @BuiltValueSerializer(custom: true)
  static Serializer<VehicleInput> get serializer => _$VehicleInputSerializer();
}

class _$VehicleInputSerializer implements PrimitiveSerializer<VehicleInput> {
  @override
  final Iterable<Type> types = const [VehicleInput];

  @override
  final String wireName = r'VehicleInput';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    VehicleInput object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    yield r'registration_no';
    yield serializers.serialize(
      object.registrationNo,
      specifiedType: const FullType(String),
    );
    if (object.model != null) {
      yield r'model';
      yield serializers.serialize(
        object.model,
        specifiedType: const FullType(String),
      );
    }
    yield r'vehicle_type';
    yield serializers.serialize(
      object.vehicleType,
      specifiedType: const FullType(VehicleType),
    );
    yield r'seat_capacity';
    yield serializers.serialize(
      object.seatCapacity,
      specifiedType: const FullType(int),
    );
    if (object.trackerType != null) {
      yield r'tracker_type';
      yield serializers.serialize(
        object.trackerType,
        specifiedType: const FullType(TrackerType),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    VehicleInput object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  @override
  VehicleInput deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return serializers.deserialize(serialized, specifiedType: FullType($VehicleInput)) as $VehicleInput;
  }
}

/// a concrete implementation of [VehicleInput], since [VehicleInput] is not instantiable
@BuiltValue(instantiable: true)
abstract class $VehicleInput implements VehicleInput, Built<$VehicleInput, $VehicleInputBuilder> {
  $VehicleInput._();

  factory $VehicleInput([void Function($VehicleInputBuilder)? updates]) = _$$VehicleInput;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults($VehicleInputBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<$VehicleInput> get serializer => _$$VehicleInputSerializer();
}

class _$$VehicleInputSerializer implements PrimitiveSerializer<$VehicleInput> {
  @override
  final Iterable<Type> types = const [$VehicleInput, _$$VehicleInput];

  @override
  final String wireName = r'$VehicleInput';

  @override
  Object serialize(
    Serializers serializers,
    $VehicleInput object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return serializers.serialize(object, specifiedType: FullType(VehicleInput))!;
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required VehicleInputBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'registration_no':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.registrationNo = valueDes;
          break;
        case r'model':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.model = valueDes;
          break;
        case r'vehicle_type':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(VehicleType),
          ) as VehicleType;
          result.vehicleType = valueDes;
          break;
        case r'seat_capacity':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.seatCapacity = valueDes;
          break;
        case r'tracker_type':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(TrackerType),
          ) as TrackerType;
          result.trackerType = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  $VehicleInput deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = $VehicleInputBuilder();
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

