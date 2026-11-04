//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'driver_duty_post_request.g.dart';

/// DriverDutyPostRequest
///
/// Properties:
/// * [onDuty] 
/// * [vehicleId] - defaults to driver's default vehicle
/// * [odometerKm] - The dashboard reading in km - the opening one when going on duty, the closing one when going off. Optional. A closing reading below the opening one is a 422. Per-cab-per-day billing cross-checks GPS km against it.
@BuiltValue()
abstract class DriverDutyPostRequest implements Built<DriverDutyPostRequest, DriverDutyPostRequestBuilder> {
  @BuiltValueField(wireName: r'on_duty')
  bool get onDuty;

  /// defaults to driver's default vehicle
  @BuiltValueField(wireName: r'vehicle_id')
  String? get vehicleId;

  /// The dashboard reading in km - the opening one when going on duty, the closing one when going off. Optional. A closing reading below the opening one is a 422. Per-cab-per-day billing cross-checks GPS km against it.
  @BuiltValueField(wireName: r'odometer_km')
  num? get odometerKm;

  DriverDutyPostRequest._();

  factory DriverDutyPostRequest([void updates(DriverDutyPostRequestBuilder b)]) = _$DriverDutyPostRequest;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(DriverDutyPostRequestBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<DriverDutyPostRequest> get serializer => _$DriverDutyPostRequestSerializer();
}

class _$DriverDutyPostRequestSerializer implements PrimitiveSerializer<DriverDutyPostRequest> {
  @override
  final Iterable<Type> types = const [DriverDutyPostRequest, _$DriverDutyPostRequest];

  @override
  final String wireName = r'DriverDutyPostRequest';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    DriverDutyPostRequest object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    yield r'on_duty';
    yield serializers.serialize(
      object.onDuty,
      specifiedType: const FullType(bool),
    );
    if (object.vehicleId != null) {
      yield r'vehicle_id';
      yield serializers.serialize(
        object.vehicleId,
        specifiedType: const FullType.nullable(String),
      );
    }
    if (object.odometerKm != null) {
      yield r'odometer_km';
      yield serializers.serialize(
        object.odometerKm,
        specifiedType: const FullType.nullable(num),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    DriverDutyPostRequest object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required DriverDutyPostRequestBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'on_duty':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(bool),
          ) as bool;
          result.onDuty = valueDes;
          break;
        case r'vehicle_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(String),
          ) as String?;
          if (valueDes == null) continue;
          result.vehicleId = valueDes;
          break;
        case r'odometer_km':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(num),
          ) as num?;
          if (valueDes == null) continue;
          result.odometerKm = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  DriverDutyPostRequest deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = DriverDutyPostRequestBuilder();
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

