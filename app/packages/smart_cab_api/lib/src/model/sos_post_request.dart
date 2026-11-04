//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'sos_post_request.g.dart';

/// SosPostRequest
///
/// Properties:
/// * [tripId] 
/// * [lat] 
/// * [lng] 
@BuiltValue()
abstract class SosPostRequest implements Built<SosPostRequest, SosPostRequestBuilder> {
  @BuiltValueField(wireName: r'trip_id')
  String? get tripId;

  @BuiltValueField(wireName: r'lat')
  num get lat;

  @BuiltValueField(wireName: r'lng')
  num get lng;

  SosPostRequest._();

  factory SosPostRequest([void updates(SosPostRequestBuilder b)]) = _$SosPostRequest;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(SosPostRequestBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<SosPostRequest> get serializer => _$SosPostRequestSerializer();
}

class _$SosPostRequestSerializer implements PrimitiveSerializer<SosPostRequest> {
  @override
  final Iterable<Type> types = const [SosPostRequest, _$SosPostRequest];

  @override
  final String wireName = r'SosPostRequest';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    SosPostRequest object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.tripId != null) {
      yield r'trip_id';
      yield serializers.serialize(
        object.tripId,
        specifiedType: const FullType.nullable(String),
      );
    }
    yield r'lat';
    yield serializers.serialize(
      object.lat,
      specifiedType: const FullType(num),
    );
    yield r'lng';
    yield serializers.serialize(
      object.lng,
      specifiedType: const FullType(num),
    );
  }

  @override
  Object serialize(
    Serializers serializers,
    SosPostRequest object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required SosPostRequestBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'trip_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(String),
          ) as String?;
          if (valueDes == null) continue;
          result.tripId = valueDes;
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
  SosPostRequest deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = SosPostRequestBuilder();
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

