//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_collection/built_collection.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'mode_setting_input.g.dart';

/// Every scoping field is optional; null means \"any\".
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
@BuiltValue(instantiable: false)
abstract class ModeSettingInput  {
  @BuiltValueField(wireName: r'mode')
  ModeSettingInputModeEnum get mode;
  // enum modeEnum {  manual,  semi_auto,  full_auto,  };

  @BuiltValueField(wireName: r'client_id')
  String? get clientId;

  @BuiltValueField(wireName: r'zone_id')
  String? get zoneId;

  @BuiltValueField(wireName: r'direction')
  ModeSettingInputDirectionEnum? get direction;
  // enum directionEnum {  to_office,  from_office,  ,  };

  /// ISO weekdays, Monday = 1 ... Sunday = 7, matching `isoweekday()`. Null or empty means every day.  An array, not the bitmask an earlier draft of this schema specified: `[1,5]` is readable in `psql` and in a log line, renders without decoding, and cannot be confused with the Sunday=0 convention the other half of the world uses. The bitmask saved four bytes a row on a table with tens of rows. 
  @BuiltValueField(wireName: r'weekdays')
  BuiltList<int>? get weekdays;

  /// local time of day, HH:MM:SS
  @BuiltValueField(wireName: r'start_time')
  String? get startTime;

  /// Local time of day, HH:MM:SS. A window needs both ends or neither - the API and a CHECK constraint both refuse one end alone, because guessing midnight for the missing end would stop a \"from 18:00\" rule exactly when an evening shift is still running. May cross midnight (22:00-06:00), in which case the weekday matched is the day the window opened. 
  @BuiltValueField(wireName: r'end_time')
  String? get endTime;

  /// why this rule exists
  @BuiltValueField(wireName: r'note')
  String? get note;

  @BuiltValueSerializer(custom: true)
  static Serializer<ModeSettingInput> get serializer => _$ModeSettingInputSerializer();
}

class _$ModeSettingInputSerializer implements PrimitiveSerializer<ModeSettingInput> {
  @override
  final Iterable<Type> types = const [ModeSettingInput];

  @override
  final String wireName = r'ModeSettingInput';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    ModeSettingInput object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    yield r'mode';
    yield serializers.serialize(
      object.mode,
      specifiedType: const FullType(ModeSettingInputModeEnum),
    );
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
        specifiedType: const FullType.nullable(ModeSettingInputDirectionEnum),
      );
    }
    if (object.weekdays != null) {
      yield r'weekdays';
      yield serializers.serialize(
        object.weekdays,
        specifiedType: const FullType.nullable(BuiltList, [FullType(int)]),
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
    if (object.note != null) {
      yield r'note';
      yield serializers.serialize(
        object.note,
        specifiedType: const FullType.nullable(String),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    ModeSettingInput object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  @override
  ModeSettingInput deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return serializers.deserialize(serialized, specifiedType: FullType($ModeSettingInput)) as $ModeSettingInput;
  }
}

/// a concrete implementation of [ModeSettingInput], since [ModeSettingInput] is not instantiable
@BuiltValue(instantiable: true)
abstract class $ModeSettingInput implements ModeSettingInput, Built<$ModeSettingInput, $ModeSettingInputBuilder> {
  $ModeSettingInput._();

  factory $ModeSettingInput([void Function($ModeSettingInputBuilder)? updates]) = _$$ModeSettingInput;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults($ModeSettingInputBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<$ModeSettingInput> get serializer => _$$ModeSettingInputSerializer();
}

class _$$ModeSettingInputSerializer implements PrimitiveSerializer<$ModeSettingInput> {
  @override
  final Iterable<Type> types = const [$ModeSettingInput, _$$ModeSettingInput];

  @override
  final String wireName = r'$ModeSettingInput';

  @override
  Object serialize(
    Serializers serializers,
    $ModeSettingInput object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return serializers.serialize(object, specifiedType: FullType(ModeSettingInput))!;
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required ModeSettingInputBuilder result,
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
            specifiedType: const FullType.nullable(ModeSettingInputDirectionEnum),
          ) as ModeSettingInputDirectionEnum?;
          if (valueDes == null) continue;
          result.direction = valueDes;
          break;
        case r'weekdays':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(BuiltList, [FullType(int)]),
          ) as BuiltList<int>?;
          if (valueDes == null) continue;
          result.weekdays.replace(valueDes);
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
        case r'note':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(String),
          ) as String?;
          if (valueDes == null) continue;
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
  $ModeSettingInput deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = $ModeSettingInputBuilder();
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

class ModeSettingInputModeEnum extends EnumClass {

  @BuiltValueEnumConst(wireName: r'manual')
  static const ModeSettingInputModeEnum manual = _$modeSettingInputModeEnum_manual;
  @BuiltValueEnumConst(wireName: r'semi_auto')
  static const ModeSettingInputModeEnum semiAuto = _$modeSettingInputModeEnum_semiAuto;
  @BuiltValueEnumConst(wireName: r'full_auto')
  static const ModeSettingInputModeEnum fullAuto = _$modeSettingInputModeEnum_fullAuto;

  static Serializer<ModeSettingInputModeEnum> get serializer => _$modeSettingInputModeEnumSerializer;

  const ModeSettingInputModeEnum._(String name): super(name);

  static BuiltSet<ModeSettingInputModeEnum> get values => _$modeSettingInputModeEnumValues;
  static ModeSettingInputModeEnum valueOf(String name) => _$modeSettingInputModeEnumValueOf(name);
}

class ModeSettingInputDirectionEnum extends EnumClass {

  @BuiltValueEnumConst(wireName: r'to_office')
  static const ModeSettingInputDirectionEnum toOffice = _$modeSettingInputDirectionEnum_toOffice;
  @BuiltValueEnumConst(wireName: r'from_office')
  static const ModeSettingInputDirectionEnum fromOffice = _$modeSettingInputDirectionEnum_fromOffice;

  static Serializer<ModeSettingInputDirectionEnum> get serializer => _$modeSettingInputDirectionEnumSerializer;

  const ModeSettingInputDirectionEnum._(String name): super(name);

  static BuiltSet<ModeSettingInputDirectionEnum> get values => _$modeSettingInputDirectionEnumValues;
  static ModeSettingInputDirectionEnum valueOf(String name) => _$modeSettingInputDirectionEnumValueOf(name);
}

