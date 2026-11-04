//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'client_input.g.dart';

/// ClientInput
///
/// Properties:
/// * [name] 
/// * [contactName] 
/// * [contactPhone] 
@BuiltValue(instantiable: false)
abstract class ClientInput  {
  @BuiltValueField(wireName: r'name')
  String get name;

  @BuiltValueField(wireName: r'contact_name')
  String? get contactName;

  @BuiltValueField(wireName: r'contact_phone')
  String? get contactPhone;

  @BuiltValueSerializer(custom: true)
  static Serializer<ClientInput> get serializer => _$ClientInputSerializer();
}

class _$ClientInputSerializer implements PrimitiveSerializer<ClientInput> {
  @override
  final Iterable<Type> types = const [ClientInput];

  @override
  final String wireName = r'ClientInput';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    ClientInput object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    yield r'name';
    yield serializers.serialize(
      object.name,
      specifiedType: const FullType(String),
    );
    if (object.contactName != null) {
      yield r'contact_name';
      yield serializers.serialize(
        object.contactName,
        specifiedType: const FullType(String),
      );
    }
    if (object.contactPhone != null) {
      yield r'contact_phone';
      yield serializers.serialize(
        object.contactPhone,
        specifiedType: const FullType(String),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    ClientInput object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  @override
  ClientInput deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return serializers.deserialize(serialized, specifiedType: FullType($ClientInput)) as $ClientInput;
  }
}

/// a concrete implementation of [ClientInput], since [ClientInput] is not instantiable
@BuiltValue(instantiable: true)
abstract class $ClientInput implements ClientInput, Built<$ClientInput, $ClientInputBuilder> {
  $ClientInput._();

  factory $ClientInput([void Function($ClientInputBuilder)? updates]) = _$$ClientInput;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults($ClientInputBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<$ClientInput> get serializer => _$$ClientInputSerializer();
}

class _$$ClientInputSerializer implements PrimitiveSerializer<$ClientInput> {
  @override
  final Iterable<Type> types = const [$ClientInput, _$$ClientInput];

  @override
  final String wireName = r'$ClientInput';

  @override
  Object serialize(
    Serializers serializers,
    $ClientInput object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return serializers.serialize(object, specifiedType: FullType(ClientInput))!;
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required ClientInputBuilder result,
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
        case r'contact_name':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.contactName = valueDes;
          break;
        case r'contact_phone':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.contactPhone = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  $ClientInput deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = $ClientInputBuilder();
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

