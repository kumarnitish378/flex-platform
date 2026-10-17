//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_collection/built_collection.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'mode_resolution.g.dart';

/// ModeResolution
///
/// Properties:
/// * [mode] 
/// * [reason] - which level of control-model.md section 2 decided it
/// * [settingId] - null for the pause, the VIP rule and the operator default
@BuiltValue()
abstract class ModeResolution implements Built<ModeResolution, ModeResolutionBuilder> {
  @BuiltValueField(wireName: r'mode')
  ModeResolutionModeEnum? get mode;
  // enum modeEnum {  manual,  semi_auto,  full_auto,  };

  /// which level of control-model.md section 2 decided it
  @BuiltValueField(wireName: r'reason')
  ModeResolutionReasonEnum? get reason;
  // enum reasonEnum {  automation_paused,  vip,  client_zone_time,  client_time,  zone_time,  client_zone,  client,  zone,  operator_default,  };

  /// null for the pause, the VIP rule and the operator default
  @BuiltValueField(wireName: r'setting_id')
  String? get settingId;

  ModeResolution._();

  factory ModeResolution([void updates(ModeResolutionBuilder b)]) = _$ModeResolution;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(ModeResolutionBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<ModeResolution> get serializer => _$ModeResolutionSerializer();
}

class _$ModeResolutionSerializer implements PrimitiveSerializer<ModeResolution> {
  @override
  final Iterable<Type> types = const [ModeResolution, _$ModeResolution];

  @override
  final String wireName = r'ModeResolution';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    ModeResolution object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.mode != null) {
      yield r'mode';
      yield serializers.serialize(
        object.mode,
        specifiedType: const FullType(ModeResolutionModeEnum),
      );
    }
    if (object.reason != null) {
      yield r'reason';
      yield serializers.serialize(
        object.reason,
        specifiedType: const FullType(ModeResolutionReasonEnum),
      );
    }
    if (object.settingId != null) {
      yield r'setting_id';
      yield serializers.serialize(
        object.settingId,
        specifiedType: const FullType.nullable(String),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    ModeResolution object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required ModeResolutionBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'mode':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(ModeResolutionModeEnum),
          ) as ModeResolutionModeEnum;
          result.mode = valueDes;
          break;
        case r'reason':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(ModeResolutionReasonEnum),
          ) as ModeResolutionReasonEnum;
          result.reason = valueDes;
          break;
        case r'setting_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(String),
          ) as String?;
          if (valueDes == null) continue;
          result.settingId = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  ModeResolution deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = ModeResolutionBuilder();
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

class ModeResolutionModeEnum extends EnumClass {

  @BuiltValueEnumConst(wireName: r'manual')
  static const ModeResolutionModeEnum manual = _$modeResolutionModeEnum_manual;
  @BuiltValueEnumConst(wireName: r'semi_auto')
  static const ModeResolutionModeEnum semiAuto = _$modeResolutionModeEnum_semiAuto;
  @BuiltValueEnumConst(wireName: r'full_auto')
  static const ModeResolutionModeEnum fullAuto = _$modeResolutionModeEnum_fullAuto;

  static Serializer<ModeResolutionModeEnum> get serializer => _$modeResolutionModeEnumSerializer;

  const ModeResolutionModeEnum._(String name): super(name);

  static BuiltSet<ModeResolutionModeEnum> get values => _$modeResolutionModeEnumValues;
  static ModeResolutionModeEnum valueOf(String name) => _$modeResolutionModeEnumValueOf(name);
}

class ModeResolutionReasonEnum extends EnumClass {

  /// which level of control-model.md section 2 decided it
  @BuiltValueEnumConst(wireName: r'automation_paused')
  static const ModeResolutionReasonEnum automationPaused = _$modeResolutionReasonEnum_automationPaused;
  /// which level of control-model.md section 2 decided it
  @BuiltValueEnumConst(wireName: r'vip')
  static const ModeResolutionReasonEnum vip = _$modeResolutionReasonEnum_vip;
  /// which level of control-model.md section 2 decided it
  @BuiltValueEnumConst(wireName: r'client_zone_time')
  static const ModeResolutionReasonEnum clientZoneTime = _$modeResolutionReasonEnum_clientZoneTime;
  /// which level of control-model.md section 2 decided it
  @BuiltValueEnumConst(wireName: r'client_time')
  static const ModeResolutionReasonEnum clientTime = _$modeResolutionReasonEnum_clientTime;
  /// which level of control-model.md section 2 decided it
  @BuiltValueEnumConst(wireName: r'zone_time')
  static const ModeResolutionReasonEnum zoneTime = _$modeResolutionReasonEnum_zoneTime;
  /// which level of control-model.md section 2 decided it
  @BuiltValueEnumConst(wireName: r'client_zone')
  static const ModeResolutionReasonEnum clientZone = _$modeResolutionReasonEnum_clientZone;
  /// which level of control-model.md section 2 decided it
  @BuiltValueEnumConst(wireName: r'client')
  static const ModeResolutionReasonEnum client = _$modeResolutionReasonEnum_client;
  /// which level of control-model.md section 2 decided it
  @BuiltValueEnumConst(wireName: r'zone')
  static const ModeResolutionReasonEnum zone = _$modeResolutionReasonEnum_zone;
  /// which level of control-model.md section 2 decided it
  @BuiltValueEnumConst(wireName: r'operator_default')
  static const ModeResolutionReasonEnum operatorDefault = _$modeResolutionReasonEnum_operatorDefault;

  static Serializer<ModeResolutionReasonEnum> get serializer => _$modeResolutionReasonEnumSerializer;

  const ModeResolutionReasonEnum._(String name): super(name);

  static BuiltSet<ModeResolutionReasonEnum> get values => _$modeResolutionReasonEnumValues;
  static ModeResolutionReasonEnum valueOf(String name) => _$modeResolutionReasonEnumValueOf(name);
}

