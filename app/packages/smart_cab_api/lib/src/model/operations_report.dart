//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:smart_cab_api/src/model/operations_report_pooling.dart';
import 'package:smart_cab_api/src/model/operations_report_period.dart';
import 'package:smart_cab_api/src/model/operations_report_wait.dart';
import 'package:smart_cab_api/src/model/operations_report_distance.dart';
import 'package:built_collection/built_collection.dart';
import 'package:smart_cab_api/src/model/operations_report_suggestions.dart';
import 'package:smart_cab_api/src/model/operations_report_overrides.dart';
import 'package:smart_cab_api/src/model/operations_report_requests.dart';
import 'package:smart_cab_api/src/model/operations_report_optimizer.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'operations_report.g.dart';

/// OperationsReport
///
/// Properties:
/// * [period] 
/// * [requests] 
/// * [wait] 
/// * [pooling] 
/// * [distance] 
/// * [overrides] 
/// * [suggestions] 
/// * [assignmentsByActor] 
/// * [optimizer] 
@BuiltValue()
abstract class OperationsReport implements Built<OperationsReport, OperationsReportBuilder> {
  @BuiltValueField(wireName: r'period')
  OperationsReportPeriod get period;

  @BuiltValueField(wireName: r'requests')
  OperationsReportRequests get requests;

  @BuiltValueField(wireName: r'wait')
  OperationsReportWait get wait;

  @BuiltValueField(wireName: r'pooling')
  OperationsReportPooling get pooling;

  @BuiltValueField(wireName: r'distance')
  OperationsReportDistance get distance;

  @BuiltValueField(wireName: r'overrides')
  OperationsReportOverrides get overrides;

  @BuiltValueField(wireName: r'suggestions')
  OperationsReportSuggestions get suggestions;

  @BuiltValueField(wireName: r'assignments_by_actor')
  BuiltMap<String, int> get assignmentsByActor;

  @BuiltValueField(wireName: r'optimizer')
  OperationsReportOptimizer get optimizer;

  OperationsReport._();

  factory OperationsReport([void updates(OperationsReportBuilder b)]) = _$OperationsReport;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(OperationsReportBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<OperationsReport> get serializer => _$OperationsReportSerializer();
}

class _$OperationsReportSerializer implements PrimitiveSerializer<OperationsReport> {
  @override
  final Iterable<Type> types = const [OperationsReport, _$OperationsReport];

  @override
  final String wireName = r'OperationsReport';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    OperationsReport object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    yield r'period';
    yield serializers.serialize(
      object.period,
      specifiedType: const FullType(OperationsReportPeriod),
    );
    yield r'requests';
    yield serializers.serialize(
      object.requests,
      specifiedType: const FullType(OperationsReportRequests),
    );
    yield r'wait';
    yield serializers.serialize(
      object.wait,
      specifiedType: const FullType(OperationsReportWait),
    );
    yield r'pooling';
    yield serializers.serialize(
      object.pooling,
      specifiedType: const FullType(OperationsReportPooling),
    );
    yield r'distance';
    yield serializers.serialize(
      object.distance,
      specifiedType: const FullType(OperationsReportDistance),
    );
    yield r'overrides';
    yield serializers.serialize(
      object.overrides,
      specifiedType: const FullType(OperationsReportOverrides),
    );
    yield r'suggestions';
    yield serializers.serialize(
      object.suggestions,
      specifiedType: const FullType(OperationsReportSuggestions),
    );
    yield r'assignments_by_actor';
    yield serializers.serialize(
      object.assignmentsByActor,
      specifiedType: const FullType(BuiltMap, [FullType(String), FullType(int)]),
    );
    yield r'optimizer';
    yield serializers.serialize(
      object.optimizer,
      specifiedType: const FullType(OperationsReportOptimizer),
    );
  }

  @override
  Object serialize(
    Serializers serializers,
    OperationsReport object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required OperationsReportBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'period':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(OperationsReportPeriod),
          ) as OperationsReportPeriod;
          result.period.replace(valueDes);
          break;
        case r'requests':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(OperationsReportRequests),
          ) as OperationsReportRequests;
          result.requests.replace(valueDes);
          break;
        case r'wait':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(OperationsReportWait),
          ) as OperationsReportWait;
          result.wait.replace(valueDes);
          break;
        case r'pooling':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(OperationsReportPooling),
          ) as OperationsReportPooling;
          result.pooling.replace(valueDes);
          break;
        case r'distance':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(OperationsReportDistance),
          ) as OperationsReportDistance;
          result.distance.replace(valueDes);
          break;
        case r'overrides':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(OperationsReportOverrides),
          ) as OperationsReportOverrides;
          result.overrides.replace(valueDes);
          break;
        case r'suggestions':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(OperationsReportSuggestions),
          ) as OperationsReportSuggestions;
          result.suggestions.replace(valueDes);
          break;
        case r'assignments_by_actor':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(BuiltMap, [FullType(String), FullType(int)]),
          ) as BuiltMap<String, int>;
          result.assignmentsByActor.replace(valueDes);
          break;
        case r'optimizer':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(OperationsReportOptimizer),
          ) as OperationsReportOptimizer;
          result.optimizer.replace(valueDes);
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  OperationsReport deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = OperationsReportBuilder();
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

