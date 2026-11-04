//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_collection/built_collection.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'suggestion.g.dart';

/// One offer the system made, and what became of it.
///
/// Properties:
/// * [id] 
/// * [requestId] 
/// * [vehicleId] 
/// * [tripId] - The trip this would join; null opens a new one.
/// * [rank] - 1 is the system's first choice.
/// * [cost] 
/// * [reasons] - The plain-text phrases exactly as they were offered. Kept verbatim rather than recomputed: \"+4 min for Rahul\" is the claim the supervisor acted on, and recomputing it later answers against a different world. 
/// * [status] - `accepted` means a supervisor approved it. `failsafe_assigned` means nobody answered and the platform assigned it anyway (§4) - a separate state because counting it as an acceptance would let an unwatched scope score 100% on Phase 2's exit criterion. 
/// * [offeredAt] 
/// * [failsafeDueAt] - When the failsafe acts if nobody answers. The countdown on S-05.
/// * [escalatedAt] 
/// * [decidedAt] 
@BuiltValue()
abstract class Suggestion implements Built<Suggestion, SuggestionBuilder> {
  @BuiltValueField(wireName: r'id')
  String? get id;

  @BuiltValueField(wireName: r'request_id')
  String? get requestId;

  @BuiltValueField(wireName: r'vehicle_id')
  String? get vehicleId;

  /// The trip this would join; null opens a new one.
  @BuiltValueField(wireName: r'trip_id')
  String? get tripId;

  /// 1 is the system's first choice.
  @BuiltValueField(wireName: r'rank')
  int? get rank;

  @BuiltValueField(wireName: r'cost')
  num? get cost;

  /// The plain-text phrases exactly as they were offered. Kept verbatim rather than recomputed: \"+4 min for Rahul\" is the claim the supervisor acted on, and recomputing it later answers against a different world. 
  @BuiltValueField(wireName: r'reasons')
  BuiltList<String>? get reasons;

  /// `accepted` means a supervisor approved it. `failsafe_assigned` means nobody answered and the platform assigned it anyway (§4) - a separate state because counting it as an acceptance would let an unwatched scope score 100% on Phase 2's exit criterion. 
  @BuiltValueField(wireName: r'status')
  SuggestionStatusEnum? get status;
  // enum statusEnum {  offered,  accepted,  rejected,  superseded,  expired,  failsafe_assigned,  };

  @BuiltValueField(wireName: r'offered_at')
  DateTime? get offeredAt;

  /// When the failsafe acts if nobody answers. The countdown on S-05.
  @BuiltValueField(wireName: r'failsafe_due_at')
  DateTime? get failsafeDueAt;

  @BuiltValueField(wireName: r'escalated_at')
  DateTime? get escalatedAt;

  @BuiltValueField(wireName: r'decided_at')
  DateTime? get decidedAt;

  Suggestion._();

  factory Suggestion([void updates(SuggestionBuilder b)]) = _$Suggestion;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(SuggestionBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<Suggestion> get serializer => _$SuggestionSerializer();
}

class _$SuggestionSerializer implements PrimitiveSerializer<Suggestion> {
  @override
  final Iterable<Type> types = const [Suggestion, _$Suggestion];

  @override
  final String wireName = r'Suggestion';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    Suggestion object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.id != null) {
      yield r'id';
      yield serializers.serialize(
        object.id,
        specifiedType: const FullType(String),
      );
    }
    if (object.requestId != null) {
      yield r'request_id';
      yield serializers.serialize(
        object.requestId,
        specifiedType: const FullType(String),
      );
    }
    if (object.vehicleId != null) {
      yield r'vehicle_id';
      yield serializers.serialize(
        object.vehicleId,
        specifiedType: const FullType(String),
      );
    }
    if (object.tripId != null) {
      yield r'trip_id';
      yield serializers.serialize(
        object.tripId,
        specifiedType: const FullType.nullable(String),
      );
    }
    if (object.rank != null) {
      yield r'rank';
      yield serializers.serialize(
        object.rank,
        specifiedType: const FullType(int),
      );
    }
    if (object.cost != null) {
      yield r'cost';
      yield serializers.serialize(
        object.cost,
        specifiedType: const FullType(num),
      );
    }
    if (object.reasons != null) {
      yield r'reasons';
      yield serializers.serialize(
        object.reasons,
        specifiedType: const FullType(BuiltList, [FullType(String)]),
      );
    }
    if (object.status != null) {
      yield r'status';
      yield serializers.serialize(
        object.status,
        specifiedType: const FullType(SuggestionStatusEnum),
      );
    }
    if (object.offeredAt != null) {
      yield r'offered_at';
      yield serializers.serialize(
        object.offeredAt,
        specifiedType: const FullType(DateTime),
      );
    }
    if (object.failsafeDueAt != null) {
      yield r'failsafe_due_at';
      yield serializers.serialize(
        object.failsafeDueAt,
        specifiedType: const FullType(DateTime),
      );
    }
    if (object.escalatedAt != null) {
      yield r'escalated_at';
      yield serializers.serialize(
        object.escalatedAt,
        specifiedType: const FullType.nullable(DateTime),
      );
    }
    if (object.decidedAt != null) {
      yield r'decided_at';
      yield serializers.serialize(
        object.decidedAt,
        specifiedType: const FullType.nullable(DateTime),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    Suggestion object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required SuggestionBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.id = valueDes;
          break;
        case r'request_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.requestId = valueDes;
          break;
        case r'vehicle_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.vehicleId = valueDes;
          break;
        case r'trip_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(String),
          ) as String?;
          if (valueDes == null) continue;
          result.tripId = valueDes;
          break;
        case r'rank':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.rank = valueDes;
          break;
        case r'cost':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(num),
          ) as num;
          result.cost = valueDes;
          break;
        case r'reasons':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(BuiltList, [FullType(String)]),
          ) as BuiltList<String>;
          result.reasons.replace(valueDes);
          break;
        case r'status':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(SuggestionStatusEnum),
          ) as SuggestionStatusEnum;
          result.status = valueDes;
          break;
        case r'offered_at':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(DateTime),
          ) as DateTime;
          result.offeredAt = valueDes;
          break;
        case r'failsafe_due_at':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(DateTime),
          ) as DateTime;
          result.failsafeDueAt = valueDes;
          break;
        case r'escalated_at':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(DateTime),
          ) as DateTime?;
          if (valueDes == null) continue;
          result.escalatedAt = valueDes;
          break;
        case r'decided_at':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(DateTime),
          ) as DateTime?;
          if (valueDes == null) continue;
          result.decidedAt = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  Suggestion deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = SuggestionBuilder();
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

class SuggestionStatusEnum extends EnumClass {

  /// `accepted` means a supervisor approved it. `failsafe_assigned` means nobody answered and the platform assigned it anyway (§4) - a separate state because counting it as an acceptance would let an unwatched scope score 100% on Phase 2's exit criterion. 
  @BuiltValueEnumConst(wireName: r'offered')
  static const SuggestionStatusEnum offered = _$suggestionStatusEnum_offered;
  /// `accepted` means a supervisor approved it. `failsafe_assigned` means nobody answered and the platform assigned it anyway (§4) - a separate state because counting it as an acceptance would let an unwatched scope score 100% on Phase 2's exit criterion. 
  @BuiltValueEnumConst(wireName: r'accepted')
  static const SuggestionStatusEnum accepted = _$suggestionStatusEnum_accepted;
  /// `accepted` means a supervisor approved it. `failsafe_assigned` means nobody answered and the platform assigned it anyway (§4) - a separate state because counting it as an acceptance would let an unwatched scope score 100% on Phase 2's exit criterion. 
  @BuiltValueEnumConst(wireName: r'rejected')
  static const SuggestionStatusEnum rejected = _$suggestionStatusEnum_rejected;
  /// `accepted` means a supervisor approved it. `failsafe_assigned` means nobody answered and the platform assigned it anyway (§4) - a separate state because counting it as an acceptance would let an unwatched scope score 100% on Phase 2's exit criterion. 
  @BuiltValueEnumConst(wireName: r'superseded')
  static const SuggestionStatusEnum superseded = _$suggestionStatusEnum_superseded;
  /// `accepted` means a supervisor approved it. `failsafe_assigned` means nobody answered and the platform assigned it anyway (§4) - a separate state because counting it as an acceptance would let an unwatched scope score 100% on Phase 2's exit criterion. 
  @BuiltValueEnumConst(wireName: r'expired')
  static const SuggestionStatusEnum expired = _$suggestionStatusEnum_expired;
  /// `accepted` means a supervisor approved it. `failsafe_assigned` means nobody answered and the platform assigned it anyway (§4) - a separate state because counting it as an acceptance would let an unwatched scope score 100% on Phase 2's exit criterion. 
  @BuiltValueEnumConst(wireName: r'failsafe_assigned')
  static const SuggestionStatusEnum failsafeAssigned = _$suggestionStatusEnum_failsafeAssigned;

  static Serializer<SuggestionStatusEnum> get serializer => _$suggestionStatusEnumSerializer;

  const SuggestionStatusEnum._(String name): super(name);

  static BuiltSet<SuggestionStatusEnum> get values => _$suggestionStatusEnumValues;
  static SuggestionStatusEnum valueOf(String name) => _$suggestionStatusEnumValueOf(name);
}

