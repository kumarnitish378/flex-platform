//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:smart_cab_api/src/model/lat_lng.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'office_input.g.dart';

/// OfficeInput
///
/// Properties:
/// * [name] 
/// * [location] 
/// * [addressText] 
@BuiltValue(instantiable: false)
abstract class OfficeInput  {
  @BuiltValueField(wireName: r'name')
  String get name;

  @BuiltValueField(wireName: r'location')
  LatLng get location;

  @BuiltValueField(wireName: r'address_text')
  String? get addressText;

  @BuiltValueSerializer(custom: true)
  static Serializer<OfficeInput> get serializer => _$OfficeInputSerializer();
}

class _$OfficeInputSerializer implements PrimitiveSerializer<OfficeInput> {
  @override
  final Iterable<Type> types = const [OfficeInput];

  @override
  final String wireName = r'OfficeInput';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    OfficeInput object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    yield r'name';
    yield serializers.serialize(
      object.name,
      specifiedType: const FullType(String),
    );
    yield r'location';
    yield serializers.serialize(
      object.location,
      specifiedType: const FullType(LatLng),
    );
    if (object.addressText != null) {
      yield r'address_text';
      yield serializers.serialize(
        object.addressText,
        specifiedType: const FullType(String),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    OfficeInput object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  @override
  OfficeInput deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return serializers.deserialize(serialized, specifiedType: FullType($OfficeInput)) as $OfficeInput;
  }
}

/// a concrete implementation of [OfficeInput], since [OfficeInput] is not instantiable
@BuiltValue(instantiable: true)
abstract class $OfficeInput implements OfficeInput, Built<$OfficeInput, $OfficeInputBuilder> {
  $OfficeInput._();

  factory $OfficeInput([void Function($OfficeInputBuilder)? updates]) = _$$OfficeInput;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults($OfficeInputBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<$OfficeInput> get serializer => _$$OfficeInputSerializer();
}

class _$$OfficeInputSerializer implements PrimitiveSerializer<$OfficeInput> {
  @override
  final Iterable<Type> types = const [$OfficeInput, _$$OfficeInput];

  @override
  final String wireName = r'$OfficeInput';

  @override
  Object serialize(
    Serializers serializers,
    $OfficeInput object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return serializers.serialize(object, specifiedType: FullType(OfficeInput))!;
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required OfficeInputBuilder result,
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
        case r'location':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(LatLng),
          ) as LatLng;
          result.location.replace(valueDes);
          break;
        case r'address_text':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.addressText = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  $OfficeInput deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = $OfficeInputBuilder();
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

