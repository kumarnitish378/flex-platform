//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_collection/built_collection.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'operations_report_overrides.g.dart';

/// OperationsReportOverrides
///
/// Properties:
/// * [total] 
/// * [hardRuleOverrides] 
/// * [byReason] 
/// * [byAction] 
@BuiltValue()
abstract class OperationsReportOverrides implements Built<OperationsReportOverrides, OperationsReportOverridesBuilder> {
  @BuiltValueField(wireName: r'total')
  int? get total;

  @BuiltValueField(wireName: r'hard_rule_overrides')
  int? get hardRuleOverrides;

  @BuiltValueField(wireName: r'by_reason')
  BuiltMap<String, int>? get byReason;

  @BuiltValueField(wireName: r'by_action')
  BuiltMap<String, int>? get byAction;

  OperationsReportOverrides._();

  factory OperationsReportOverrides([void updates(OperationsReportOverridesBuilder b)]) = _$OperationsReportOverrides;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(OperationsReportOverridesBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<OperationsReportOverrides> get serializer => _$OperationsReportOverridesSerializer();
}

class _$OperationsReportOverridesSerializer implements PrimitiveSerializer<OperationsReportOverrides> {
  @override
  final Iterable<Type> types = const [OperationsReportOverrides, _$OperationsReportOverrides];

  @override
  final String wireName = r'OperationsReportOverrides';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    OperationsReportOverrides object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.total != null) {
      yield r'total';
      yield serializers.serialize(
        object.total,
        specifiedType: const FullType(int),
      );
    }
    if (object.hardRuleOverrides != null) {
      yield r'hard_rule_overrides';
      yield serializers.serialize(
        object.hardRuleOverrides,
        specifiedType: const FullType(int),
      );
    }
    if (object.byReason != null) {
      yield r'by_reason';
      yield serializers.serialize(
        object.byReason,
        specifiedType: const FullType(BuiltMap, [FullType(String), FullType(int)]),
      );
    }
    if (object.byAction != null) {
      yield r'by_action';
      yield serializers.serialize(
        object.byAction,
        specifiedType: const FullType(BuiltMap, [FullType(String), FullType(int)]),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    OperationsReportOverrides object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required OperationsReportOverridesBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'total':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.total = valueDes;
          break;
        case r'hard_rule_overrides':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.hardRuleOverrides = valueDes;
          break;
        case r'by_reason':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(BuiltMap, [FullType(String), FullType(int)]),
          ) as BuiltMap<String, int>;
          result.byReason.replace(valueDes);
          break;
        case r'by_action':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(BuiltMap, [FullType(String), FullType(int)]),
          ) as BuiltMap<String, int>;
          result.byAction.replace(valueDes);
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  OperationsReportOverrides deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = OperationsReportOverridesBuilder();
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

