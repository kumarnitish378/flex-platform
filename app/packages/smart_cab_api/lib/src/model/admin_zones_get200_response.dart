//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_collection/built_collection.dart';
import 'package:smart_cab_api/src/model/zone.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'admin_zones_get200_response.g.dart';

/// AdminZonesGet200Response
///
/// Properties:
/// * [items] 
@BuiltValue()
abstract class AdminZonesGet200Response implements Built<AdminZonesGet200Response, AdminZonesGet200ResponseBuilder> {
  @BuiltValueField(wireName: r'items')
  BuiltList<Zone>? get items;

  AdminZonesGet200Response._();

  factory AdminZonesGet200Response([void updates(AdminZonesGet200ResponseBuilder b)]) = _$AdminZonesGet200Response;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(AdminZonesGet200ResponseBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<AdminZonesGet200Response> get serializer => _$AdminZonesGet200ResponseSerializer();
}

class _$AdminZonesGet200ResponseSerializer implements PrimitiveSerializer<AdminZonesGet200Response> {
  @override
  final Iterable<Type> types = const [AdminZonesGet200Response, _$AdminZonesGet200Response];

  @override
  final String wireName = r'AdminZonesGet200Response';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    AdminZonesGet200Response object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.items != null) {
      yield r'items';
      yield serializers.serialize(
        object.items,
        specifiedType: const FullType(BuiltList, [FullType(Zone)]),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    AdminZonesGet200Response object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required AdminZonesGet200ResponseBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'items':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(BuiltList, [FullType(Zone)]),
          ) as BuiltList<Zone>;
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
  AdminZonesGet200Response deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = AdminZonesGet200ResponseBuilder();
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

