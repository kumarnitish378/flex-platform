//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_collection/built_collection.dart';
import 'package:built_value/json_object.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'alert.g.dart';

/// Alert
///
/// Properties:
/// * [id] 
/// * [type] 
/// * [severity] 
/// * [status] 
/// * [createdAt] 
/// * [requestId] 
/// * [tripId] 
/// * [vehicleId] 
/// * [data] 
@BuiltValue()
abstract class Alert implements Built<Alert, AlertBuilder> {
  @BuiltValueField(wireName: r'id')
  String? get id;

  @BuiltValueField(wireName: r'type')
  AlertTypeEnum? get type;
  // enum typeEnum {  sos,  driver_issue,  request_unassigned,  request_near_expiry,  vip_no_vehicle,  failsafe,  stale_vehicle,  mode_prompt,  system,  };

  @BuiltValueField(wireName: r'severity')
  AlertSeverityEnum? get severity;
  // enum severityEnum {  critical,  warning,  info,  };

  @BuiltValueField(wireName: r'status')
  AlertStatusEnum? get status;
  // enum statusEnum {  open,  acknowledged,  resolved,  };

  @BuiltValueField(wireName: r'created_at')
  DateTime? get createdAt;

  @BuiltValueField(wireName: r'request_id')
  String? get requestId;

  @BuiltValueField(wireName: r'trip_id')
  String? get tripId;

  @BuiltValueField(wireName: r'vehicle_id')
  String? get vehicleId;

  @BuiltValueField(wireName: r'data')
  BuiltMap<String, JsonObject?>? get data;

  Alert._();

  factory Alert([void updates(AlertBuilder b)]) = _$Alert;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(AlertBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<Alert> get serializer => _$AlertSerializer();
}

class _$AlertSerializer implements PrimitiveSerializer<Alert> {
  @override
  final Iterable<Type> types = const [Alert, _$Alert];

  @override
  final String wireName = r'Alert';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    Alert object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.id != null) {
      yield r'id';
      yield serializers.serialize(
        object.id,
        specifiedType: const FullType(String),
      );
    }
    if (object.type != null) {
      yield r'type';
      yield serializers.serialize(
        object.type,
        specifiedType: const FullType(AlertTypeEnum),
      );
    }
    if (object.severity != null) {
      yield r'severity';
      yield serializers.serialize(
        object.severity,
        specifiedType: const FullType(AlertSeverityEnum),
      );
    }
    if (object.status != null) {
      yield r'status';
      yield serializers.serialize(
        object.status,
        specifiedType: const FullType(AlertStatusEnum),
      );
    }
    if (object.createdAt != null) {
      yield r'created_at';
      yield serializers.serialize(
        object.createdAt,
        specifiedType: const FullType(DateTime),
      );
    }
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
    if (object.data != null) {
      yield r'data';
      yield serializers.serialize(
        object.data,
        specifiedType: const FullType(BuiltMap, [FullType(String), FullType.nullable(JsonObject)]),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    Alert object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required AlertBuilder result,
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
        case r'type':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(AlertTypeEnum),
          ) as AlertTypeEnum;
          result.type = valueDes;
          break;
        case r'severity':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(AlertSeverityEnum),
          ) as AlertSeverityEnum;
          result.severity = valueDes;
          break;
        case r'status':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(AlertStatusEnum),
          ) as AlertStatusEnum;
          result.status = valueDes;
          break;
        case r'created_at':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(DateTime),
          ) as DateTime;
          result.createdAt = valueDes;
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
        case r'data':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(BuiltMap, [FullType(String), FullType.nullable(JsonObject)]),
          ) as BuiltMap<String, JsonObject?>;
          result.data.replace(valueDes);
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  Alert deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = AlertBuilder();
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

class AlertTypeEnum extends EnumClass {

  @BuiltValueEnumConst(wireName: r'sos')
  static const AlertTypeEnum sos = _$alertTypeEnum_sos;
  @BuiltValueEnumConst(wireName: r'driver_issue')
  static const AlertTypeEnum driverIssue = _$alertTypeEnum_driverIssue;
  @BuiltValueEnumConst(wireName: r'request_unassigned')
  static const AlertTypeEnum requestUnassigned = _$alertTypeEnum_requestUnassigned;
  @BuiltValueEnumConst(wireName: r'request_near_expiry')
  static const AlertTypeEnum requestNearExpiry = _$alertTypeEnum_requestNearExpiry;
  @BuiltValueEnumConst(wireName: r'vip_no_vehicle')
  static const AlertTypeEnum vipNoVehicle = _$alertTypeEnum_vipNoVehicle;
  @BuiltValueEnumConst(wireName: r'failsafe')
  static const AlertTypeEnum failsafe = _$alertTypeEnum_failsafe;
  @BuiltValueEnumConst(wireName: r'stale_vehicle')
  static const AlertTypeEnum staleVehicle = _$alertTypeEnum_staleVehicle;
  @BuiltValueEnumConst(wireName: r'mode_prompt')
  static const AlertTypeEnum modePrompt = _$alertTypeEnum_modePrompt;
  @BuiltValueEnumConst(wireName: r'system')
  static const AlertTypeEnum system = _$alertTypeEnum_system;

  static Serializer<AlertTypeEnum> get serializer => _$alertTypeEnumSerializer;

  const AlertTypeEnum._(String name): super(name);

  static BuiltSet<AlertTypeEnum> get values => _$alertTypeEnumValues;
  static AlertTypeEnum valueOf(String name) => _$alertTypeEnumValueOf(name);
}

class AlertSeverityEnum extends EnumClass {

  @BuiltValueEnumConst(wireName: r'critical')
  static const AlertSeverityEnum critical = _$alertSeverityEnum_critical;
  @BuiltValueEnumConst(wireName: r'warning')
  static const AlertSeverityEnum warning = _$alertSeverityEnum_warning;
  @BuiltValueEnumConst(wireName: r'info')
  static const AlertSeverityEnum info = _$alertSeverityEnum_info;

  static Serializer<AlertSeverityEnum> get serializer => _$alertSeverityEnumSerializer;

  const AlertSeverityEnum._(String name): super(name);

  static BuiltSet<AlertSeverityEnum> get values => _$alertSeverityEnumValues;
  static AlertSeverityEnum valueOf(String name) => _$alertSeverityEnumValueOf(name);
}

class AlertStatusEnum extends EnumClass {

  @BuiltValueEnumConst(wireName: r'open')
  static const AlertStatusEnum open = _$alertStatusEnum_open;
  @BuiltValueEnumConst(wireName: r'acknowledged')
  static const AlertStatusEnum acknowledged = _$alertStatusEnum_acknowledged;
  @BuiltValueEnumConst(wireName: r'resolved')
  static const AlertStatusEnum resolved = _$alertStatusEnum_resolved;

  static Serializer<AlertStatusEnum> get serializer => _$alertStatusEnumSerializer;

  const AlertStatusEnum._(String name): super(name);

  static BuiltSet<AlertStatusEnum> get values => _$alertStatusEnumValues;
  static AlertStatusEnum valueOf(String name) => _$alertStatusEnumValueOf(name);
}

