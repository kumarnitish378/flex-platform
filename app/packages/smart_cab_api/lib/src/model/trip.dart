//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:smart_cab_api/src/model/trip_stop.dart';
import 'package:built_collection/built_collection.dart';
import 'package:smart_cab_api/src/model/trip_status.dart';
import 'package:smart_cab_api/src/model/direction.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'trip.g.dart';

/// Trip
///
/// Properties:
/// * [id] 
/// * [vehicleId] 
/// * [driverId] 
/// * [direction] 
/// * [status] 
/// * [poolingBlocked] 
/// * [modeUsed] 
/// * [stops] 
@BuiltValue()
abstract class Trip implements Built<Trip, TripBuilder> {
  @BuiltValueField(wireName: r'id')
  String? get id;

  @BuiltValueField(wireName: r'vehicle_id')
  String? get vehicleId;

  @BuiltValueField(wireName: r'driver_id')
  String? get driverId;

  @BuiltValueField(wireName: r'direction')
  Direction? get direction;
  // enum directionEnum {  to_office,  from_office,  };

  @BuiltValueField(wireName: r'status')
  TripStatus? get status;
  // enum statusEnum {  planned,  dispatched,  in_progress,  completed,  cancelled,  aborted,  };

  @BuiltValueField(wireName: r'pooling_blocked')
  bool? get poolingBlocked;

  @BuiltValueField(wireName: r'mode_used')
  TripModeUsedEnum? get modeUsed;
  // enum modeUsedEnum {  manual,  semi_auto,  full_auto,  failsafe,  };

  @BuiltValueField(wireName: r'stops')
  BuiltList<TripStop>? get stops;

  Trip._();

  factory Trip([void updates(TripBuilder b)]) = _$Trip;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(TripBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<Trip> get serializer => _$TripSerializer();
}

class _$TripSerializer implements PrimitiveSerializer<Trip> {
  @override
  final Iterable<Type> types = const [Trip, _$Trip];

  @override
  final String wireName = r'Trip';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    Trip object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.id != null) {
      yield r'id';
      yield serializers.serialize(
        object.id,
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
    if (object.driverId != null) {
      yield r'driver_id';
      yield serializers.serialize(
        object.driverId,
        specifiedType: const FullType(String),
      );
    }
    if (object.direction != null) {
      yield r'direction';
      yield serializers.serialize(
        object.direction,
        specifiedType: const FullType(Direction),
      );
    }
    if (object.status != null) {
      yield r'status';
      yield serializers.serialize(
        object.status,
        specifiedType: const FullType(TripStatus),
      );
    }
    if (object.poolingBlocked != null) {
      yield r'pooling_blocked';
      yield serializers.serialize(
        object.poolingBlocked,
        specifiedType: const FullType(bool),
      );
    }
    if (object.modeUsed != null) {
      yield r'mode_used';
      yield serializers.serialize(
        object.modeUsed,
        specifiedType: const FullType(TripModeUsedEnum),
      );
    }
    if (object.stops != null) {
      yield r'stops';
      yield serializers.serialize(
        object.stops,
        specifiedType: const FullType(BuiltList, [FullType(TripStop)]),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    Trip object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required TripBuilder result,
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
        case r'vehicle_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.vehicleId = valueDes;
          break;
        case r'driver_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.driverId = valueDes;
          break;
        case r'direction':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(Direction),
          ) as Direction;
          result.direction = valueDes;
          break;
        case r'status':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(TripStatus),
          ) as TripStatus;
          result.status = valueDes;
          break;
        case r'pooling_blocked':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(bool),
          ) as bool;
          result.poolingBlocked = valueDes;
          break;
        case r'mode_used':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(TripModeUsedEnum),
          ) as TripModeUsedEnum;
          result.modeUsed = valueDes;
          break;
        case r'stops':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(BuiltList, [FullType(TripStop)]),
          ) as BuiltList<TripStop>;
          result.stops.replace(valueDes);
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  Trip deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = TripBuilder();
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

class TripModeUsedEnum extends EnumClass {

  @BuiltValueEnumConst(wireName: r'manual')
  static const TripModeUsedEnum manual = _$tripModeUsedEnum_manual;
  @BuiltValueEnumConst(wireName: r'semi_auto')
  static const TripModeUsedEnum semiAuto = _$tripModeUsedEnum_semiAuto;
  @BuiltValueEnumConst(wireName: r'full_auto')
  static const TripModeUsedEnum fullAuto = _$tripModeUsedEnum_fullAuto;
  @BuiltValueEnumConst(wireName: r'failsafe')
  static const TripModeUsedEnum failsafe = _$tripModeUsedEnum_failsafe;

  static Serializer<TripModeUsedEnum> get serializer => _$tripModeUsedEnumSerializer;

  const TripModeUsedEnum._(String name): super(name);

  static BuiltSet<TripModeUsedEnum> get values => _$tripModeUsedEnumValues;
  static TripModeUsedEnum valueOf(String name) => _$tripModeUsedEnumValueOf(name);
}

