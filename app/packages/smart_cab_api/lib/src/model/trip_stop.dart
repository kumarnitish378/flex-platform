//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_collection/built_collection.dart';
import 'package:smart_cab_api/src/model/lat_lng.dart';
import 'package:smart_cab_api/src/model/stop_status.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'trip_stop.g.dart';

/// TripStop
///
/// Properties:
/// * [id] 
/// * [sequence] 
/// * [stopType] 
/// * [requestId] 
/// * [riderFirstName] 
/// * [riderPhone] - only for assigned driver during active trip
/// * [location] 
/// * [landmark] 
/// * [status] 
/// * [plannedEta] 
/// * [latestEta] 
/// * [etaApproximate] - true when the ETA came from the approx provider rather than road routing (OSRM down, slow, or the shared public-server rate limit was exhausted). Clients must show such ETAs as approximate. See ADR-0010. 
/// * [arrivedAt] 
/// * [doneAt] 
@BuiltValue()
abstract class TripStop implements Built<TripStop, TripStopBuilder> {
  @BuiltValueField(wireName: r'id')
  String? get id;

  @BuiltValueField(wireName: r'sequence')
  int? get sequence;

  @BuiltValueField(wireName: r'stop_type')
  TripStopStopTypeEnum? get stopType;
  // enum stopTypeEnum {  pickup,  drop,  };

  @BuiltValueField(wireName: r'request_id')
  String? get requestId;

  @BuiltValueField(wireName: r'rider_first_name')
  String? get riderFirstName;

  /// only for assigned driver during active trip
  @BuiltValueField(wireName: r'rider_phone')
  String? get riderPhone;

  @BuiltValueField(wireName: r'location')
  LatLng? get location;

  @BuiltValueField(wireName: r'landmark')
  String? get landmark;

  @BuiltValueField(wireName: r'status')
  StopStatus? get status;
  // enum statusEnum {  pending,  en_route,  arrived,  done,  skipped,  };

  @BuiltValueField(wireName: r'planned_eta')
  DateTime? get plannedEta;

  @BuiltValueField(wireName: r'latest_eta')
  DateTime? get latestEta;

  /// true when the ETA came from the approx provider rather than road routing (OSRM down, slow, or the shared public-server rate limit was exhausted). Clients must show such ETAs as approximate. See ADR-0010. 
  @BuiltValueField(wireName: r'eta_approximate')
  bool? get etaApproximate;

  @BuiltValueField(wireName: r'arrived_at')
  DateTime? get arrivedAt;

  @BuiltValueField(wireName: r'done_at')
  DateTime? get doneAt;

  TripStop._();

  factory TripStop([void updates(TripStopBuilder b)]) = _$TripStop;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(TripStopBuilder b) => b
      ..etaApproximate = false;

  @BuiltValueSerializer(custom: true)
  static Serializer<TripStop> get serializer => _$TripStopSerializer();
}

class _$TripStopSerializer implements PrimitiveSerializer<TripStop> {
  @override
  final Iterable<Type> types = const [TripStop, _$TripStop];

  @override
  final String wireName = r'TripStop';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    TripStop object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.id != null) {
      yield r'id';
      yield serializers.serialize(
        object.id,
        specifiedType: const FullType(String),
      );
    }
    if (object.sequence != null) {
      yield r'sequence';
      yield serializers.serialize(
        object.sequence,
        specifiedType: const FullType(int),
      );
    }
    if (object.stopType != null) {
      yield r'stop_type';
      yield serializers.serialize(
        object.stopType,
        specifiedType: const FullType(TripStopStopTypeEnum),
      );
    }
    if (object.requestId != null) {
      yield r'request_id';
      yield serializers.serialize(
        object.requestId,
        specifiedType: const FullType(String),
      );
    }
    if (object.riderFirstName != null) {
      yield r'rider_first_name';
      yield serializers.serialize(
        object.riderFirstName,
        specifiedType: const FullType(String),
      );
    }
    if (object.riderPhone != null) {
      yield r'rider_phone';
      yield serializers.serialize(
        object.riderPhone,
        specifiedType: const FullType.nullable(String),
      );
    }
    if (object.location != null) {
      yield r'location';
      yield serializers.serialize(
        object.location,
        specifiedType: const FullType(LatLng),
      );
    }
    if (object.landmark != null) {
      yield r'landmark';
      yield serializers.serialize(
        object.landmark,
        specifiedType: const FullType.nullable(String),
      );
    }
    if (object.status != null) {
      yield r'status';
      yield serializers.serialize(
        object.status,
        specifiedType: const FullType(StopStatus),
      );
    }
    if (object.plannedEta != null) {
      yield r'planned_eta';
      yield serializers.serialize(
        object.plannedEta,
        specifiedType: const FullType(DateTime),
      );
    }
    if (object.latestEta != null) {
      yield r'latest_eta';
      yield serializers.serialize(
        object.latestEta,
        specifiedType: const FullType(DateTime),
      );
    }
    if (object.etaApproximate != null) {
      yield r'eta_approximate';
      yield serializers.serialize(
        object.etaApproximate,
        specifiedType: const FullType(bool),
      );
    }
    if (object.arrivedAt != null) {
      yield r'arrived_at';
      yield serializers.serialize(
        object.arrivedAt,
        specifiedType: const FullType.nullable(DateTime),
      );
    }
    if (object.doneAt != null) {
      yield r'done_at';
      yield serializers.serialize(
        object.doneAt,
        specifiedType: const FullType.nullable(DateTime),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    TripStop object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required TripStopBuilder result,
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
        case r'sequence':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.sequence = valueDes;
          break;
        case r'stop_type':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(TripStopStopTypeEnum),
          ) as TripStopStopTypeEnum;
          result.stopType = valueDes;
          break;
        case r'request_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.requestId = valueDes;
          break;
        case r'rider_first_name':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.riderFirstName = valueDes;
          break;
        case r'rider_phone':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(String),
          ) as String?;
          if (valueDes == null) continue;
          result.riderPhone = valueDes;
          break;
        case r'location':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(LatLng),
          ) as LatLng;
          result.location.replace(valueDes);
          break;
        case r'landmark':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(String),
          ) as String?;
          if (valueDes == null) continue;
          result.landmark = valueDes;
          break;
        case r'status':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(StopStatus),
          ) as StopStatus;
          result.status = valueDes;
          break;
        case r'planned_eta':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(DateTime),
          ) as DateTime;
          result.plannedEta = valueDes;
          break;
        case r'latest_eta':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(DateTime),
          ) as DateTime;
          result.latestEta = valueDes;
          break;
        case r'eta_approximate':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(bool),
          ) as bool;
          result.etaApproximate = valueDes;
          break;
        case r'arrived_at':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(DateTime),
          ) as DateTime?;
          if (valueDes == null) continue;
          result.arrivedAt = valueDes;
          break;
        case r'done_at':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(DateTime),
          ) as DateTime?;
          if (valueDes == null) continue;
          result.doneAt = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  TripStop deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = TripStopBuilder();
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

class TripStopStopTypeEnum extends EnumClass {

  @BuiltValueEnumConst(wireName: r'pickup')
  static const TripStopStopTypeEnum pickup = _$tripStopStopTypeEnum_pickup;
  @BuiltValueEnumConst(wireName: r'drop')
  static const TripStopStopTypeEnum drop = _$tripStopStopTypeEnum_drop;

  static Serializer<TripStopStopTypeEnum> get serializer => _$tripStopStopTypeEnumSerializer;

  const TripStopStopTypeEnum._(String name): super(name);

  static BuiltSet<TripStopStopTypeEnum> get values => _$tripStopStopTypeEnumValues;
  static TripStopStopTypeEnum valueOf(String name) => _$tripStopStopTypeEnumValueOf(name);
}

