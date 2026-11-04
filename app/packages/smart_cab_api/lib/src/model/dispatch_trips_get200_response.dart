//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:smart_cab_api/src/model/trip.dart';
import 'package:built_collection/built_collection.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'dispatch_trips_get200_response.g.dart';

/// DispatchTripsGet200Response
///
/// Properties:
/// * [items] 
@BuiltValue()
abstract class DispatchTripsGet200Response implements Built<DispatchTripsGet200Response, DispatchTripsGet200ResponseBuilder> {
  @BuiltValueField(wireName: r'items')
  BuiltList<Trip>? get items;

  DispatchTripsGet200Response._();

  factory DispatchTripsGet200Response([void updates(DispatchTripsGet200ResponseBuilder b)]) = _$DispatchTripsGet200Response;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(DispatchTripsGet200ResponseBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<DispatchTripsGet200Response> get serializer => _$DispatchTripsGet200ResponseSerializer();
}

class _$DispatchTripsGet200ResponseSerializer implements PrimitiveSerializer<DispatchTripsGet200Response> {
  @override
  final Iterable<Type> types = const [DispatchTripsGet200Response, _$DispatchTripsGet200Response];

  @override
  final String wireName = r'DispatchTripsGet200Response';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    DispatchTripsGet200Response object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.items != null) {
      yield r'items';
      yield serializers.serialize(
        object.items,
        specifiedType: const FullType(BuiltList, [FullType(Trip)]),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    DispatchTripsGet200Response object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required DispatchTripsGet200ResponseBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'items':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(BuiltList, [FullType(Trip)]),
          ) as BuiltList<Trip>;
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
  DispatchTripsGet200Response deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = DispatchTripsGet200ResponseBuilder();
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

