//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_collection/built_collection.dart';
import 'package:smart_cab_api/src/model/candidate.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'dispatch_requests_request_id_candidates_get200_response.g.dart';

/// DispatchRequestsRequestIdCandidatesGet200Response
///
/// Properties:
/// * [items] 
@BuiltValue()
abstract class DispatchRequestsRequestIdCandidatesGet200Response implements Built<DispatchRequestsRequestIdCandidatesGet200Response, DispatchRequestsRequestIdCandidatesGet200ResponseBuilder> {
  @BuiltValueField(wireName: r'items')
  BuiltList<Candidate> get items;

  DispatchRequestsRequestIdCandidatesGet200Response._();

  factory DispatchRequestsRequestIdCandidatesGet200Response([void updates(DispatchRequestsRequestIdCandidatesGet200ResponseBuilder b)]) = _$DispatchRequestsRequestIdCandidatesGet200Response;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(DispatchRequestsRequestIdCandidatesGet200ResponseBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<DispatchRequestsRequestIdCandidatesGet200Response> get serializer => _$DispatchRequestsRequestIdCandidatesGet200ResponseSerializer();
}

class _$DispatchRequestsRequestIdCandidatesGet200ResponseSerializer implements PrimitiveSerializer<DispatchRequestsRequestIdCandidatesGet200Response> {
  @override
  final Iterable<Type> types = const [DispatchRequestsRequestIdCandidatesGet200Response, _$DispatchRequestsRequestIdCandidatesGet200Response];

  @override
  final String wireName = r'DispatchRequestsRequestIdCandidatesGet200Response';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    DispatchRequestsRequestIdCandidatesGet200Response object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    yield r'items';
    yield serializers.serialize(
      object.items,
      specifiedType: const FullType(BuiltList, [FullType(Candidate)]),
    );
  }

  @override
  Object serialize(
    Serializers serializers,
    DispatchRequestsRequestIdCandidatesGet200Response object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required DispatchRequestsRequestIdCandidatesGet200ResponseBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'items':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(BuiltList, [FullType(Candidate)]),
          ) as BuiltList<Candidate>;
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
  DispatchRequestsRequestIdCandidatesGet200Response deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = DispatchRequestsRequestIdCandidatesGet200ResponseBuilder();
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

