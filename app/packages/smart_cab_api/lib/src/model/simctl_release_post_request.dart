//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'simctl_release_post_request.g.dart';

/// SimctlReleasePostRequest
///
/// Properties:
/// * [runId] - the id that made the claim
@BuiltValue()
abstract class SimctlReleasePostRequest implements Built<SimctlReleasePostRequest, SimctlReleasePostRequestBuilder> {
  /// the id that made the claim
  @BuiltValueField(wireName: r'run_id')
  String get runId;

  SimctlReleasePostRequest._();

  factory SimctlReleasePostRequest([void updates(SimctlReleasePostRequestBuilder b)]) = _$SimctlReleasePostRequest;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(SimctlReleasePostRequestBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<SimctlReleasePostRequest> get serializer => _$SimctlReleasePostRequestSerializer();
}

class _$SimctlReleasePostRequestSerializer implements PrimitiveSerializer<SimctlReleasePostRequest> {
  @override
  final Iterable<Type> types = const [SimctlReleasePostRequest, _$SimctlReleasePostRequest];

  @override
  final String wireName = r'SimctlReleasePostRequest';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    SimctlReleasePostRequest object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    yield r'run_id';
    yield serializers.serialize(
      object.runId,
      specifiedType: const FullType(String),
    );
  }

  @override
  Object serialize(
    Serializers serializers,
    SimctlReleasePostRequest object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required SimctlReleasePostRequestBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'run_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.runId = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  SimctlReleasePostRequest deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = SimctlReleasePostRequestBuilder();
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

