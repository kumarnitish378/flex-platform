//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:smart_cab_api/src/model/urgency.dart';
import 'package:smart_cab_api/src/model/ride_request_assignment.dart';
import 'package:smart_cab_api/src/model/lat_lng.dart';
import 'package:smart_cab_api/src/model/direction.dart';
import 'package:smart_cab_api/src/model/request_status.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'ride_request.g.dart';

/// RideRequest
///
/// Properties:
/// * [id] 
/// * [employeeId] 
/// * [employeeName] 
/// * [clientId] 
/// * [direction] 
/// * [officeId] 
/// * [location] 
/// * [pickupLocation] 
/// * [landmark] 
/// * [requestedTime] 
/// * [urgency] 
/// * [noSharing] 
/// * [status] 
/// * [waitingSince] 
/// * [tripId] 
/// * [assignment] 
/// * [locked] 
/// * [escalatedAt] - Set when nobody had served this request by `retry_after_minutes` after the cab was due (ADR-0019). The board shows such a request as late. `urgency` stays whatever the rider asked for - it is never rewritten by the platform (ADR-0021), so this is the field that says \"we are failing this one\". 
/// * [cancelReason] 
@BuiltValue()
abstract class RideRequest implements Built<RideRequest, RideRequestBuilder> {
  @BuiltValueField(wireName: r'id')
  String? get id;

  @BuiltValueField(wireName: r'employee_id')
  String? get employeeId;

  @BuiltValueField(wireName: r'employee_name')
  String? get employeeName;

  @BuiltValueField(wireName: r'client_id')
  String? get clientId;

  @BuiltValueField(wireName: r'direction')
  Direction? get direction;
  // enum directionEnum {  to_office,  from_office,  };

  @BuiltValueField(wireName: r'office_id')
  String? get officeId;

  @BuiltValueField(wireName: r'location')
  LatLng? get location;

  @BuiltValueField(wireName: r'pickup_location')
  LatLng? get pickupLocation;

  @BuiltValueField(wireName: r'landmark')
  String? get landmark;

  @BuiltValueField(wireName: r'requested_time')
  DateTime? get requestedTime;

  @BuiltValueField(wireName: r'urgency')
  Urgency? get urgency;
  // enum urgencyEnum {  high,  medium,  low,  };

  @BuiltValueField(wireName: r'no_sharing')
  bool? get noSharing;

  @BuiltValueField(wireName: r'status')
  RequestStatus? get status;
  // enum statusEnum {  requested,  queued,  suggested,  assigned,  picked_up,  dropped,  no_show,  cancelled,  expired,  };

  @BuiltValueField(wireName: r'waiting_since')
  DateTime? get waitingSince;

  @BuiltValueField(wireName: r'trip_id')
  String? get tripId;

  @BuiltValueField(wireName: r'assignment')
  RideRequestAssignment? get assignment;

  @BuiltValueField(wireName: r'locked')
  bool? get locked;

  /// Set when nobody had served this request by `retry_after_minutes` after the cab was due (ADR-0019). The board shows such a request as late. `urgency` stays whatever the rider asked for - it is never rewritten by the platform (ADR-0021), so this is the field that says \"we are failing this one\". 
  @BuiltValueField(wireName: r'escalated_at')
  DateTime? get escalatedAt;

  @BuiltValueField(wireName: r'cancel_reason')
  String? get cancelReason;

  RideRequest._();

  factory RideRequest([void updates(RideRequestBuilder b)]) = _$RideRequest;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(RideRequestBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<RideRequest> get serializer => _$RideRequestSerializer();
}

class _$RideRequestSerializer implements PrimitiveSerializer<RideRequest> {
  @override
  final Iterable<Type> types = const [RideRequest, _$RideRequest];

  @override
  final String wireName = r'RideRequest';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    RideRequest object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.id != null) {
      yield r'id';
      yield serializers.serialize(
        object.id,
        specifiedType: const FullType(String),
      );
    }
    if (object.employeeId != null) {
      yield r'employee_id';
      yield serializers.serialize(
        object.employeeId,
        specifiedType: const FullType(String),
      );
    }
    if (object.employeeName != null) {
      yield r'employee_name';
      yield serializers.serialize(
        object.employeeName,
        specifiedType: const FullType(String),
      );
    }
    if (object.clientId != null) {
      yield r'client_id';
      yield serializers.serialize(
        object.clientId,
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
    if (object.officeId != null) {
      yield r'office_id';
      yield serializers.serialize(
        object.officeId,
        specifiedType: const FullType(String),
      );
    }
    if (object.location != null) {
      yield r'location';
      yield serializers.serialize(
        object.location,
        specifiedType: const FullType(LatLng),
      );
    }
    if (object.pickupLocation != null) {
      yield r'pickup_location';
      yield serializers.serialize(
        object.pickupLocation,
        specifiedType: const FullType.nullable(LatLng),
      );
    }
    if (object.landmark != null) {
      yield r'landmark';
      yield serializers.serialize(
        object.landmark,
        specifiedType: const FullType.nullable(String),
      );
    }
    if (object.requestedTime != null) {
      yield r'requested_time';
      yield serializers.serialize(
        object.requestedTime,
        specifiedType: const FullType(DateTime),
      );
    }
    if (object.urgency != null) {
      yield r'urgency';
      yield serializers.serialize(
        object.urgency,
        specifiedType: const FullType(Urgency),
      );
    }
    if (object.noSharing != null) {
      yield r'no_sharing';
      yield serializers.serialize(
        object.noSharing,
        specifiedType: const FullType(bool),
      );
    }
    if (object.status != null) {
      yield r'status';
      yield serializers.serialize(
        object.status,
        specifiedType: const FullType(RequestStatus),
      );
    }
    if (object.waitingSince != null) {
      yield r'waiting_since';
      yield serializers.serialize(
        object.waitingSince,
        specifiedType: const FullType(DateTime),
      );
    }
    if (object.tripId != null) {
      yield r'trip_id';
      yield serializers.serialize(
        object.tripId,
        specifiedType: const FullType.nullable(String),
      );
    }
    if (object.assignment != null) {
      yield r'assignment';
      yield serializers.serialize(
        object.assignment,
        specifiedType: const FullType.nullable(RideRequestAssignment),
      );
    }
    if (object.locked != null) {
      yield r'locked';
      yield serializers.serialize(
        object.locked,
        specifiedType: const FullType(bool),
      );
    }
    if (object.escalatedAt != null) {
      yield r'escalated_at';
      yield serializers.serialize(
        object.escalatedAt,
        specifiedType: const FullType.nullable(DateTime),
      );
    }
    if (object.cancelReason != null) {
      yield r'cancel_reason';
      yield serializers.serialize(
        object.cancelReason,
        specifiedType: const FullType.nullable(String),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    RideRequest object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required RideRequestBuilder result,
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
        case r'employee_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.employeeId = valueDes;
          break;
        case r'employee_name':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.employeeName = valueDes;
          break;
        case r'client_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.clientId = valueDes;
          break;
        case r'direction':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(Direction),
          ) as Direction;
          result.direction = valueDes;
          break;
        case r'office_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.officeId = valueDes;
          break;
        case r'location':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(LatLng),
          ) as LatLng;
          result.location.replace(valueDes);
          break;
        case r'pickup_location':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(LatLng),
          ) as LatLng?;
          if (valueDes == null) continue;
          result.pickupLocation.replace(valueDes);
          break;
        case r'landmark':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(String),
          ) as String?;
          if (valueDes == null) continue;
          result.landmark = valueDes;
          break;
        case r'requested_time':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(DateTime),
          ) as DateTime;
          result.requestedTime = valueDes;
          break;
        case r'urgency':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(Urgency),
          ) as Urgency;
          result.urgency = valueDes;
          break;
        case r'no_sharing':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(bool),
          ) as bool;
          result.noSharing = valueDes;
          break;
        case r'status':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(RequestStatus),
          ) as RequestStatus;
          result.status = valueDes;
          break;
        case r'waiting_since':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(DateTime),
          ) as DateTime;
          result.waitingSince = valueDes;
          break;
        case r'trip_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(String),
          ) as String?;
          if (valueDes == null) continue;
          result.tripId = valueDes;
          break;
        case r'assignment':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(RideRequestAssignment),
          ) as RideRequestAssignment?;
          if (valueDes == null) continue;
          result.assignment.replace(valueDes);
          break;
        case r'locked':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(bool),
          ) as bool;
          result.locked = valueDes;
          break;
        case r'escalated_at':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(DateTime),
          ) as DateTime?;
          if (valueDes == null) continue;
          result.escalatedAt = valueDes;
          break;
        case r'cancel_reason':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(String),
          ) as String?;
          if (valueDes == null) continue;
          result.cancelReason = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  RideRequest deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = RideRequestBuilder();
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

