//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_collection/built_collection.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'suggestion_decision_result.g.dart';

/// SuggestionDecisionResult
///
/// Properties:
/// * [suggestionId] 
/// * [decision] 
/// * [status] 
/// * [tripId] - the trip created or joined; null for `reject`
@BuiltValue()
abstract class SuggestionDecisionResult implements Built<SuggestionDecisionResult, SuggestionDecisionResultBuilder> {
  @BuiltValueField(wireName: r'suggestion_id')
  String? get suggestionId;

  @BuiltValueField(wireName: r'decision')
  SuggestionDecisionResultDecisionEnum? get decision;
  // enum decisionEnum {  approve,  choose_other,  reject,  };

  @BuiltValueField(wireName: r'status')
  SuggestionDecisionResultStatusEnum? get status;
  // enum statusEnum {  accepted,  rejected,  superseded,  expired,  offered,  };

  /// the trip created or joined; null for `reject`
  @BuiltValueField(wireName: r'trip_id')
  String? get tripId;

  SuggestionDecisionResult._();

  factory SuggestionDecisionResult([void updates(SuggestionDecisionResultBuilder b)]) = _$SuggestionDecisionResult;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(SuggestionDecisionResultBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<SuggestionDecisionResult> get serializer => _$SuggestionDecisionResultSerializer();
}

class _$SuggestionDecisionResultSerializer implements PrimitiveSerializer<SuggestionDecisionResult> {
  @override
  final Iterable<Type> types = const [SuggestionDecisionResult, _$SuggestionDecisionResult];

  @override
  final String wireName = r'SuggestionDecisionResult';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    SuggestionDecisionResult object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.suggestionId != null) {
      yield r'suggestion_id';
      yield serializers.serialize(
        object.suggestionId,
        specifiedType: const FullType(String),
      );
    }
    if (object.decision != null) {
      yield r'decision';
      yield serializers.serialize(
        object.decision,
        specifiedType: const FullType(SuggestionDecisionResultDecisionEnum),
      );
    }
    if (object.status != null) {
      yield r'status';
      yield serializers.serialize(
        object.status,
        specifiedType: const FullType(SuggestionDecisionResultStatusEnum),
      );
    }
    if (object.tripId != null) {
      yield r'trip_id';
      yield serializers.serialize(
        object.tripId,
        specifiedType: const FullType.nullable(String),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    SuggestionDecisionResult object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required SuggestionDecisionResultBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'suggestion_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.suggestionId = valueDes;
          break;
        case r'decision':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(SuggestionDecisionResultDecisionEnum),
          ) as SuggestionDecisionResultDecisionEnum;
          result.decision = valueDes;
          break;
        case r'status':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(SuggestionDecisionResultStatusEnum),
          ) as SuggestionDecisionResultStatusEnum;
          result.status = valueDes;
          break;
        case r'trip_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(String),
          ) as String?;
          if (valueDes == null) continue;
          result.tripId = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  SuggestionDecisionResult deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = SuggestionDecisionResultBuilder();
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

class SuggestionDecisionResultDecisionEnum extends EnumClass {

  @BuiltValueEnumConst(wireName: r'approve')
  static const SuggestionDecisionResultDecisionEnum approve = _$suggestionDecisionResultDecisionEnum_approve;
  @BuiltValueEnumConst(wireName: r'choose_other')
  static const SuggestionDecisionResultDecisionEnum chooseOther = _$suggestionDecisionResultDecisionEnum_chooseOther;
  @BuiltValueEnumConst(wireName: r'reject')
  static const SuggestionDecisionResultDecisionEnum reject = _$suggestionDecisionResultDecisionEnum_reject;

  static Serializer<SuggestionDecisionResultDecisionEnum> get serializer => _$suggestionDecisionResultDecisionEnumSerializer;

  const SuggestionDecisionResultDecisionEnum._(String name): super(name);

  static BuiltSet<SuggestionDecisionResultDecisionEnum> get values => _$suggestionDecisionResultDecisionEnumValues;
  static SuggestionDecisionResultDecisionEnum valueOf(String name) => _$suggestionDecisionResultDecisionEnumValueOf(name);
}

class SuggestionDecisionResultStatusEnum extends EnumClass {

  @BuiltValueEnumConst(wireName: r'accepted')
  static const SuggestionDecisionResultStatusEnum accepted = _$suggestionDecisionResultStatusEnum_accepted;
  @BuiltValueEnumConst(wireName: r'rejected')
  static const SuggestionDecisionResultStatusEnum rejected = _$suggestionDecisionResultStatusEnum_rejected;
  @BuiltValueEnumConst(wireName: r'superseded')
  static const SuggestionDecisionResultStatusEnum superseded = _$suggestionDecisionResultStatusEnum_superseded;
  @BuiltValueEnumConst(wireName: r'expired')
  static const SuggestionDecisionResultStatusEnum expired = _$suggestionDecisionResultStatusEnum_expired;
  @BuiltValueEnumConst(wireName: r'offered')
  static const SuggestionDecisionResultStatusEnum offered = _$suggestionDecisionResultStatusEnum_offered;

  static Serializer<SuggestionDecisionResultStatusEnum> get serializer => _$suggestionDecisionResultStatusEnumSerializer;

  const SuggestionDecisionResultStatusEnum._(String name): super(name);

  static BuiltSet<SuggestionDecisionResultStatusEnum> get values => _$suggestionDecisionResultStatusEnumValues;
  static SuggestionDecisionResultStatusEnum valueOf(String name) => _$suggestionDecisionResultStatusEnumValueOf(name);
}

