//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_collection/built_collection.dart';
import 'package:smart_cab_api/src/model/reason_code.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'dispatch_suggestions_suggestion_id_decision_post_request.g.dart';

/// DispatchSuggestionsSuggestionIdDecisionPostRequest
///
/// Properties:
/// * [decision] 
/// * [vehicleId] 
/// * [reasonCode] 
@BuiltValue()
abstract class DispatchSuggestionsSuggestionIdDecisionPostRequest implements Built<DispatchSuggestionsSuggestionIdDecisionPostRequest, DispatchSuggestionsSuggestionIdDecisionPostRequestBuilder> {
  @BuiltValueField(wireName: r'decision')
  DispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnum get decision;
  // enum decisionEnum {  approve,  choose_other,  reject,  };

  @BuiltValueField(wireName: r'vehicle_id')
  String? get vehicleId;

  @BuiltValueField(wireName: r'reason_code')
  ReasonCode? get reasonCode;
  // enum reasonCodeEnum {  driver_issue,  local_knowledge,  client_request,  traffic,  vehicle_issue,  safety,  other,  };

  DispatchSuggestionsSuggestionIdDecisionPostRequest._();

  factory DispatchSuggestionsSuggestionIdDecisionPostRequest([void updates(DispatchSuggestionsSuggestionIdDecisionPostRequestBuilder b)]) = _$DispatchSuggestionsSuggestionIdDecisionPostRequest;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(DispatchSuggestionsSuggestionIdDecisionPostRequestBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<DispatchSuggestionsSuggestionIdDecisionPostRequest> get serializer => _$DispatchSuggestionsSuggestionIdDecisionPostRequestSerializer();
}

class _$DispatchSuggestionsSuggestionIdDecisionPostRequestSerializer implements PrimitiveSerializer<DispatchSuggestionsSuggestionIdDecisionPostRequest> {
  @override
  final Iterable<Type> types = const [DispatchSuggestionsSuggestionIdDecisionPostRequest, _$DispatchSuggestionsSuggestionIdDecisionPostRequest];

  @override
  final String wireName = r'DispatchSuggestionsSuggestionIdDecisionPostRequest';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    DispatchSuggestionsSuggestionIdDecisionPostRequest object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    yield r'decision';
    yield serializers.serialize(
      object.decision,
      specifiedType: const FullType(DispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnum),
    );
    if (object.vehicleId != null) {
      yield r'vehicle_id';
      yield serializers.serialize(
        object.vehicleId,
        specifiedType: const FullType.nullable(String),
      );
    }
    if (object.reasonCode != null) {
      yield r'reason_code';
      yield serializers.serialize(
        object.reasonCode,
        specifiedType: const FullType(ReasonCode),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    DispatchSuggestionsSuggestionIdDecisionPostRequest object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required DispatchSuggestionsSuggestionIdDecisionPostRequestBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'decision':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(DispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnum),
          ) as DispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnum;
          result.decision = valueDes;
          break;
        case r'vehicle_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(String),
          ) as String?;
          if (valueDes == null) continue;
          result.vehicleId = valueDes;
          break;
        case r'reason_code':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(ReasonCode),
          ) as ReasonCode;
          result.reasonCode = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  DispatchSuggestionsSuggestionIdDecisionPostRequest deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = DispatchSuggestionsSuggestionIdDecisionPostRequestBuilder();
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

class DispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnum extends EnumClass {

  @BuiltValueEnumConst(wireName: r'approve')
  static const DispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnum approve = _$dispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnum_approve;
  @BuiltValueEnumConst(wireName: r'choose_other')
  static const DispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnum chooseOther = _$dispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnum_chooseOther;
  @BuiltValueEnumConst(wireName: r'reject')
  static const DispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnum reject = _$dispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnum_reject;

  static Serializer<DispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnum> get serializer => _$dispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnumSerializer;

  const DispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnum._(String name): super(name);

  static BuiltSet<DispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnum> get values => _$dispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnumValues;
  static DispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnum valueOf(String name) => _$dispatchSuggestionsSuggestionIdDecisionPostRequestDecisionEnumValueOf(name);
}

