//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'driver_trips_trip_id_start_post_request.g.dart';

/// DriverTripsTripIdStartPostRequest
///
/// Properties:
/// * [clientEventId] - idempotency key generated on device
/// * [occurredAt] 
/// * [lat] 
/// * [lng] 
@BuiltValue()
abstract class DriverTripsTripIdStartPostRequest implements Built<DriverTripsTripIdStartPostRequest, DriverTripsTripIdStartPostRequestBuilder> {
  /// idempotency key generated on device
  @BuiltValueField(wireName: r'client_event_id')
  String get clientEventId;

  @BuiltValueField(wireName: r'occurred_at')
  DateTime get occurredAt;

  @BuiltValueField(wireName: r'lat')
  num? get lat;

  @BuiltValueField(wireName: r'lng')
  num? get lng;

  DriverTripsTripIdStartPostRequest._();

  factory DriverTripsTripIdStartPostRequest([void updates(DriverTripsTripIdStartPostRequestBuilder b)]) = _$DriverTripsTripIdStartPostRequest;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(DriverTripsTripIdStartPostRequestBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<DriverTripsTripIdStartPostRequest> get serializer => _$DriverTripsTripIdStartPostRequestSerializer();
}

class _$DriverTripsTripIdStartPostRequestSerializer implements PrimitiveSerializer<DriverTripsTripIdStartPostRequest> {
  @override
  final Iterable<Type> types = const [DriverTripsTripIdStartPostRequest, _$DriverTripsTripIdStartPostRequest];

  @override
  final String wireName = r'DriverTripsTripIdStartPostRequest';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    DriverTripsTripIdStartPostRequest object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    yield r'client_event_id';
    yield serializers.serialize(
      object.clientEventId,
      specifiedType: const FullType(String),
    );
    yield r'occurred_at';
    yield serializers.serialize(
      object.occurredAt,
      specifiedType: const FullType(DateTime),
    );
    if (object.lat != null) {
      yield r'lat';
      yield serializers.serialize(
        object.lat,
        specifiedType: const FullType(num),
      );
    }
    if (object.lng != null) {
      yield r'lng';
      yield serializers.serialize(
        object.lng,
        specifiedType: const FullType(num),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    DriverTripsTripIdStartPostRequest object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required DriverTripsTripIdStartPostRequestBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'client_event_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.clientEventId = valueDes;
          break;
        case r'occurred_at':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(DateTime),
          ) as DateTime;
          result.occurredAt = valueDes;
          break;
        case r'lat':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(num),
          ) as num;
          result.lat = valueDes;
          break;
        case r'lng':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(num),
          ) as num;
          result.lng = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  DriverTripsTripIdStartPostRequest deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = DriverTripsTripIdStartPostRequestBuilder();
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

