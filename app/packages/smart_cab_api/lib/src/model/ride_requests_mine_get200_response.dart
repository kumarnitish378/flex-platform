//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:smart_cab_api/src/model/ride_request.dart';
import 'package:built_collection/built_collection.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'ride_requests_mine_get200_response.g.dart';

/// RideRequestsMineGet200Response
///
/// Properties:
/// * [items] 
/// * [nextCursor] 
@BuiltValue()
abstract class RideRequestsMineGet200Response implements Built<RideRequestsMineGet200Response, RideRequestsMineGet200ResponseBuilder> {
  @BuiltValueField(wireName: r'items')
  BuiltList<RideRequest>? get items;

  @BuiltValueField(wireName: r'next_cursor')
  String? get nextCursor;

  RideRequestsMineGet200Response._();

  factory RideRequestsMineGet200Response([void updates(RideRequestsMineGet200ResponseBuilder b)]) = _$RideRequestsMineGet200Response;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(RideRequestsMineGet200ResponseBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<RideRequestsMineGet200Response> get serializer => _$RideRequestsMineGet200ResponseSerializer();
}

class _$RideRequestsMineGet200ResponseSerializer implements PrimitiveSerializer<RideRequestsMineGet200Response> {
  @override
  final Iterable<Type> types = const [RideRequestsMineGet200Response, _$RideRequestsMineGet200Response];

  @override
  final String wireName = r'RideRequestsMineGet200Response';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    RideRequestsMineGet200Response object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.items != null) {
      yield r'items';
      yield serializers.serialize(
        object.items,
        specifiedType: const FullType(BuiltList, [FullType(RideRequest)]),
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
    RideRequestsMineGet200Response object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required RideRequestsMineGet200ResponseBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'items':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(BuiltList, [FullType(RideRequest)]),
          ) as BuiltList<RideRequest>;
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
  RideRequestsMineGet200Response deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = RideRequestsMineGet200ResponseBuilder();
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

