//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:smart_cab_api/src/model/employee_input.dart';
import 'package:smart_cab_api/src/model/lat_lng.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'employee.g.dart';

/// Employee
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
/// * [id] 
/// * [clientId] 
/// * [zoneId] 
@BuiltValue()
abstract class Employee implements EmployeeInput, Built<Employee, EmployeeBuilder> {
  @BuiltValueField(wireName: r'client_id')
  String? get clientId;

  @BuiltValueField(wireName: r'zone_id')
  String? get zoneId;

  @BuiltValueField(wireName: r'id')
  String? get id;

  Employee._();

  factory Employee([void updates(EmployeeBuilder b)]) = _$Employee;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(EmployeeBuilder b) => b
      ..nightEscortRequired = false
      ..active = true
      ..priority = 5
      ..isVip = false;

  @BuiltValueSerializer(custom: true)
  static Serializer<Employee> get serializer => _$EmployeeSerializer();
}

class _$EmployeeSerializer implements PrimitiveSerializer<Employee> {
  @override
  final Iterable<Type> types = const [Employee, _$Employee];

  @override
  final String wireName = r'Employee';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    Employee object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.clientId != null) {
      yield r'client_id';
      yield serializers.serialize(
        object.clientId,
        specifiedType: const FullType(String),
      );
    }
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
    if (object.nightEscortRequired != null) {
      yield r'night_escort_required';
      yield serializers.serialize(
        object.nightEscortRequired,
        specifiedType: const FullType(bool),
      );
    }
    yield r'name';
    yield serializers.serialize(
      object.name,
      specifiedType: const FullType(String),
    );
    if (object.zoneId != null) {
      yield r'zone_id';
      yield serializers.serialize(
        object.zoneId,
        specifiedType: const FullType.nullable(String),
      );
    }
    if (object.active != null) {
      yield r'active';
      yield serializers.serialize(
        object.active,
        specifiedType: const FullType(bool),
      );
    }
    if (object.id != null) {
      yield r'id';
      yield serializers.serialize(
        object.id,
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
    if (object.homeLandmark != null) {
      yield r'home_landmark';
      yield serializers.serialize(
        object.homeLandmark,
        specifiedType: const FullType(String),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    Employee object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required EmployeeBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'client_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.clientId = valueDes;
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
        case r'night_escort_required':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(bool),
          ) as bool;
          result.nightEscortRequired = valueDes;
          break;
        case r'name':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.name = valueDes;
          break;
        case r'zone_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(String),
          ) as String?;
          if (valueDes == null) continue;
          result.zoneId = valueDes;
          break;
        case r'active':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(bool),
          ) as bool;
          result.active = valueDes;
          break;
        case r'id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.id = valueDes;
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
        case r'home_landmark':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.homeLandmark = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  Employee deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = EmployeeBuilder();
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

