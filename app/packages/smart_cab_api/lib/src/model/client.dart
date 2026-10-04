//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:smart_cab_api/src/model/client_input.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'client.g.dart';

/// Client
///
/// Properties:
/// * [name] 
/// * [contactName] 
/// * [contactPhone] 
/// * [id] 
@BuiltValue()
abstract class Client implements ClientInput, Built<Client, ClientBuilder> {
  @BuiltValueField(wireName: r'id')
  String? get id;

  Client._();

  factory Client([void updates(ClientBuilder b)]) = _$Client;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(ClientBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<Client> get serializer => _$ClientSerializer();
}

class _$ClientSerializer implements PrimitiveSerializer<Client> {
  @override
  final Iterable<Type> types = const [Client, _$Client];

  @override
  final String wireName = r'Client';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    Client object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    yield r'name';
    yield serializers.serialize(
      object.name,
      specifiedType: const FullType(String),
    );
    if (object.id != null) {
      yield r'id';
      yield serializers.serialize(
        object.id,
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
    if (object.contactName != null) {
      yield r'contact_name';
      yield serializers.serialize(
        object.contactName,
        specifiedType: const FullType(String),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    Client object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required ClientBuilder result,
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
        case r'id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.id = valueDes;
          break;
        case r'contact_phone':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.contactPhone = valueDes;
          break;
        case r'contact_name':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.contactName = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  Client deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = ClientBuilder();
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

