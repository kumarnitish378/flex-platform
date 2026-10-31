//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'operations_report_pooling.g.dart';

/// trips completed in the period that carried at least one rider
///
/// Properties:
/// * [trips] 
/// * [ridersCarried] 
/// * [ridersPerTrip] 
/// * [pooledTrips] 
/// * [poolingRate] 
/// * [vehiclesUsed] 
@BuiltValue()
abstract class OperationsReportPooling implements Built<OperationsReportPooling, OperationsReportPoolingBuilder> {
  @BuiltValueField(wireName: r'trips')
  int? get trips;

  @BuiltValueField(wireName: r'riders_carried')
  int? get ridersCarried;

  @BuiltValueField(wireName: r'riders_per_trip')
  num? get ridersPerTrip;

  @BuiltValueField(wireName: r'pooled_trips')
  int? get pooledTrips;

  @BuiltValueField(wireName: r'pooling_rate')
  num? get poolingRate;

  @BuiltValueField(wireName: r'vehicles_used')
  int? get vehiclesUsed;

  OperationsReportPooling._();

  factory OperationsReportPooling([void updates(OperationsReportPoolingBuilder b)]) = _$OperationsReportPooling;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(OperationsReportPoolingBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<OperationsReportPooling> get serializer => _$OperationsReportPoolingSerializer();
}

class _$OperationsReportPoolingSerializer implements PrimitiveSerializer<OperationsReportPooling> {
  @override
  final Iterable<Type> types = const [OperationsReportPooling, _$OperationsReportPooling];

  @override
  final String wireName = r'OperationsReportPooling';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    OperationsReportPooling object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.trips != null) {
      yield r'trips';
      yield serializers.serialize(
        object.trips,
        specifiedType: const FullType(int),
      );
    }
    if (object.ridersCarried != null) {
      yield r'riders_carried';
      yield serializers.serialize(
        object.ridersCarried,
        specifiedType: const FullType(int),
      );
    }
    if (object.ridersPerTrip != null) {
      yield r'riders_per_trip';
      yield serializers.serialize(
        object.ridersPerTrip,
        specifiedType: const FullType.nullable(num),
      );
    }
    if (object.pooledTrips != null) {
      yield r'pooled_trips';
      yield serializers.serialize(
        object.pooledTrips,
        specifiedType: const FullType(int),
      );
    }
    if (object.poolingRate != null) {
      yield r'pooling_rate';
      yield serializers.serialize(
        object.poolingRate,
        specifiedType: const FullType.nullable(num),
      );
    }
    if (object.vehiclesUsed != null) {
      yield r'vehicles_used';
      yield serializers.serialize(
        object.vehiclesUsed,
        specifiedType: const FullType(int),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    OperationsReportPooling object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required OperationsReportPoolingBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'trips':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.trips = valueDes;
          break;
        case r'riders_carried':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.ridersCarried = valueDes;
          break;
        case r'riders_per_trip':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(num),
          ) as num?;
          if (valueDes == null) continue;
          result.ridersPerTrip = valueDes;
          break;
        case r'pooled_trips':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.pooledTrips = valueDes;
          break;
        case r'pooling_rate':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(num),
          ) as num?;
          if (valueDes == null) continue;
          result.poolingRate = valueDes;
          break;
        case r'vehicles_used':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.vehiclesUsed = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  OperationsReportPooling deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = OperationsReportPoolingBuilder();
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

