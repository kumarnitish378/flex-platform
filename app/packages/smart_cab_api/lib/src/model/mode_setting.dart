//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_collection/built_collection.dart';
import 'package:smart_cab_api/src/model/mode_setting_input.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'mode_setting.g.dart';

/// ModeSetting
///
/// Properties:
/// * [mode] 
/// * [clientId] 
/// * [zoneId] 
/// * [direction] 
/// * [weekdays] - ISO weekdays, Monday = 1 ... Sunday = 7, matching `isoweekday()`. Null or empty means every day.  An array, not the bitmask an earlier draft of this schema specified: `[1,5]` is readable in `psql` and in a log line, renders without decoding, and cannot be confused with the Sunday=0 convention the other half of the world uses. The bitmask saved four bytes a row on a table with tens of rows. 
/// * [startTime] - local time of day, HH:MM:SS
/// * [endTime] - Local time of day, HH:MM:SS. A window needs both ends or neither - the API and a CHECK constraint both refuse one end alone, because guessing midnight for the missing end would stop a \"from 18:00\" rule exactly when an evening shift is still running. May cross midnight (22:00-06:00), in which case the weekday matched is the day the window opened. 
/// * [note] - why this rule exists
/// * [id] 
/// * [updatedAt] 
@BuiltValue()
abstract class ModeSetting implements ModeSettingInput, Built<ModeSetting, ModeSettingBuilder> {
  @BuiltValueField(wireName: r'id')
  String? get id;

  @BuiltValueField(wireName: r'updated_at')
  DateTime? get updatedAt;

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
    yield r'mode';
    yield serializers.serialize(
      object.mode,
      specifiedType: const FullType(ModeSettingInputModeEnum),
    );
    if (object.note != null) {
      yield r'note';
      yield serializers.serialize(
        object.note,
        specifiedType: const FullType.nullable(String),
      );
    }
    if (object.clientId != null) {
      yield r'client_id';
      yield serializers.serialize(
        object.clientId,
        specifiedType: const FullType.nullable(String),
      );
    }
    if (object.weekdays != null) {
      yield r'weekdays';
      yield serializers.serialize(
        object.weekdays,
        specifiedType: const FullType.nullable(BuiltList, [FullType(int)]),
      );
    }
    if (object.zoneId != null) {
      yield r'zone_id';
      yield serializers.serialize(
        object.zoneId,
        specifiedType: const FullType.nullable(String),
      );
    }
    if (object.startTime != null) {
      yield r'start_time';
      yield serializers.serialize(
        object.startTime,
        specifiedType: const FullType.nullable(String),
      );
    }
    if (object.id != null) {
      yield r'id';
      yield serializers.serialize(
        object.id,
        specifiedType: const FullType(String),
      );
    }
    if (object.endTime != null) {
      yield r'end_time';
      yield serializers.serialize(
        object.endTime,
        specifiedType: const FullType.nullable(String),
      );
    }
    if (object.updatedAt != null) {
      yield r'updated_at';
      yield serializers.serialize(
        object.updatedAt,
        specifiedType: const FullType(DateTime),
      );
    }
    if (object.direction != null) {
      yield r'direction';
      yield serializers.serialize(
        object.direction,
        specifiedType: const FullType.nullable(ModeSettingInputDirectionEnum),
      );
    }
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
        case r'mode':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(ModeSettingInputModeEnum),
          ) as ModeSettingInputModeEnum;
          result.mode = valueDes;
          break;
        case r'note':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(String),
          ) as String?;
          if (valueDes == null) continue;
          result.note = valueDes;
          break;
        case r'client_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(String),
          ) as String?;
          if (valueDes == null) continue;
          result.clientId = valueDes;
          break;
        case r'weekdays':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(BuiltList, [FullType(int)]),
          ) as BuiltList<int>?;
          if (valueDes == null) continue;
          result.weekdays.replace(valueDes);
          break;
        case r'zone_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(String),
          ) as String?;
          if (valueDes == null) continue;
          result.zoneId = valueDes;
          break;
        case r'start_time':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(String),
          ) as String?;
          if (valueDes == null) continue;
          result.startTime = valueDes;
          break;
        case r'id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.id = valueDes;
          break;
        case r'end_time':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(String),
          ) as String?;
          if (valueDes == null) continue;
          result.endTime = valueDes;
          break;
        case r'updated_at':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(DateTime),
          ) as DateTime;
          result.updatedAt = valueDes;
          break;
        case r'direction':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(ModeSettingInputDirectionEnum),
          ) as ModeSettingInputDirectionEnum?;
          if (valueDes == null) continue;
          result.direction = valueDes;
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

class ModeSettingDirectionEnum extends EnumClass {

  @BuiltValueEnumConst(wireName: r'to_office')
  static const ModeSettingDirectionEnum toOffice = _$modeSettingDirectionEnum_toOffice;
  @BuiltValueEnumConst(wireName: r'from_office')
  static const ModeSettingDirectionEnum fromOffice = _$modeSettingDirectionEnum_fromOffice;

  static Serializer<ModeSettingDirectionEnum> get serializer => _$modeSettingDirectionEnumSerializer;

  const ModeSettingDirectionEnum._(String name): super(name);

  static BuiltSet<ModeSettingDirectionEnum> get values => _$modeSettingDirectionEnumValues;
  static ModeSettingDirectionEnum valueOf(String name) => _$modeSettingDirectionEnumValueOf(name);
}

