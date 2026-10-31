//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_collection/built_collection.dart';
import 'package:smart_cab_api/src/model/lat_lng.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'zone_input.g.dart';

/// ZoneInput
///
/// Properties:
/// * [name] 
/// * [boundary] - The outer ring, in order. Send it open or closed - the last point is joined to the first either way. A ring that crosses itself is refused with 422 rather than being silently repaired, because the repair is a guess about which lobe the operator meant. 
/// * [active] 
@BuiltValue(instantiable: false)
abstract class ZoneInput  {
  @BuiltValueField(wireName: r'name')
  String get name;

  /// The outer ring, in order. Send it open or closed - the last point is joined to the first either way. A ring that crosses itself is refused with 422 rather than being silently repaired, because the repair is a guess about which lobe the operator meant. 
  @BuiltValueField(wireName: r'boundary')
  BuiltList<LatLng> get boundary;

  @BuiltValueField(wireName: r'active')
  bool? get active;

  @BuiltValueSerializer(custom: true)
  static Serializer<ZoneInput> get serializer => _$ZoneInputSerializer();
}

class _$ZoneInputSerializer implements PrimitiveSerializer<ZoneInput> {
  @override
  final Iterable<Type> types = const [ZoneInput];

  @override
  final String wireName = r'ZoneInput';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    ZoneInput object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    yield r'name';
    yield serializers.serialize(
      object.name,
      specifiedType: const FullType(String),
    );
    yield r'boundary';
    yield serializers.serialize(
      object.boundary,
      specifiedType: const FullType(BuiltList, [FullType(LatLng)]),
    );
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
    ZoneInput object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  @override
  ZoneInput deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return serializers.deserialize(serialized, specifiedType: FullType($ZoneInput)) as $ZoneInput;
  }
}

/// a concrete implementation of [ZoneInput], since [ZoneInput] is not instantiable
@BuiltValue(instantiable: true)
abstract class $ZoneInput implements ZoneInput, Built<$ZoneInput, $ZoneInputBuilder> {
  $ZoneInput._();

  factory $ZoneInput([void Function($ZoneInputBuilder)? updates]) = _$$ZoneInput;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults($ZoneInputBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<$ZoneInput> get serializer => _$$ZoneInputSerializer();
}

class _$$ZoneInputSerializer implements PrimitiveSerializer<$ZoneInput> {
  @override
  final Iterable<Type> types = const [$ZoneInput, _$$ZoneInput];

  @override
  final String wireName = r'$ZoneInput';

  @override
  Object serialize(
    Serializers serializers,
    $ZoneInput object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return serializers.serialize(object, specifiedType: FullType(ZoneInput))!;
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required ZoneInputBuilder result,
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
        case r'boundary':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(BuiltList, [FullType(LatLng)]),
          ) as BuiltList<LatLng>;
          result.boundary.replace(valueDes);
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
  $ZoneInput deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = $ZoneInputBuilder();
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

