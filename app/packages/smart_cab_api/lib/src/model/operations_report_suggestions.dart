//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'operations_report_suggestions.g.dart';

/// rank-1 suggestions settled in the period (OQ-39 - see the endpoint)
///
/// Properties:
/// * [answeredByAPerson] 
/// * [accepted] 
/// * [rejected] 
/// * [failsafeAssigned] 
/// * [rejectedForAnOfferedAlternative] 
/// * [acceptanceRate] 
/// * [acceptanceRateWithAlternatives] 
@BuiltValue()
abstract class OperationsReportSuggestions implements Built<OperationsReportSuggestions, OperationsReportSuggestionsBuilder> {
  @BuiltValueField(wireName: r'answered_by_a_person')
  int? get answeredByAPerson;

  @BuiltValueField(wireName: r'accepted')
  int? get accepted;

  @BuiltValueField(wireName: r'rejected')
  int? get rejected;

  @BuiltValueField(wireName: r'failsafe_assigned')
  int? get failsafeAssigned;

  @BuiltValueField(wireName: r'rejected_for_an_offered_alternative')
  int? get rejectedForAnOfferedAlternative;

  @BuiltValueField(wireName: r'acceptance_rate')
  num? get acceptanceRate;

  @BuiltValueField(wireName: r'acceptance_rate_with_alternatives')
  num? get acceptanceRateWithAlternatives;

  OperationsReportSuggestions._();

  factory OperationsReportSuggestions([void updates(OperationsReportSuggestionsBuilder b)]) = _$OperationsReportSuggestions;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(OperationsReportSuggestionsBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<OperationsReportSuggestions> get serializer => _$OperationsReportSuggestionsSerializer();
}

class _$OperationsReportSuggestionsSerializer implements PrimitiveSerializer<OperationsReportSuggestions> {
  @override
  final Iterable<Type> types = const [OperationsReportSuggestions, _$OperationsReportSuggestions];

  @override
  final String wireName = r'OperationsReportSuggestions';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    OperationsReportSuggestions object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.answeredByAPerson != null) {
      yield r'answered_by_a_person';
      yield serializers.serialize(
        object.answeredByAPerson,
        specifiedType: const FullType(int),
      );
    }
    if (object.accepted != null) {
      yield r'accepted';
      yield serializers.serialize(
        object.accepted,
        specifiedType: const FullType(int),
      );
    }
    if (object.rejected != null) {
      yield r'rejected';
      yield serializers.serialize(
        object.rejected,
        specifiedType: const FullType(int),
      );
    }
    if (object.failsafeAssigned != null) {
      yield r'failsafe_assigned';
      yield serializers.serialize(
        object.failsafeAssigned,
        specifiedType: const FullType(int),
      );
    }
    if (object.rejectedForAnOfferedAlternative != null) {
      yield r'rejected_for_an_offered_alternative';
      yield serializers.serialize(
        object.rejectedForAnOfferedAlternative,
        specifiedType: const FullType(int),
      );
    }
    if (object.acceptanceRate != null) {
      yield r'acceptance_rate';
      yield serializers.serialize(
        object.acceptanceRate,
        specifiedType: const FullType.nullable(num),
      );
    }
    if (object.acceptanceRateWithAlternatives != null) {
      yield r'acceptance_rate_with_alternatives';
      yield serializers.serialize(
        object.acceptanceRateWithAlternatives,
        specifiedType: const FullType.nullable(num),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    OperationsReportSuggestions object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required OperationsReportSuggestionsBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'answered_by_a_person':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.answeredByAPerson = valueDes;
          break;
        case r'accepted':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.accepted = valueDes;
          break;
        case r'rejected':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.rejected = valueDes;
          break;
        case r'failsafe_assigned':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.failsafeAssigned = valueDes;
          break;
        case r'rejected_for_an_offered_alternative':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.rejectedForAnOfferedAlternative = valueDes;
          break;
        case r'acceptance_rate':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(num),
          ) as num?;
          if (valueDes == null) continue;
          result.acceptanceRate = valueDes;
          break;
        case r'acceptance_rate_with_alternatives':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(num),
          ) as num?;
          if (valueDes == null) continue;
          result.acceptanceRateWithAlternatives = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  OperationsReportSuggestions deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = OperationsReportSuggestionsBuilder();
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

