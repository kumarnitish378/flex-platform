//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_collection/built_collection.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'operations_report_wait.g.dart';

/// asking to getting in, in minutes (the product's one definition of wait)
///
/// Properties:
/// * [measured] 
/// * [medianMinutes] 
/// * [p90Minutes] 
/// * [distribution] - riders per bucket: 0-5, 5-10, 10-15, 15-20, 20-30, 30-45, 45-60, 60+
@BuiltValue()
abstract class OperationsReportWait implements Built<OperationsReportWait, OperationsReportWaitBuilder> {
  @BuiltValueField(wireName: r'measured')
  int? get measured;

  @BuiltValueField(wireName: r'median_minutes')
  num? get medianMinutes;

  @BuiltValueField(wireName: r'p90_minutes')
  num? get p90Minutes;

  /// riders per bucket: 0-5, 5-10, 10-15, 15-20, 20-30, 30-45, 45-60, 60+
  @BuiltValueField(wireName: r'distribution')
  BuiltMap<String, int>? get distribution;

  OperationsReportWait._();

  factory OperationsReportWait([void updates(OperationsReportWaitBuilder b)]) = _$OperationsReportWait;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(OperationsReportWaitBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<OperationsReportWait> get serializer => _$OperationsReportWaitSerializer();
}

class _$OperationsReportWaitSerializer implements PrimitiveSerializer<OperationsReportWait> {
  @override
  final Iterable<Type> types = const [OperationsReportWait, _$OperationsReportWait];

  @override
  final String wireName = r'OperationsReportWait';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    OperationsReportWait object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.measured != null) {
      yield r'measured';
      yield serializers.serialize(
        object.measured,
        specifiedType: const FullType(int),
      );
    }
    if (object.medianMinutes != null) {
      yield r'median_minutes';
      yield serializers.serialize(
        object.medianMinutes,
        specifiedType: const FullType.nullable(num),
      );
    }
    if (object.p90Minutes != null) {
      yield r'p90_minutes';
      yield serializers.serialize(
        object.p90Minutes,
        specifiedType: const FullType.nullable(num),
      );
    }
    if (object.distribution != null) {
      yield r'distribution';
      yield serializers.serialize(
        object.distribution,
        specifiedType: const FullType(BuiltMap, [FullType(String), FullType(int)]),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    OperationsReportWait object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required OperationsReportWaitBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'measured':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.measured = valueDes;
          break;
        case r'median_minutes':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(num),
          ) as num?;
          if (valueDes == null) continue;
          result.medianMinutes = valueDes;
          break;
        case r'p90_minutes':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(num),
          ) as num?;
          if (valueDes == null) continue;
          result.p90Minutes = valueDes;
          break;
        case r'distribution':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(BuiltMap, [FullType(String), FullType(int)]),
          ) as BuiltMap<String, int>;
          result.distribution.replace(valueDes);
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  OperationsReportWait deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = OperationsReportWaitBuilder();
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

