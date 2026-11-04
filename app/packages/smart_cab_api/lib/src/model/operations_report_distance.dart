//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'operations_report_distance.g.dart';

/// from the cabs' pings; trips with no measurement are left out, not zeroed
///
/// Properties:
/// * [tripsMeasured] 
/// * [cabKmTotal] 
/// * [cabKmPerTrip] 
/// * [cabKmPerRider] 
@BuiltValue()
abstract class OperationsReportDistance implements Built<OperationsReportDistance, OperationsReportDistanceBuilder> {
  @BuiltValueField(wireName: r'trips_measured')
  int? get tripsMeasured;

  @BuiltValueField(wireName: r'cab_km_total')
  num? get cabKmTotal;

  @BuiltValueField(wireName: r'cab_km_per_trip')
  num? get cabKmPerTrip;

  @BuiltValueField(wireName: r'cab_km_per_rider')
  num? get cabKmPerRider;

  OperationsReportDistance._();

  factory OperationsReportDistance([void updates(OperationsReportDistanceBuilder b)]) = _$OperationsReportDistance;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(OperationsReportDistanceBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<OperationsReportDistance> get serializer => _$OperationsReportDistanceSerializer();
}

class _$OperationsReportDistanceSerializer implements PrimitiveSerializer<OperationsReportDistance> {
  @override
  final Iterable<Type> types = const [OperationsReportDistance, _$OperationsReportDistance];

  @override
  final String wireName = r'OperationsReportDistance';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    OperationsReportDistance object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.tripsMeasured != null) {
      yield r'trips_measured';
      yield serializers.serialize(
        object.tripsMeasured,
        specifiedType: const FullType(int),
      );
    }
    if (object.cabKmTotal != null) {
      yield r'cab_km_total';
      yield serializers.serialize(
        object.cabKmTotal,
        specifiedType: const FullType.nullable(num),
      );
    }
    if (object.cabKmPerTrip != null) {
      yield r'cab_km_per_trip';
      yield serializers.serialize(
        object.cabKmPerTrip,
        specifiedType: const FullType.nullable(num),
      );
    }
    if (object.cabKmPerRider != null) {
      yield r'cab_km_per_rider';
      yield serializers.serialize(
        object.cabKmPerRider,
        specifiedType: const FullType.nullable(num),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    OperationsReportDistance object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required OperationsReportDistanceBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'trips_measured':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.tripsMeasured = valueDes;
          break;
        case r'cab_km_total':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(num),
          ) as num?;
          if (valueDes == null) continue;
          result.cabKmTotal = valueDes;
          break;
        case r'cab_km_per_trip':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(num),
          ) as num?;
          if (valueDes == null) continue;
          result.cabKmPerTrip = valueDes;
          break;
        case r'cab_km_per_rider':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(num),
          ) as num?;
          if (valueDes == null) continue;
          result.cabKmPerRider = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  OperationsReportDistance deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = OperationsReportDistanceBuilder();
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

