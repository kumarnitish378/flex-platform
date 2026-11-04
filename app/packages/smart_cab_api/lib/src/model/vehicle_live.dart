//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:smart_cab_api/src/model/vehicle.dart';
import 'package:smart_cab_api/src/model/lat_lng.dart';
import 'package:smart_cab_api/src/model/vehicle_type.dart';
import 'package:smart_cab_api/src/model/tracker_type.dart';
import 'package:smart_cab_api/src/model/vehicle_status.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'vehicle_live.g.dart';

/// VehicleLive
///
/// Properties:
/// * [registrationNo] 
/// * [model] 
/// * [vehicleType] 
/// * [seatCapacity] 
/// * [trackerType] 
/// * [id] 
/// * [status] 
/// * [currentDriverId] 
/// * [position] 
/// * [positionAt] 
/// * [stale] 
/// * [activeTripId] 
/// * [seatsFree] 
@BuiltValue()
abstract class VehicleLive implements Vehicle, Built<VehicleLive, VehicleLiveBuilder> {
  @BuiltValueField(wireName: r'stale')
  bool? get stale;

  @BuiltValueField(wireName: r'seats_free')
  int? get seatsFree;

  @BuiltValueField(wireName: r'position')
  LatLng? get position;

  @BuiltValueField(wireName: r'position_at')
  DateTime? get positionAt;

  @BuiltValueField(wireName: r'active_trip_id')
  String? get activeTripId;

  VehicleLive._();

  factory VehicleLive([void updates(VehicleLiveBuilder b)]) = _$VehicleLive;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(VehicleLiveBuilder b) => b
      ..trackerType = TrackerType.app;

  @BuiltValueSerializer(custom: true)
  static Serializer<VehicleLive> get serializer => _$VehicleLiveSerializer();
}

class _$VehicleLiveSerializer implements PrimitiveSerializer<VehicleLive> {
  @override
  final Iterable<Type> types = const [VehicleLive, _$VehicleLive];

  @override
  final String wireName = r'VehicleLive';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    VehicleLive object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.seatsFree != null) {
      yield r'seats_free';
      yield serializers.serialize(
        object.seatsFree,
        specifiedType: const FullType(int),
      );
    }
    if (object.trackerType != null) {
      yield r'tracker_type';
      yield serializers.serialize(
        object.trackerType,
        specifiedType: const FullType(TrackerType),
      );
    }
    if (object.positionAt != null) {
      yield r'position_at';
      yield serializers.serialize(
        object.positionAt,
        specifiedType: const FullType.nullable(DateTime),
      );
    }
    if (object.activeTripId != null) {
      yield r'active_trip_id';
      yield serializers.serialize(
        object.activeTripId,
        specifiedType: const FullType.nullable(String),
      );
    }
    yield r'seat_capacity';
    yield serializers.serialize(
      object.seatCapacity,
      specifiedType: const FullType(int),
    );
    if (object.stale != null) {
      yield r'stale';
      yield serializers.serialize(
        object.stale,
        specifiedType: const FullType(bool),
      );
    }
    if (object.currentDriverId != null) {
      yield r'current_driver_id';
      yield serializers.serialize(
        object.currentDriverId,
        specifiedType: const FullType.nullable(String),
      );
    }
    yield r'registration_no';
    yield serializers.serialize(
      object.registrationNo,
      specifiedType: const FullType(String),
    );
    if (object.model != null) {
      yield r'model';
      yield serializers.serialize(
        object.model,
        specifiedType: const FullType(String),
      );
    }
    if (object.position != null) {
      yield r'position';
      yield serializers.serialize(
        object.position,
        specifiedType: const FullType.nullable(LatLng),
      );
    }
    if (object.id != null) {
      yield r'id';
      yield serializers.serialize(
        object.id,
        specifiedType: const FullType(String),
      );
    }
    yield r'vehicle_type';
    yield serializers.serialize(
      object.vehicleType,
      specifiedType: const FullType(VehicleType),
    );
    if (object.status != null) {
      yield r'status';
      yield serializers.serialize(
        object.status,
        specifiedType: const FullType(VehicleStatus),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    VehicleLive object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required VehicleLiveBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'seats_free':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.seatsFree = valueDes;
          break;
        case r'tracker_type':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(TrackerType),
          ) as TrackerType;
          result.trackerType = valueDes;
          break;
        case r'position_at':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(DateTime),
          ) as DateTime?;
          if (valueDes == null) continue;
          result.positionAt = valueDes;
          break;
        case r'active_trip_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(String),
          ) as String?;
          if (valueDes == null) continue;
          result.activeTripId = valueDes;
          break;
        case r'seat_capacity':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.seatCapacity = valueDes;
          break;
        case r'stale':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(bool),
          ) as bool;
          result.stale = valueDes;
          break;
        case r'current_driver_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(String),
          ) as String?;
          if (valueDes == null) continue;
          result.currentDriverId = valueDes;
          break;
        case r'registration_no':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.registrationNo = valueDes;
          break;
        case r'model':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.model = valueDes;
          break;
        case r'position':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(LatLng),
          ) as LatLng?;
          if (valueDes == null) continue;
          result.position.replace(valueDes);
          break;
        case r'id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.id = valueDes;
          break;
        case r'vehicle_type':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(VehicleType),
          ) as VehicleType;
          result.vehicleType = valueDes;
          break;
        case r'status':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(VehicleStatus),
          ) as VehicleStatus;
          result.status = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  VehicleLive deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = VehicleLiveBuilder();
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

