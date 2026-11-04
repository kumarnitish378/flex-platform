//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'driver_input.g.dart';

/// DriverInput
///
/// Properties:
/// * [name] 
/// * [phone] 
/// * [licenceLast4] 
/// * [defaultVehicleId] 
/// * [active] 
@BuiltValue(instantiable: false)
abstract class DriverInput  {
  @BuiltValueField(wireName: r'name')
  String get name;

  @BuiltValueField(wireName: r'phone')
  String get phone;

  @BuiltValueField(wireName: r'licence_last4')
  String? get licenceLast4;

  @BuiltValueField(wireName: r'default_vehicle_id')
  String? get defaultVehicleId;

  @BuiltValueField(wireName: r'active')
  bool? get active;

  @BuiltValueSerializer(custom: true)
  static Serializer<DriverInput> get serializer => _$DriverInputSerializer();
}

class _$DriverInputSerializer implements PrimitiveSerializer<DriverInput> {
  @override
  final Iterable<Type> types = const [DriverInput];

  @override
  final String wireName = r'DriverInput';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    DriverInput object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    yield r'name';
    yield serializers.serialize(
      object.name,
      specifiedType: const FullType(String),
    );
    yield r'phone';
    yield serializers.serialize(
      object.phone,
      specifiedType: const FullType(String),
    );
    if (object.licenceLast4 != null) {
      yield r'licence_last4';
      yield serializers.serialize(
        object.licenceLast4,
        specifiedType: const FullType(String),
      );
    }
    if (object.defaultVehicleId != null) {
      yield r'default_vehicle_id';
      yield serializers.serialize(
        object.defaultVehicleId,
        specifiedType: const FullType.nullable(String),
      );
    }
    if (object.active != null) {
      yield r'active';
      yield serializers.serialize(
        object.active,
        specifiedType: const FullType(bool),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    DriverInput object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  @override
  DriverInput deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return serializers.deserialize(serialized, specifiedType: FullType($DriverInput)) as $DriverInput;
  }
}

/// a concrete implementation of [DriverInput], since [DriverInput] is not instantiable
@BuiltValue(instantiable: true)
abstract class $DriverInput implements DriverInput, Built<$DriverInput, $DriverInputBuilder> {
  $DriverInput._();

  factory $DriverInput([void Function($DriverInputBuilder)? updates]) = _$$DriverInput;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults($DriverInputBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<$DriverInput> get serializer => _$$DriverInputSerializer();
}

class _$$DriverInputSerializer implements PrimitiveSerializer<$DriverInput> {
  @override
  final Iterable<Type> types = const [$DriverInput, _$$DriverInput];

  @override
  final String wireName = r'$DriverInput';

  @override
  Object serialize(
    Serializers serializers,
    $DriverInput object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return serializers.serialize(object, specifiedType: FullType(DriverInput))!;
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required DriverInputBuilder result,
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
        case r'phone':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.phone = valueDes;
          break;
        case r'licence_last4':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.licenceLast4 = valueDes;
          break;
        case r'default_vehicle_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(String),
          ) as String?;
          if (valueDes == null) continue;
          result.defaultVehicleId = valueDes;
          break;
        case r'active':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(bool),
          ) as bool;
          result.active = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  $DriverInput deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = $DriverInputBuilder();
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

