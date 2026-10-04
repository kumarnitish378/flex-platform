//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:smart_cab_api/src/model/urgency.dart';
import 'package:smart_cab_api/src/model/lat_lng.dart';
import 'package:smart_cab_api/src/model/direction.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'ride_request_input.g.dart';

/// RideRequestInput
///
/// Properties:
/// * [employeeId] - required when created on behalf; ignored for employee role
/// * [direction] 
/// * [requestedTime] - pickup time for to_office; ready-to-leave time for from_office
/// * [location] 
/// * [landmark] 
/// * [urgency] 
/// * [noSharing] 
@BuiltValue()
abstract class RideRequestInput implements Built<RideRequestInput, RideRequestInputBuilder> {
  /// required when created on behalf; ignored for employee role
  @BuiltValueField(wireName: r'employee_id')
  String? get employeeId;

  @BuiltValueField(wireName: r'direction')
  Direction get direction;
  // enum directionEnum {  to_office,  from_office,  };

  /// pickup time for to_office; ready-to-leave time for from_office
  @BuiltValueField(wireName: r'requested_time')
  DateTime get requestedTime;

  @BuiltValueField(wireName: r'location')
  LatLng? get location;

  @BuiltValueField(wireName: r'landmark')
  String? get landmark;

  @BuiltValueField(wireName: r'urgency')
  Urgency? get urgency;
  // enum urgencyEnum {  high,  medium,  low,  };

  @BuiltValueField(wireName: r'no_sharing')
  bool? get noSharing;

  RideRequestInput._();

  factory RideRequestInput([void updates(RideRequestInputBuilder b)]) = _$RideRequestInput;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(RideRequestInputBuilder b) => b
      ..noSharing = false;

  @BuiltValueSerializer(custom: true)
  static Serializer<RideRequestInput> get serializer => _$RideRequestInputSerializer();
}

class _$RideRequestInputSerializer implements PrimitiveSerializer<RideRequestInput> {
  @override
  final Iterable<Type> types = const [RideRequestInput, _$RideRequestInput];

  @override
  final String wireName = r'RideRequestInput';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    RideRequestInput object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.employeeId != null) {
      yield r'employee_id';
      yield serializers.serialize(
        object.employeeId,
        specifiedType: const FullType.nullable(String),
      );
    }
    yield r'direction';
    yield serializers.serialize(
      object.direction,
      specifiedType: const FullType(Direction),
    );
    yield r'requested_time';
    yield serializers.serialize(
      object.requestedTime,
      specifiedType: const FullType(DateTime),
    );
    if (object.location != null) {
      yield r'location';
      yield serializers.serialize(
        object.location,
        specifiedType: const FullType.nullable(LatLng),
      );
    }
    if (object.landmark != null) {
      yield r'landmark';
      yield serializers.serialize(
        object.landmark,
        specifiedType: const FullType(String),
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
  }

  @override
  Object serialize(
    Serializers serializers,
    RideRequestInput object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required RideRequestInputBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'employee_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(String),
          ) as String?;
          if (valueDes == null) continue;
          result.employeeId = valueDes;
          break;
        case r'direction':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(Direction),
          ) as Direction;
          result.direction = valueDes;
          break;
        case r'requested_time':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(DateTime),
          ) as DateTime;
          result.requestedTime = valueDes;
          break;
        case r'location':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(LatLng),
          ) as LatLng?;
          if (valueDes == null) continue;
          result.location.replace(valueDes);
          break;
        case r'landmark':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.landmark = valueDes;
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
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  RideRequestInput deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = RideRequestInputBuilder();
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

