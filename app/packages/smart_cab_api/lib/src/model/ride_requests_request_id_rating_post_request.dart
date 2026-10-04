//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'ride_requests_request_id_rating_post_request.g.dart';

/// RideRequestsRequestIdRatingPostRequest
///
/// Properties:
/// * [rating] 
/// * [comment] 
@BuiltValue()
abstract class RideRequestsRequestIdRatingPostRequest implements Built<RideRequestsRequestIdRatingPostRequest, RideRequestsRequestIdRatingPostRequestBuilder> {
  @BuiltValueField(wireName: r'rating')
  int get rating;

  @BuiltValueField(wireName: r'comment')
  String? get comment;

  RideRequestsRequestIdRatingPostRequest._();

  factory RideRequestsRequestIdRatingPostRequest([void updates(RideRequestsRequestIdRatingPostRequestBuilder b)]) = _$RideRequestsRequestIdRatingPostRequest;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(RideRequestsRequestIdRatingPostRequestBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<RideRequestsRequestIdRatingPostRequest> get serializer => _$RideRequestsRequestIdRatingPostRequestSerializer();
}

class _$RideRequestsRequestIdRatingPostRequestSerializer implements PrimitiveSerializer<RideRequestsRequestIdRatingPostRequest> {
  @override
  final Iterable<Type> types = const [RideRequestsRequestIdRatingPostRequest, _$RideRequestsRequestIdRatingPostRequest];

  @override
  final String wireName = r'RideRequestsRequestIdRatingPostRequest';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    RideRequestsRequestIdRatingPostRequest object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    yield r'rating';
    yield serializers.serialize(
      object.rating,
      specifiedType: const FullType(int),
    );
    if (object.comment != null) {
      yield r'comment';
      yield serializers.serialize(
        object.comment,
        specifiedType: const FullType(String),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    RideRequestsRequestIdRatingPostRequest object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required RideRequestsRequestIdRatingPostRequestBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'rating':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.rating = valueDes;
          break;
        case r'comment':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.comment = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  RideRequestsRequestIdRatingPostRequest deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = RideRequestsRequestIdRatingPostRequestBuilder();
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

