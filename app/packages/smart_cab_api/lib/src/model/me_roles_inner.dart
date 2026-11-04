//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:smart_cab_api/src/model/role.dart';
import 'package:built_collection/built_collection.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'me_roles_inner.g.dart';

/// MeRolesInner
///
/// Properties:
/// * [role] 
/// * [operatorId] 
/// * [clientId] 
/// * [employeeId] 
/// * [driverId] 
/// * [permissions] 
@BuiltValue()
abstract class MeRolesInner implements Built<MeRolesInner, MeRolesInnerBuilder> {
  @BuiltValueField(wireName: r'role')
  Role? get role;
  // enum roleEnum {  platform_admin,  operator_admin,  supervisor,  driver,  client_admin,  employee,  };

  @BuiltValueField(wireName: r'operator_id')
  String? get operatorId;

  @BuiltValueField(wireName: r'client_id')
  String? get clientId;

  @BuiltValueField(wireName: r'employee_id')
  String? get employeeId;

  @BuiltValueField(wireName: r'driver_id')
  String? get driverId;

  @BuiltValueField(wireName: r'permissions')
  BuiltList<String>? get permissions;

  MeRolesInner._();

  factory MeRolesInner([void updates(MeRolesInnerBuilder b)]) = _$MeRolesInner;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(MeRolesInnerBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<MeRolesInner> get serializer => _$MeRolesInnerSerializer();
}

class _$MeRolesInnerSerializer implements PrimitiveSerializer<MeRolesInner> {
  @override
  final Iterable<Type> types = const [MeRolesInner, _$MeRolesInner];

  @override
  final String wireName = r'MeRolesInner';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    MeRolesInner object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    if (object.role != null) {
      yield r'role';
      yield serializers.serialize(
        object.role,
        specifiedType: const FullType(Role),
      );
    }
    if (object.operatorId != null) {
      yield r'operator_id';
      yield serializers.serialize(
        object.operatorId,
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
    if (object.employeeId != null) {
      yield r'employee_id';
      yield serializers.serialize(
        object.employeeId,
        specifiedType: const FullType.nullable(String),
      );
    }
    if (object.driverId != null) {
      yield r'driver_id';
      yield serializers.serialize(
        object.driverId,
        specifiedType: const FullType.nullable(String),
      );
    }
    if (object.permissions != null) {
      yield r'permissions';
      yield serializers.serialize(
        object.permissions,
        specifiedType: const FullType(BuiltList, [FullType(String)]),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    MeRolesInner object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required MeRolesInnerBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'role':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(Role),
          ) as Role;
          result.role = valueDes;
          break;
        case r'operator_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(String),
          ) as String?;
          if (valueDes == null) continue;
          result.operatorId = valueDes;
          break;
        case r'client_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(String),
          ) as String?;
          if (valueDes == null) continue;
          result.clientId = valueDes;
          break;
        case r'employee_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(String),
          ) as String?;
          if (valueDes == null) continue;
          result.employeeId = valueDes;
          break;
        case r'driver_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(String),
          ) as String?;
          if (valueDes == null) continue;
          result.driverId = valueDes;
          break;
        case r'permissions':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(BuiltList, [FullType(String)]),
          ) as BuiltList<String>;
          result.permissions.replace(valueDes);
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  MeRolesInner deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = MeRolesInnerBuilder();
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

