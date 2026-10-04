//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:smart_cab_api/src/model/lat_lng.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'employee_input.g.dart';

/// EmployeeInput
///
/// Properties:
/// * [name] 
/// * [phone] 
/// * [officeId] 
/// * [homeLocation] 
/// * [homeLandmark] 
/// * [priority] 
/// * [isVip] 
/// * [nightEscortRequired] 
/// * [active] 
@BuiltValue(instantiable: false)
abstract class EmployeeInput  {
  @BuiltValueField(wireName: r'name')
  String get name;

  @BuiltValueField(wireName: r'phone')
  String get phone;

  @BuiltValueField(wireName: r'office_id')
  String get officeId;

  @BuiltValueField(wireName: r'home_location')
  LatLng get homeLocation;

  @BuiltValueField(wireName: r'home_landmark')
  String? get homeLandmark;

  @BuiltValueField(wireName: r'priority')
  int? get priority;

  @BuiltValueField(wireName: r'is_vip')
  bool? get isVip;

  @BuiltValueField(wireName: r'night_escort_required')
  bool? get nightEscortRequired;

  @BuiltValueField(wireName: r'active')
  bool? get active;

  @BuiltValueSerializer(custom: true)
  static Serializer<EmployeeInput> get serializer => _$EmployeeInputSerializer();
}

class _$EmployeeInputSerializer implements PrimitiveSerializer<EmployeeInput> {
  @override
  final Iterable<Type> types = const [EmployeeInput];

  @override
  final String wireName = r'EmployeeInput';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    EmployeeInput object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    yield r'name';
    yield serializers.serialize(
      object.name,
      specifiedType: const FullType(String),
    );
    yield r'phone';
    yield serializers.serialize(
      object.phone,
      specifiedType: const FullType(String),
    );
    yield r'office_id';
    yield serializers.serialize(
      object.officeId,
      specifiedType: const FullType(String),
    );
    yield r'home_location';
    yield serializers.serialize(
      object.homeLocation,
      specifiedType: const FullType(LatLng),
    );
    if (object.homeLandmark != null) {
      yield r'home_landmark';
      yield serializers.serialize(
        object.homeLandmark,
        specifiedType: const FullType(String),
      );
    }
    if (object.priority != null) {
      yield r'priority';
      yield serializers.serialize(
        object.priority,
        specifiedType: const FullType(int),
      );
    }
    if (object.isVip != null) {
      yield r'is_vip';
      yield serializers.serialize(
        object.isVip,
        specifiedType: const FullType(bool),
      );
    }
    if (object.nightEscortRequired != null) {
      yield r'night_escort_required';
      yield serializers.serialize(
        object.nightEscortRequired,
        specifiedType: const FullType(bool),
      );
    }
    if (object.active != null) {
      yield r'active';
      yield serializers.serialize(
        object.active,
        specifiedType: const FullType(bool),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    EmployeeInput object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  @override
  EmployeeInput deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return serializers.deserialize(serialized, specifiedType: FullType($EmployeeInput)) as $EmployeeInput;
  }
}

/// a concrete implementation of [EmployeeInput], since [EmployeeInput] is not instantiable
@BuiltValue(instantiable: true)
abstract class $EmployeeInput implements EmployeeInput, Built<$EmployeeInput, $EmployeeInputBuilder> {
  $EmployeeInput._();

  factory $EmployeeInput([void Function($EmployeeInputBuilder)? updates]) = _$$EmployeeInput;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults($EmployeeInputBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<$EmployeeInput> get serializer => _$$EmployeeInputSerializer();
}

class _$$EmployeeInputSerializer implements PrimitiveSerializer<$EmployeeInput> {
  @override
  final Iterable<Type> types = const [$EmployeeInput, _$$EmployeeInput];

  @override
  final String wireName = r'$EmployeeInput';

  @override
  Object serialize(
    Serializers serializers,
    $EmployeeInput object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return serializers.serialize(object, specifiedType: FullType(EmployeeInput))!;
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required EmployeeInputBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'name':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.name = valueDes;
          break;
        case r'phone':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.phone = valueDes;
          break;
        case r'office_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.officeId = valueDes;
          break;
        case r'home_location':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(LatLng),
          ) as LatLng;
          result.homeLocation.replace(valueDes);
          break;
        case r'home_landmark':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.homeLandmark = valueDes;
          break;
        case r'priority':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(int),
          ) as int;
          result.priority = valueDes;
          break;
        case r'is_vip':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(bool),
          ) as bool;
          result.isVip = valueDes;
          break;
        case r'night_escort_required':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(bool),
          ) as bool;
          result.nightEscortRequired = valueDes;
          break;
        case r'active':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(bool),
          ) as bool;
          result.active = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  $EmployeeInput deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = $EmployeeInputBuilder();
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

