//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:smart_cab_api/src/model/trip.dart';
import 'package:built_collection/built_collection.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'driver_trips_get200_response.g.dart';

/// DriverTripsGet200Response
///
/// Properties:
/// * [items] 
@BuiltValue()
abstract class DriverTripsGet200Response implements Built<DriverTripsGet200Response, DriverTripsGet200ResponseBuilder> {
  @BuiltValueField(wireName: r'items')
  BuiltList<Trip> get items;

  DriverTripsGet200Response._();

  factory DriverTripsGet200Response([void updates(DriverTripsGet200ResponseBuilder b)]) = _$DriverTripsGet200Response;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(DriverTripsGet200ResponseBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<DriverTripsGet200Response> get serializer => _$DriverTripsGet200ResponseSerializer();
}

class _$DriverTripsGet200ResponseSerializer implements PrimitiveSerializer<DriverTripsGet200Response> {
  @override
  final Iterable<Type> types = const [DriverTripsGet200Response, _$DriverTripsGet200Response];

  @override
  final String wireName = r'DriverTripsGet200Response';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    DriverTripsGet200Response object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    yield r'items';
    yield serializers.serialize(
      object.items,
      specifiedType: const FullType(BuiltList, [FullType(Trip)]),
    );
  }

  @override
  Object serialize(
    Serializers serializers,
    DriverTripsGet200Response object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required DriverTripsGet200ResponseBuilder result,
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
  DriverTripsGet200Response deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = DriverTripsGet200ResponseBuilder();
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

