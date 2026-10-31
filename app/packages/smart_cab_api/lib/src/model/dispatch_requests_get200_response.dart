//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:smart_cab_api/src/model/ride_request.dart';
import 'package:built_collection/built_collection.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'dispatch_requests_get200_response.g.dart';

/// DispatchRequestsGet200Response
///
/// Properties:
/// * [items] 
@BuiltValue()
abstract class DispatchRequestsGet200Response implements Built<DispatchRequestsGet200Response, DispatchRequestsGet200ResponseBuilder> {
  @BuiltValueField(wireName: r'items')
  BuiltList<RideRequest> get items;

  DispatchRequestsGet200Response._();

  factory DispatchRequestsGet200Response([void updates(DispatchRequestsGet200ResponseBuilder b)]) = _$DispatchRequestsGet200Response;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(DispatchRequestsGet200ResponseBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<DispatchRequestsGet200Response> get serializer => _$DispatchRequestsGet200ResponseSerializer();
}

class _$DispatchRequestsGet200ResponseSerializer implements PrimitiveSerializer<DispatchRequestsGet200Response> {
  @override
  final Iterable<Type> types = const [DispatchRequestsGet200Response, _$DispatchRequestsGet200Response];

  @override
  final String wireName = r'DispatchRequestsGet200Response';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    DispatchRequestsGet200Response object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    yield r'items';
    yield serializers.serialize(
      object.items,
      specifiedType: const FullType(BuiltList, [FullType(RideRequest)]),
    );
  }

  @override
  Object serialize(
    Serializers serializers,
    DispatchRequestsGet200Response object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required DispatchRequestsGet200ResponseBuilder result,
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
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  DispatchRequestsGet200Response deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = DispatchRequestsGet200ResponseBuilder();
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

