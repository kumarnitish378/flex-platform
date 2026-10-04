//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_collection/built_collection.dart';
import 'package:smart_cab_api/src/model/employee.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'admin_clients_client_id_employees_get200_response.g.dart';

/// AdminClientsClientIdEmployeesGet200Response
///
/// Properties:
/// * [items] 
/// * [nextCursor] 
@BuiltValue()
abstract class AdminClientsClientIdEmployeesGet200Response implements Built<AdminClientsClientIdEmployeesGet200Response, AdminClientsClientIdEmployeesGet200ResponseBuilder> {
  @BuiltValueField(wireName: r'items')
  BuiltList<Employee>? get items;

  @BuiltValueField(wireName: r'next_cursor')
  String? get nextCursor;

  AdminClientsClientIdEmployeesGet200Response._();

  factory AdminClientsClientIdEmployeesGet200Response([void updates(AdminClientsClientIdEmployeesGet200ResponseBuilder b)]) = _$AdminClientsClientIdEmployeesGet200Response;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(AdminClientsClientIdEmployeesGet200ResponseBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<AdminClientsClientIdEmployeesGet200Response> get serializer => _$AdminClientsClientIdEmployeesGet200ResponseSerializer();
}

class _$AdminClientsClientIdEmployeesGet200ResponseSerializer implements PrimitiveSerializer<AdminClientsClientIdEmployeesGet200Response> {
  @override
  final Iterable<Type> types = const [AdminClientsClientIdEmployeesGet200Response, _$AdminClientsClientIdEmployeesGet200Response];

  @override
  final String wireName = r'AdminClientsClientIdEmployeesGet200Response';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    AdminClientsClientIdEmployeesGet200Response object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.items != null) {
      yield r'items';
      yield serializers.serialize(
        object.items,
        specifiedType: const FullType(BuiltList, [FullType(Employee)]),
      );
    }
    if (object.nextCursor != null) {
      yield r'next_cursor';
      yield serializers.serialize(
        object.nextCursor,
        specifiedType: const FullType.nullable(String),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    AdminClientsClientIdEmployeesGet200Response object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required AdminClientsClientIdEmployeesGet200ResponseBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'items':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(BuiltList, [FullType(Employee)]),
          ) as BuiltList<Employee>;
          result.items.replace(valueDes);
          break;
        case r'next_cursor':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(String),
          ) as String?;
          if (valueDes == null) continue;
          result.nextCursor = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  AdminClientsClientIdEmployeesGet200Response deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = AdminClientsClientIdEmployeesGet200ResponseBuilder();
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

