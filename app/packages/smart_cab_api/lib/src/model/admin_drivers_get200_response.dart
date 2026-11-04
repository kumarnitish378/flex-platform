//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_collection/built_collection.dart';
import 'package:smart_cab_api/src/model/driver.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'admin_drivers_get200_response.g.dart';

/// AdminDriversGet200Response
///
/// Properties:
/// * [items] 
/// * [nextCursor] 
@BuiltValue()
abstract class AdminDriversGet200Response implements Built<AdminDriversGet200Response, AdminDriversGet200ResponseBuilder> {
  @BuiltValueField(wireName: r'items')
  BuiltList<Driver>? get items;

  @BuiltValueField(wireName: r'next_cursor')
  String? get nextCursor;

  AdminDriversGet200Response._();

  factory AdminDriversGet200Response([void updates(AdminDriversGet200ResponseBuilder b)]) = _$AdminDriversGet200Response;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(AdminDriversGet200ResponseBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<AdminDriversGet200Response> get serializer => _$AdminDriversGet200ResponseSerializer();
}

class _$AdminDriversGet200ResponseSerializer implements PrimitiveSerializer<AdminDriversGet200Response> {
  @override
  final Iterable<Type> types = const [AdminDriversGet200Response, _$AdminDriversGet200Response];

  @override
  final String wireName = r'AdminDriversGet200Response';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    AdminDriversGet200Response object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.items != null) {
      yield r'items';
      yield serializers.serialize(
        object.items,
        specifiedType: const FullType(BuiltList, [FullType(Driver)]),
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
    AdminDriversGet200Response object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required AdminDriversGet200ResponseBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'items':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(BuiltList, [FullType(Driver)]),
          ) as BuiltList<Driver>;
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
  AdminDriversGet200Response deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = AdminDriversGet200ResponseBuilder();
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

