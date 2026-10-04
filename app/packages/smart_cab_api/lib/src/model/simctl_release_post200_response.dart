//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'simctl_release_post200_response.g.dart';

/// SimctlReleasePost200Response
///
/// Properties:
/// * [released] 
@BuiltValue()
abstract class SimctlReleasePost200Response implements Built<SimctlReleasePost200Response, SimctlReleasePost200ResponseBuilder> {
  @BuiltValueField(wireName: r'released')
  bool? get released;

  SimctlReleasePost200Response._();

  factory SimctlReleasePost200Response([void updates(SimctlReleasePost200ResponseBuilder b)]) = _$SimctlReleasePost200Response;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(SimctlReleasePost200ResponseBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<SimctlReleasePost200Response> get serializer => _$SimctlReleasePost200ResponseSerializer();
}

class _$SimctlReleasePost200ResponseSerializer implements PrimitiveSerializer<SimctlReleasePost200Response> {
  @override
  final Iterable<Type> types = const [SimctlReleasePost200Response, _$SimctlReleasePost200Response];

  @override
  final String wireName = r'SimctlReleasePost200Response';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    SimctlReleasePost200Response object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.released != null) {
      yield r'released';
      yield serializers.serialize(
        object.released,
        specifiedType: const FullType(bool),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    SimctlReleasePost200Response object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required SimctlReleasePost200ResponseBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'released':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(bool),
          ) as bool;
          result.released = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  SimctlReleasePost200Response deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = SimctlReleasePost200ResponseBuilder();
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

