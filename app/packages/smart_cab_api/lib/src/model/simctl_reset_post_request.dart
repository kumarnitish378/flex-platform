//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'simctl_reset_post_request.g.dart';

/// SimctlResetPostRequest
///
/// Properties:
/// * [scenarioYaml] 
@BuiltValue()
abstract class SimctlResetPostRequest implements Built<SimctlResetPostRequest, SimctlResetPostRequestBuilder> {
  @BuiltValueField(wireName: r'scenario_yaml')
  String? get scenarioYaml;

  SimctlResetPostRequest._();

  factory SimctlResetPostRequest([void updates(SimctlResetPostRequestBuilder b)]) = _$SimctlResetPostRequest;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(SimctlResetPostRequestBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<SimctlResetPostRequest> get serializer => _$SimctlResetPostRequestSerializer();
}

class _$SimctlResetPostRequestSerializer implements PrimitiveSerializer<SimctlResetPostRequest> {
  @override
  final Iterable<Type> types = const [SimctlResetPostRequest, _$SimctlResetPostRequest];

  @override
  final String wireName = r'SimctlResetPostRequest';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    SimctlResetPostRequest object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.scenarioYaml != null) {
      yield r'scenario_yaml';
      yield serializers.serialize(
        object.scenarioYaml,
        specifiedType: const FullType(String),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    SimctlResetPostRequest object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required SimctlResetPostRequestBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'scenario_yaml':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.scenarioYaml = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  SimctlResetPostRequest deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = SimctlResetPostRequestBuilder();
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

