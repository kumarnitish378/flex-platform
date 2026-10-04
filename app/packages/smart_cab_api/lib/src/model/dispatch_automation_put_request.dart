//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:smart_cab_api/src/model/reason_code.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'dispatch_automation_put_request.g.dart';

/// DispatchAutomationPutRequest
///
/// Properties:
/// * [automationPaused] 
/// * [reasonCode] 
/// * [note] 
@BuiltValue()
abstract class DispatchAutomationPutRequest implements Built<DispatchAutomationPutRequest, DispatchAutomationPutRequestBuilder> {
  @BuiltValueField(wireName: r'automation_paused')
  bool get automationPaused;

  @BuiltValueField(wireName: r'reason_code')
  ReasonCode get reasonCode;
  // enum reasonCodeEnum {  driver_issue,  local_knowledge,  client_request,  traffic,  vehicle_issue,  safety,  other,  };

  @BuiltValueField(wireName: r'note')
  String? get note;

  DispatchAutomationPutRequest._();

  factory DispatchAutomationPutRequest([void updates(DispatchAutomationPutRequestBuilder b)]) = _$DispatchAutomationPutRequest;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(DispatchAutomationPutRequestBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<DispatchAutomationPutRequest> get serializer => _$DispatchAutomationPutRequestSerializer();
}

class _$DispatchAutomationPutRequestSerializer implements PrimitiveSerializer<DispatchAutomationPutRequest> {
  @override
  final Iterable<Type> types = const [DispatchAutomationPutRequest, _$DispatchAutomationPutRequest];

  @override
  final String wireName = r'DispatchAutomationPutRequest';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    DispatchAutomationPutRequest object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    yield r'automation_paused';
    yield serializers.serialize(
      object.automationPaused,
      specifiedType: const FullType(bool),
    );
    yield r'reason_code';
    yield serializers.serialize(
      object.reasonCode,
      specifiedType: const FullType(ReasonCode),
    );
    if (object.note != null) {
      yield r'note';
      yield serializers.serialize(
        object.note,
        specifiedType: const FullType(String),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    DispatchAutomationPutRequest object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required DispatchAutomationPutRequestBuilder result,
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
        case r'reason_code':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(ReasonCode),
          ) as ReasonCode;
          result.reasonCode = valueDes;
          break;
        case r'note':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.note = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  DispatchAutomationPutRequest deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = DispatchAutomationPutRequestBuilder();
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

