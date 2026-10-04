//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:smart_cab_api/src/model/driver_input.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'driver.g.dart';

/// Driver
///
/// Properties:
/// * [name] 
/// * [phone] 
/// * [licenceLast4] 
/// * [defaultVehicleId] 
/// * [active] 
/// * [id] 
@BuiltValue()
abstract class Driver implements DriverInput, Built<Driver, DriverBuilder> {
  @BuiltValueField(wireName: r'id')
  String? get id;

  Driver._();

  factory Driver([void updates(DriverBuilder b)]) = _$Driver;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(DriverBuilder b) => b
      ..active = true;

  @BuiltValueSerializer(custom: true)
  static Serializer<Driver> get serializer => _$DriverSerializer();
}

class _$DriverSerializer implements PrimitiveSerializer<Driver> {
  @override
  final Iterable<Type> types = const [Driver, _$Driver];

  @override
  final String wireName = r'Driver';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    Driver object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    yield r'name';
    yield serializers.serialize(
      object.name,
      specifiedType: const FullType(String),
    );
    if (object.active != null) {
      yield r'active';
      yield serializers.serialize(
        object.active,
        specifiedType: const FullType(bool),
      );
    }
    if (object.id != null) {
      yield r'id';
      yield serializers.serialize(
        object.id,
        specifiedType: const FullType(String),
      );
    }
    if (object.licenceLast4 != null) {
      yield r'licence_last4';
      yield serializers.serialize(
        object.licenceLast4,
        specifiedType: const FullType(String),
      );
    }
    yield r'phone';
    yield serializers.serialize(
      object.phone,
      specifiedType: const FullType(String),
    );
    if (object.defaultVehicleId != null) {
      yield r'default_vehicle_id';
      yield serializers.serialize(
        object.defaultVehicleId,
        specifiedType: const FullType.nullable(String),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    Driver object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required DriverBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'name':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.name = valueDes;
          break;
        case r'active':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(bool),
          ) as bool;
          result.active = valueDes;
          break;
        case r'id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.id = valueDes;
          break;
        case r'licence_last4':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.licenceLast4 = valueDes;
          break;
        case r'phone':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.phone = valueDes;
          break;
        case r'default_vehicle_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(String),
          ) as String?;
          if (valueDes == null) continue;
          result.defaultVehicleId = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  Driver deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = DriverBuilder();
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

