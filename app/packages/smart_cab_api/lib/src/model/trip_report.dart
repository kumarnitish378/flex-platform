//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_collection/built_collection.dart';
import 'package:built_value/json_object.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'trip_report.g.dart';

/// TripReport
///
/// Properties:
/// * [trips] 
/// * [requests] 
/// * [medianWaitMinutes] 
/// * [p90WaitMinutes] 
/// * [noShows] 
/// * [cancellations] 
/// * [rows] 
@BuiltValue()
abstract class TripReport implements Built<TripReport, TripReportBuilder> {
  @BuiltValueField(wireName: r'trips')
  int? get trips;

  @BuiltValueField(wireName: r'requests')
  int? get requests;

  @BuiltValueField(wireName: r'median_wait_minutes')
  num? get medianWaitMinutes;

  @BuiltValueField(wireName: r'p90_wait_minutes')
  num? get p90WaitMinutes;

  @BuiltValueField(wireName: r'no_shows')
  int? get noShows;

  @BuiltValueField(wireName: r'cancellations')
  int? get cancellations;

  @BuiltValueField(wireName: r'rows')
  BuiltList<BuiltMap<String, JsonObject?>>? get rows;

  TripReport._();

  factory TripReport([void updates(TripReportBuilder b)]) = _$TripReport;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(TripReportBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<TripReport> get serializer => _$TripReportSerializer();
}

class _$TripReportSerializer implements PrimitiveSerializer<TripReport> {
  @override
  final Iterable<Type> types = const [TripReport, _$TripReport];

  @override
  final String wireName = r'TripReport';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    TripReport object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.trips != null) {
      yield r'trips';
      yield serializers.serialize(
        object.trips,
        specifiedType: const FullType(int),
      );
    }
    if (object.requests != null) {
      yield r'requests';
      yield serializers.serialize(
        object.requests,
        specifiedType: const FullType(int),
      );
    }
    if (object.medianWaitMinutes != null) {
      yield r'median_wait_minutes';
      yield serializers.serialize(
        object.medianWaitMinutes,
        specifiedType: const FullType(num),
      );
    }
    if (object.p90WaitMinutes != null) {
      yield r'p90_wait_minutes';
      yield serializers.serialize(
        object.p90WaitMinutes,
        specifiedType: const FullType(num),
      );
    }
    if (object.noShows != null) {
      yield r'no_shows';
      yield serializers.serialize(
        object.noShows,
        specifiedType: const FullType(int),
      );
    }
    if (object.cancellations != null) {
      yield r'cancellations';
      yield serializers.serialize(
        object.cancellations,
        specifiedType: const FullType(int),
      );
    }
    if (object.rows != null) {
      yield r'rows';
      yield serializers.serialize(
        object.rows,
        specifiedType: const FullType(BuiltList, [FullType(BuiltMap, [FullType(String), FullType.nullable(JsonObject)])]),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    TripReport object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required TripReportBuilder result,
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
        case r'requests':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.requests = valueDes;
          break;
        case r'median_wait_minutes':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(num),
          ) as num;
          result.medianWaitMinutes = valueDes;
          break;
        case r'p90_wait_minutes':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(num),
          ) as num;
          result.p90WaitMinutes = valueDes;
          break;
        case r'no_shows':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.noShows = valueDes;
          break;
        case r'cancellations':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.cancellations = valueDes;
          break;
        case r'rows':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(BuiltList, [FullType(BuiltMap, [FullType(String), FullType.nullable(JsonObject)])]),
          ) as BuiltList<BuiltMap<String, JsonObject?>>;
          result.rows.replace(valueDes);
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  TripReport deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = TripReportBuilder();
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

