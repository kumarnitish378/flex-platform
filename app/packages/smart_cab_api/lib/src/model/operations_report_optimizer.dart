//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'operations_report_optimizer.g.dart';

/// OperationsReportOptimizer
///
/// Properties:
/// * [runs] 
/// * [failed] 
/// * [applied] 
/// * [suggested] 
/// * [hinted] 
@BuiltValue()
abstract class OperationsReportOptimizer implements Built<OperationsReportOptimizer, OperationsReportOptimizerBuilder> {
  @BuiltValueField(wireName: r'runs')
  int? get runs;

  @BuiltValueField(wireName: r'failed')
  int? get failed;

  @BuiltValueField(wireName: r'applied')
  int? get applied;

  @BuiltValueField(wireName: r'suggested')
  int? get suggested;

  @BuiltValueField(wireName: r'hinted')
  int? get hinted;

  OperationsReportOptimizer._();

  factory OperationsReportOptimizer([void updates(OperationsReportOptimizerBuilder b)]) = _$OperationsReportOptimizer;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(OperationsReportOptimizerBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<OperationsReportOptimizer> get serializer => _$OperationsReportOptimizerSerializer();
}

class _$OperationsReportOptimizerSerializer implements PrimitiveSerializer<OperationsReportOptimizer> {
  @override
  final Iterable<Type> types = const [OperationsReportOptimizer, _$OperationsReportOptimizer];

  @override
  final String wireName = r'OperationsReportOptimizer';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    OperationsReportOptimizer object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.runs != null) {
      yield r'runs';
      yield serializers.serialize(
        object.runs,
        specifiedType: const FullType(int),
      );
    }
    if (object.failed != null) {
      yield r'failed';
      yield serializers.serialize(
        object.failed,
        specifiedType: const FullType(int),
      );
    }
    if (object.applied != null) {
      yield r'applied';
      yield serializers.serialize(
        object.applied,
        specifiedType: const FullType(int),
      );
    }
    if (object.suggested != null) {
      yield r'suggested';
      yield serializers.serialize(
        object.suggested,
        specifiedType: const FullType(int),
      );
    }
    if (object.hinted != null) {
      yield r'hinted';
      yield serializers.serialize(
        object.hinted,
        specifiedType: const FullType(int),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    OperationsReportOptimizer object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required OperationsReportOptimizerBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'runs':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.runs = valueDes;
          break;
        case r'failed':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.failed = valueDes;
          break;
        case r'applied':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.applied = valueDes;
          break;
        case r'suggested':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.suggested = valueDes;
          break;
        case r'hinted':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.hinted = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  OperationsReportOptimizer deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = OperationsReportOptimizerBuilder();
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

