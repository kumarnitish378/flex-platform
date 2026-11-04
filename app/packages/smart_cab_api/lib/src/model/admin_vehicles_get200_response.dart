//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:smart_cab_api/src/model/vehicle.dart';
import 'package:built_collection/built_collection.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'admin_vehicles_get200_response.g.dart';

/// AdminVehiclesGet200Response
///
/// Properties:
/// * [items] 
/// * [nextCursor] 
@BuiltValue()
abstract class AdminVehiclesGet200Response implements Built<AdminVehiclesGet200Response, AdminVehiclesGet200ResponseBuilder> {
  @BuiltValueField(wireName: r'items')
  BuiltList<Vehicle>? get items;

  @BuiltValueField(wireName: r'next_cursor')
  String? get nextCursor;

  AdminVehiclesGet200Response._();

  factory AdminVehiclesGet200Response([void updates(AdminVehiclesGet200ResponseBuilder b)]) = _$AdminVehiclesGet200Response;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(AdminVehiclesGet200ResponseBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<AdminVehiclesGet200Response> get serializer => _$AdminVehiclesGet200ResponseSerializer();
}

class _$AdminVehiclesGet200ResponseSerializer implements PrimitiveSerializer<AdminVehiclesGet200Response> {
  @override
  final Iterable<Type> types = const [AdminVehiclesGet200Response, _$AdminVehiclesGet200Response];

  @override
  final String wireName = r'AdminVehiclesGet200Response';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    AdminVehiclesGet200Response object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.items != null) {
      yield r'items';
      yield serializers.serialize(
        object.items,
        specifiedType: const FullType(BuiltList, [FullType(Vehicle)]),
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
    AdminVehiclesGet200Response object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required AdminVehiclesGet200ResponseBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'items':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(BuiltList, [FullType(Vehicle)]),
          ) as BuiltList<Vehicle>;
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
  AdminVehiclesGet200Response deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = AdminVehiclesGet200ResponseBuilder();
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

