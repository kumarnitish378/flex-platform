//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:smart_cab_api/src/model/duty_state_mqtt.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'duty_state.g.dart';

/// DutyState
///
/// Properties:
/// * [onDuty] 
/// * [vehicleId] 
/// * [mqtt] 
@BuiltValue()
abstract class DutyState implements Built<DutyState, DutyStateBuilder> {
  @BuiltValueField(wireName: r'on_duty')
  bool? get onDuty;

  @BuiltValueField(wireName: r'vehicle_id')
  String? get vehicleId;

  @BuiltValueField(wireName: r'mqtt')
  DutyStateMqtt? get mqtt;

  DutyState._();

  factory DutyState([void updates(DutyStateBuilder b)]) = _$DutyState;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(DutyStateBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<DutyState> get serializer => _$DutyStateSerializer();
}

class _$DutyStateSerializer implements PrimitiveSerializer<DutyState> {
  @override
  final Iterable<Type> types = const [DutyState, _$DutyState];

  @override
  final String wireName = r'DutyState';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    DutyState object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.onDuty != null) {
      yield r'on_duty';
      yield serializers.serialize(
        object.onDuty,
        specifiedType: const FullType(bool),
      );
    }
    if (object.vehicleId != null) {
      yield r'vehicle_id';
      yield serializers.serialize(
        object.vehicleId,
        specifiedType: const FullType.nullable(String),
      );
    }
    if (object.mqtt != null) {
      yield r'mqtt';
      yield serializers.serialize(
        object.mqtt,
        specifiedType: const FullType.nullable(DutyStateMqtt),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    DutyState object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required DutyStateBuilder result,
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
        case r'mqtt':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(DutyStateMqtt),
          ) as DutyStateMqtt?;
          if (valueDes == null) continue;
          result.mqtt.replace(valueDes);
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  DutyState deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = DutyStateBuilder();
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

