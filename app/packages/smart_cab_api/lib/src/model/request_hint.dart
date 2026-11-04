//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_collection/built_collection.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'request_hint.g.dart';

/// What the optimizer would do with a queued request in a `manual` scope (`allocation-rules.md` §6: in `manual` the proposed trips \"are shown as hints only\"). Nothing has been assigned and nothing will be: acting on it is the supervisor's call, through `/dispatch/assign`. 
///
/// Properties:
/// * [requestId] 
/// * [vehicleId] 
/// * [tripId] - the trip it would join, or null if it would open a new one
/// * [riderOrder] - every request on the resulting trip, in stop order
/// * [pickupEtaMinutes] 
/// * [cost] - the plan's cost for this trip
/// * [reasons] 
/// * [createdAt] 
@BuiltValue()
abstract class RequestHint implements Built<RequestHint, RequestHintBuilder> {
  @BuiltValueField(wireName: r'request_id')
  String? get requestId;

  @BuiltValueField(wireName: r'vehicle_id')
  String? get vehicleId;

  /// the trip it would join, or null if it would open a new one
  @BuiltValueField(wireName: r'trip_id')
  String? get tripId;

  /// every request on the resulting trip, in stop order
  @BuiltValueField(wireName: r'rider_order')
  BuiltList<String>? get riderOrder;

  @BuiltValueField(wireName: r'pickup_eta_minutes')
  num? get pickupEtaMinutes;

  /// the plan's cost for this trip
  @BuiltValueField(wireName: r'cost')
  num? get cost;

  @BuiltValueField(wireName: r'reasons')
  BuiltList<String>? get reasons;

  @BuiltValueField(wireName: r'created_at')
  DateTime? get createdAt;

  RequestHint._();

  factory RequestHint([void updates(RequestHintBuilder b)]) = _$RequestHint;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(RequestHintBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<RequestHint> get serializer => _$RequestHintSerializer();
}

class _$RequestHintSerializer implements PrimitiveSerializer<RequestHint> {
  @override
  final Iterable<Type> types = const [RequestHint, _$RequestHint];

  @override
  final String wireName = r'RequestHint';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    RequestHint object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
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
    if (object.riderOrder != null) {
      yield r'rider_order';
      yield serializers.serialize(
        object.riderOrder,
        specifiedType: const FullType(BuiltList, [FullType(String)]),
      );
    }
    if (object.pickupEtaMinutes != null) {
      yield r'pickup_eta_minutes';
      yield serializers.serialize(
        object.pickupEtaMinutes,
        specifiedType: const FullType(num),
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
    if (object.createdAt != null) {
      yield r'created_at';
      yield serializers.serialize(
        object.createdAt,
        specifiedType: const FullType(DateTime),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    RequestHint object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required RequestHintBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
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
        case r'rider_order':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(BuiltList, [FullType(String)]),
          ) as BuiltList<String>;
          result.riderOrder.replace(valueDes);
          break;
        case r'pickup_eta_minutes':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(num),
          ) as num;
          result.pickupEtaMinutes = valueDes;
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
        case r'created_at':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(DateTime),
          ) as DateTime;
          result.createdAt = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  RequestHint deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = RequestHintBuilder();
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

