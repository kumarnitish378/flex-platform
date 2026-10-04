//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'ride_request_assignment.g.dart';

/// RideRequestAssignment
///
/// Properties:
/// * [vehicleRegistrationNo] 
/// * [vehicleModel] 
/// * [driverName] 
/// * [driverPhone] 
/// * [pickupEta] 
/// * [pickupEtaApproximate] - true when the ETA is approximate (ADR-0010)
@BuiltValue()
abstract class RideRequestAssignment implements Built<RideRequestAssignment, RideRequestAssignmentBuilder> {
  @BuiltValueField(wireName: r'vehicle_registration_no')
  String? get vehicleRegistrationNo;

  @BuiltValueField(wireName: r'vehicle_model')
  String? get vehicleModel;

  @BuiltValueField(wireName: r'driver_name')
  String? get driverName;

  @BuiltValueField(wireName: r'driver_phone')
  String? get driverPhone;

  @BuiltValueField(wireName: r'pickup_eta')
  DateTime? get pickupEta;

  /// true when the ETA is approximate (ADR-0010)
  @BuiltValueField(wireName: r'pickup_eta_approximate')
  bool? get pickupEtaApproximate;

  RideRequestAssignment._();

  factory RideRequestAssignment([void updates(RideRequestAssignmentBuilder b)]) = _$RideRequestAssignment;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(RideRequestAssignmentBuilder b) => b
      ..pickupEtaApproximate = false;

  @BuiltValueSerializer(custom: true)
  static Serializer<RideRequestAssignment> get serializer => _$RideRequestAssignmentSerializer();
}

class _$RideRequestAssignmentSerializer implements PrimitiveSerializer<RideRequestAssignment> {
  @override
  final Iterable<Type> types = const [RideRequestAssignment, _$RideRequestAssignment];

  @override
  final String wireName = r'RideRequestAssignment';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    RideRequestAssignment object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.vehicleRegistrationNo != null) {
      yield r'vehicle_registration_no';
      yield serializers.serialize(
        object.vehicleRegistrationNo,
        specifiedType: const FullType(String),
      );
    }
    if (object.vehicleModel != null) {
      yield r'vehicle_model';
      yield serializers.serialize(
        object.vehicleModel,
        specifiedType: const FullType(String),
      );
    }
    if (object.driverName != null) {
      yield r'driver_name';
      yield serializers.serialize(
        object.driverName,
        specifiedType: const FullType(String),
      );
    }
    if (object.driverPhone != null) {
      yield r'driver_phone';
      yield serializers.serialize(
        object.driverPhone,
        specifiedType: const FullType(String),
      );
    }
    if (object.pickupEta != null) {
      yield r'pickup_eta';
      yield serializers.serialize(
        object.pickupEta,
        specifiedType: const FullType(DateTime),
      );
    }
    if (object.pickupEtaApproximate != null) {
      yield r'pickup_eta_approximate';
      yield serializers.serialize(
        object.pickupEtaApproximate,
        specifiedType: const FullType(bool),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    RideRequestAssignment object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required RideRequestAssignmentBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'vehicle_registration_no':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.vehicleRegistrationNo = valueDes;
          break;
        case r'vehicle_model':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.vehicleModel = valueDes;
          break;
        case r'driver_name':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.driverName = valueDes;
          break;
        case r'driver_phone':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.driverPhone = valueDes;
          break;
        case r'pickup_eta':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(DateTime),
          ) as DateTime;
          result.pickupEta = valueDes;
          break;
        case r'pickup_eta_approximate':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(bool),
          ) as bool;
          result.pickupEtaApproximate = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  RideRequestAssignment deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = RideRequestAssignmentBuilder();
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

