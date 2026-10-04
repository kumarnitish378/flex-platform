//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_collection/built_collection.dart';
import 'package:smart_cab_api/src/model/reason_code.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'override_input.g.dart';

/// OverrideInput
///
/// Properties:
/// * [action] 
/// * [requestId] 
/// * [tripId] 
/// * [vehicleId] 
/// * [targetVehicleId] 
/// * [holdUntil] 
/// * [expiresAt] 
/// * [reasonCode] 
/// * [note] 
@BuiltValue()
abstract class OverrideInput implements Built<OverrideInput, OverrideInputBuilder> {
  @BuiltValueField(wireName: r'action')
  OverrideInputActionEnum get action;
  // enum actionEnum {  reassign,  lock,  unlock,  force_priority,  block_pooling,  hold,  cancel,  vehicle_out_of_service,  };

  @BuiltValueField(wireName: r'request_id')
  String? get requestId;

  @BuiltValueField(wireName: r'trip_id')
  String? get tripId;

  @BuiltValueField(wireName: r'vehicle_id')
  String? get vehicleId;

  @BuiltValueField(wireName: r'target_vehicle_id')
  String? get targetVehicleId;

  @BuiltValueField(wireName: r'hold_until')
  DateTime? get holdUntil;

  @BuiltValueField(wireName: r'expires_at')
  DateTime? get expiresAt;

  @BuiltValueField(wireName: r'reason_code')
  ReasonCode get reasonCode;
  // enum reasonCodeEnum {  driver_issue,  local_knowledge,  client_request,  traffic,  vehicle_issue,  safety,  other,  };

  @BuiltValueField(wireName: r'note')
  String? get note;

  OverrideInput._();

  factory OverrideInput([void updates(OverrideInputBuilder b)]) = _$OverrideInput;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(OverrideInputBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<OverrideInput> get serializer => _$OverrideInputSerializer();
}

class _$OverrideInputSerializer implements PrimitiveSerializer<OverrideInput> {
  @override
  final Iterable<Type> types = const [OverrideInput, _$OverrideInput];

  @override
  final String wireName = r'OverrideInput';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    OverrideInput object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    yield r'action';
    yield serializers.serialize(
      object.action,
      specifiedType: const FullType(OverrideInputActionEnum),
    );
    if (object.requestId != null) {
      yield r'request_id';
      yield serializers.serialize(
        object.requestId,
        specifiedType: const FullType.nullable(String),
      );
    }
    if (object.tripId != null) {
      yield r'trip_id';
      yield serializers.serialize(
        object.tripId,
        specifiedType: const FullType.nullable(String),
      );
    }
    if (object.vehicleId != null) {
      yield r'vehicle_id';
      yield serializers.serialize(
        object.vehicleId,
        specifiedType: const FullType.nullable(String),
      );
    }
    if (object.targetVehicleId != null) {
      yield r'target_vehicle_id';
      yield serializers.serialize(
        object.targetVehicleId,
        specifiedType: const FullType.nullable(String),
      );
    }
    if (object.holdUntil != null) {
      yield r'hold_until';
      yield serializers.serialize(
        object.holdUntil,
        specifiedType: const FullType.nullable(DateTime),
      );
    }
    if (object.expiresAt != null) {
      yield r'expires_at';
      yield serializers.serialize(
        object.expiresAt,
        specifiedType: const FullType.nullable(DateTime),
      );
    }
    yield r'reason_code';
    yield serializers.serialize(
      object.reasonCode,
      specifiedType: const FullType(ReasonCode),
    );
    if (object.note != null) {
      yield r'note';
      yield serializers.serialize(
        object.note,
        specifiedType: const FullType(String),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    OverrideInput object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required OverrideInputBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'action':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(OverrideInputActionEnum),
          ) as OverrideInputActionEnum;
          result.action = valueDes;
          break;
        case r'request_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(String),
          ) as String?;
          if (valueDes == null) continue;
          result.requestId = valueDes;
          break;
        case r'trip_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(String),
          ) as String?;
          if (valueDes == null) continue;
          result.tripId = valueDes;
          break;
        case r'vehicle_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(String),
          ) as String?;
          if (valueDes == null) continue;
          result.vehicleId = valueDes;
          break;
        case r'target_vehicle_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(String),
          ) as String?;
          if (valueDes == null) continue;
          result.targetVehicleId = valueDes;
          break;
        case r'hold_until':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(DateTime),
          ) as DateTime?;
          if (valueDes == null) continue;
          result.holdUntil = valueDes;
          break;
        case r'expires_at':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(DateTime),
          ) as DateTime?;
          if (valueDes == null) continue;
          result.expiresAt = valueDes;
          break;
        case r'reason_code':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(ReasonCode),
          ) as ReasonCode;
          result.reasonCode = valueDes;
          break;
        case r'note':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.note = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  OverrideInput deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = OverrideInputBuilder();
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

class OverrideInputActionEnum extends EnumClass {

  @BuiltValueEnumConst(wireName: r'reassign')
  static const OverrideInputActionEnum reassign = _$overrideInputActionEnum_reassign;
  @BuiltValueEnumConst(wireName: r'lock')
  static const OverrideInputActionEnum lock = _$overrideInputActionEnum_lock;
  @BuiltValueEnumConst(wireName: r'unlock')
  static const OverrideInputActionEnum unlock = _$overrideInputActionEnum_unlock;
  @BuiltValueEnumConst(wireName: r'force_priority')
  static const OverrideInputActionEnum forcePriority = _$overrideInputActionEnum_forcePriority;
  @BuiltValueEnumConst(wireName: r'block_pooling')
  static const OverrideInputActionEnum blockPooling = _$overrideInputActionEnum_blockPooling;
  @BuiltValueEnumConst(wireName: r'hold')
  static const OverrideInputActionEnum hold = _$overrideInputActionEnum_hold;
  @BuiltValueEnumConst(wireName: r'cancel')
  static const OverrideInputActionEnum cancel = _$overrideInputActionEnum_cancel;
  @BuiltValueEnumConst(wireName: r'vehicle_out_of_service')
  static const OverrideInputActionEnum vehicleOutOfService = _$overrideInputActionEnum_vehicleOutOfService;

  static Serializer<OverrideInputActionEnum> get serializer => _$overrideInputActionEnumSerializer;

  const OverrideInputActionEnum._(String name): super(name);

  static BuiltSet<OverrideInputActionEnum> get values => _$overrideInputActionEnumValues;
  static OverrideInputActionEnum valueOf(String name) => _$overrideInputActionEnumValueOf(name);
}

