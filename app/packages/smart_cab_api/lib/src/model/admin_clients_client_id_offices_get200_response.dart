//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_collection/built_collection.dart';
import 'package:smart_cab_api/src/model/office.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'admin_clients_client_id_offices_get200_response.g.dart';

/// AdminClientsClientIdOfficesGet200Response
///
/// Properties:
/// * [items] 
@BuiltValue()
abstract class AdminClientsClientIdOfficesGet200Response implements Built<AdminClientsClientIdOfficesGet200Response, AdminClientsClientIdOfficesGet200ResponseBuilder> {
  @BuiltValueField(wireName: r'items')
  BuiltList<Office> get items;

  AdminClientsClientIdOfficesGet200Response._();

  factory AdminClientsClientIdOfficesGet200Response([void updates(AdminClientsClientIdOfficesGet200ResponseBuilder b)]) = _$AdminClientsClientIdOfficesGet200Response;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(AdminClientsClientIdOfficesGet200ResponseBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<AdminClientsClientIdOfficesGet200Response> get serializer => _$AdminClientsClientIdOfficesGet200ResponseSerializer();
}

class _$AdminClientsClientIdOfficesGet200ResponseSerializer implements PrimitiveSerializer<AdminClientsClientIdOfficesGet200Response> {
  @override
  final Iterable<Type> types = const [AdminClientsClientIdOfficesGet200Response, _$AdminClientsClientIdOfficesGet200Response];

  @override
  final String wireName = r'AdminClientsClientIdOfficesGet200Response';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    AdminClientsClientIdOfficesGet200Response object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    yield r'items';
    yield serializers.serialize(
      object.items,
      specifiedType: const FullType(BuiltList, [FullType(Office)]),
    );
  }

  @override
  Object serialize(
    Serializers serializers,
    AdminClientsClientIdOfficesGet200Response object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required AdminClientsClientIdOfficesGet200ResponseBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'items':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(BuiltList, [FullType(Office)]),
          ) as BuiltList<Office>;
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
  AdminClientsClientIdOfficesGet200Response deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = AdminClientsClientIdOfficesGet200ResponseBuilder();
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

