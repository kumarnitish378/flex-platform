//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:smart_cab_api/src/model/client.dart';
import 'package:built_collection/built_collection.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'admin_clients_get200_response.g.dart';

/// AdminClientsGet200Response
///
/// Properties:
/// * [items] 
@BuiltValue()
abstract class AdminClientsGet200Response implements Built<AdminClientsGet200Response, AdminClientsGet200ResponseBuilder> {
  @BuiltValueField(wireName: r'items')
  BuiltList<Client> get items;

  AdminClientsGet200Response._();

  factory AdminClientsGet200Response([void updates(AdminClientsGet200ResponseBuilder b)]) = _$AdminClientsGet200Response;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(AdminClientsGet200ResponseBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<AdminClientsGet200Response> get serializer => _$AdminClientsGet200ResponseSerializer();
}

class _$AdminClientsGet200ResponseSerializer implements PrimitiveSerializer<AdminClientsGet200Response> {
  @override
  final Iterable<Type> types = const [AdminClientsGet200Response, _$AdminClientsGet200Response];

  @override
  final String wireName = r'AdminClientsGet200Response';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    AdminClientsGet200Response object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    yield r'items';
    yield serializers.serialize(
      object.items,
      specifiedType: const FullType(BuiltList, [FullType(Client)]),
    );
  }

  @override
  Object serialize(
    Serializers serializers,
    AdminClientsGet200Response object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required AdminClientsGet200ResponseBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'items':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(BuiltList, [FullType(Client)]),
          ) as BuiltList<Client>;
          result.items.replace(valueDes);
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  AdminClientsGet200Response deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = AdminClientsGet200ResponseBuilder();
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

