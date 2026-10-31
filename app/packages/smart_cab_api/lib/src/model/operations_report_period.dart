//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:smart_cab_api/src/model/date.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'operations_report_period.g.dart';

/// OperationsReportPeriod
///
/// Properties:
/// * [from] 
/// * [to] 
@BuiltValue()
abstract class OperationsReportPeriod implements Built<OperationsReportPeriod, OperationsReportPeriodBuilder> {
  @BuiltValueField(wireName: r'from')
  Date? get from;

  @BuiltValueField(wireName: r'to')
  Date? get to;

  OperationsReportPeriod._();

  factory OperationsReportPeriod([void updates(OperationsReportPeriodBuilder b)]) = _$OperationsReportPeriod;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(OperationsReportPeriodBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<OperationsReportPeriod> get serializer => _$OperationsReportPeriodSerializer();
}

class _$OperationsReportPeriodSerializer implements PrimitiveSerializer<OperationsReportPeriod> {
  @override
  final Iterable<Type> types = const [OperationsReportPeriod, _$OperationsReportPeriod];

  @override
  final String wireName = r'OperationsReportPeriod';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    OperationsReportPeriod object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.from != null) {
      yield r'from';
      yield serializers.serialize(
        object.from,
        specifiedType: const FullType(Date),
      );
    }
    if (object.to != null) {
      yield r'to';
      yield serializers.serialize(
        object.to,
        specifiedType: const FullType(Date),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    OperationsReportPeriod object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required OperationsReportPeriodBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'from':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(Date),
          ) as Date;
          result.from = valueDes;
          break;
        case r'to':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(Date),
          ) as Date;
          result.to = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  OperationsReportPeriod deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = OperationsReportPeriodBuilder();
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

