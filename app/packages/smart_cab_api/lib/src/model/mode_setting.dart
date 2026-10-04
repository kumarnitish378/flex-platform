//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_collection/built_collection.dart';
import 'package:smart_cab_api/src/model/direction.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'mode_setting.g.dart';

/// ModeSetting
///
/// Properties:
/// * [id] 
/// * [clientId] 
/// * [zoneId] 
/// * [direction] 
/// * [weekdays] - bitmask Mon=1..Sun=64
/// * [startTime] 
/// * [endTime] 
/// * [mode] 
@BuiltValue()
abstract class ModeSetting implements Built<ModeSetting, ModeSettingBuilder> {
  @BuiltValueField(wireName: r'id')
  String? get id;

  @BuiltValueField(wireName: r'client_id')
  String? get clientId;

  @BuiltValueField(wireName: r'zone_id')
  String? get zoneId;

  @BuiltValueField(wireName: r'direction')
  Direction? get direction;
  // enum directionEnum {  to_office,  from_office,  };

  /// bitmask Mon=1..Sun=64
  @BuiltValueField(wireName: r'weekdays')
  int? get weekdays;

  @BuiltValueField(wireName: r'start_time')
  String? get startTime;

  @BuiltValueField(wireName: r'end_time')
  String? get endTime;

  @BuiltValueField(wireName: r'mode')
  ModeSettingModeEnum get mode;
  // enum modeEnum {  manual,  semi_auto,  full_auto,  };

  ModeSetting._();

  factory ModeSetting([void updates(ModeSettingBuilder b)]) = _$ModeSetting;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(ModeSettingBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<ModeSetting> get serializer => _$ModeSettingSerializer();
}

class _$ModeSettingSerializer implements PrimitiveSerializer<ModeSetting> {
  @override
  final Iterable<Type> types = const [ModeSetting, _$ModeSetting];

  @override
  final String wireName = r'ModeSetting';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    ModeSetting object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.id != null) {
      yield r'id';
      yield serializers.serialize(
        object.id,
        specifiedType: const FullType(String),
      );
    }
    if (object.clientId != null) {
      yield r'client_id';
      yield serializers.serialize(
        object.clientId,
        specifiedType: const FullType.nullable(String),
      );
    }
    if (object.zoneId != null) {
      yield r'zone_id';
      yield serializers.serialize(
        object.zoneId,
        specifiedType: const FullType.nullable(String),
      );
    }
    if (object.direction != null) {
      yield r'direction';
      yield serializers.serialize(
        object.direction,
        specifiedType: const FullType.nullable(Direction),
      );
    }
    if (object.weekdays != null) {
      yield r'weekdays';
      yield serializers.serialize(
        object.weekdays,
        specifiedType: const FullType.nullable(int),
      );
    }
    if (object.startTime != null) {
      yield r'start_time';
      yield serializers.serialize(
        object.startTime,
        specifiedType: const FullType.nullable(String),
      );
    }
    if (object.endTime != null) {
      yield r'end_time';
      yield serializers.serialize(
        object.endTime,
        specifiedType: const FullType.nullable(String),
      );
    }
    yield r'mode';
    yield serializers.serialize(
      object.mode,
      specifiedType: const FullType(ModeSettingModeEnum),
    );
  }

  @override
  Object serialize(
    Serializers serializers,
    ModeSetting object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required ModeSettingBuilder result,
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
        case r'client_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(String),
          ) as String?;
          if (valueDes == null) continue;
          result.clientId = valueDes;
          break;
        case r'zone_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(String),
          ) as String?;
          if (valueDes == null) continue;
          result.zoneId = valueDes;
          break;
        case r'direction':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(Direction),
          ) as Direction?;
          if (valueDes == null) continue;
          result.direction = valueDes;
          break;
        case r'weekdays':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(int),
          ) as int?;
          if (valueDes == null) continue;
          result.weekdays = valueDes;
          break;
        case r'start_time':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(String),
          ) as String?;
          if (valueDes == null) continue;
          result.startTime = valueDes;
          break;
        case r'end_time':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(String),
          ) as String?;
          if (valueDes == null) continue;
          result.endTime = valueDes;
          break;
        case r'mode':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(ModeSettingModeEnum),
          ) as ModeSettingModeEnum;
          result.mode = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  ModeSetting deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = ModeSettingBuilder();
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

class ModeSettingModeEnum extends EnumClass {

  @BuiltValueEnumConst(wireName: r'manual')
  static const ModeSettingModeEnum manual = _$modeSettingModeEnum_manual;
  @BuiltValueEnumConst(wireName: r'semi_auto')
  static const ModeSettingModeEnum semiAuto = _$modeSettingModeEnum_semiAuto;
  @BuiltValueEnumConst(wireName: r'full_auto')
  static const ModeSettingModeEnum fullAuto = _$modeSettingModeEnum_fullAuto;

  static Serializer<ModeSettingModeEnum> get serializer => _$modeSettingModeEnumSerializer;

  const ModeSettingModeEnum._(String name): super(name);

  static BuiltSet<ModeSettingModeEnum> get values => _$modeSettingModeEnumValues;
  static ModeSettingModeEnum valueOf(String name) => _$modeSettingModeEnumValueOf(name);
}

