//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'dispatch_automation_get200_response.g.dart';

/// DispatchAutomationGet200Response
///
/// Properties:
/// * [automationPaused] 
@BuiltValue()
abstract class DispatchAutomationGet200Response implements Built<DispatchAutomationGet200Response, DispatchAutomationGet200ResponseBuilder> {
  @BuiltValueField(wireName: r'automation_paused')
  bool? get automationPaused;

  DispatchAutomationGet200Response._();

  factory DispatchAutomationGet200Response([void updates(DispatchAutomationGet200ResponseBuilder b)]) = _$DispatchAutomationGet200Response;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(DispatchAutomationGet200ResponseBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<DispatchAutomationGet200Response> get serializer => _$DispatchAutomationGet200ResponseSerializer();
}

class _$DispatchAutomationGet200ResponseSerializer implements PrimitiveSerializer<DispatchAutomationGet200Response> {
  @override
  final Iterable<Type> types = const [DispatchAutomationGet200Response, _$DispatchAutomationGet200Response];

  @override
  final String wireName = r'DispatchAutomationGet200Response';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    DispatchAutomationGet200Response object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.automationPaused != null) {
      yield r'automation_paused';
      yield serializers.serialize(
        object.automationPaused,
        specifiedType: const FullType(bool),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    DispatchAutomationGet200Response object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required DispatchAutomationGet200ResponseBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'automation_paused':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(bool),
          ) as bool;
          result.automationPaused = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  DispatchAutomationGet200Response deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = DispatchAutomationGet200ResponseBuilder();
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

