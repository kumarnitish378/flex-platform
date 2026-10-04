// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'role.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

const Role _$platformAdmin = const Role._('platformAdmin');
const Role _$operatorAdmin = const Role._('operatorAdmin');
const Role _$supervisor = const Role._('supervisor');
const Role _$driver = const Role._('driver');
const Role _$clientAdmin = const Role._('clientAdmin');
const Role _$employee = const Role._('employee');

Role _$valueOf(String name) {
  switch (name) {
    case 'platformAdmin':
      return _$platformAdmin;
    case 'operatorAdmin':
      return _$operatorAdmin;
    case 'supervisor':
      return _$supervisor;
    case 'driver':
      return _$driver;
    case 'clientAdmin':
      return _$clientAdmin;
    case 'employee':
      return _$employee;
    default:
      throw ArgumentError(name);
  }
}

final BuiltSet<Role> _$values = BuiltSet<Role>(const <Role>[
  _$platformAdmin,
  _$operatorAdmin,
  _$supervisor,
  _$driver,
  _$clientAdmin,
  _$employee,
]);

class _$RoleMeta {
  const _$RoleMeta();
  Role get platformAdmin => _$platformAdmin;
  Role get operatorAdmin => _$operatorAdmin;
  Role get supervisor => _$supervisor;
  Role get driver => _$driver;
  Role get clientAdmin => _$clientAdmin;
  Role get employee => _$employee;
  Role valueOf(String name) => _$valueOf(name);
  BuiltSet<Role> get values => _$values;
}

abstract class _$RoleMixin {
  // ignore: non_constant_identifier_names
  _$RoleMeta get Role => const _$RoleMeta();
}

Serializer<Role> _$roleSerializer = _$RoleSerializer();

class _$RoleSerializer implements PrimitiveSerializer<Role> {
  static const Map<String, Object> _toWire = const <String, Object>{
    'platformAdmin': 'platform_admin',
    'operatorAdmin': 'operator_admin',
    'supervisor': 'supervisor',
    'driver': 'driver',
    'clientAdmin': 'client_admin',
    'employee': 'employee',
  };
  static const Map<Object, String> _fromWire = const <Object, String>{
    'platform_admin': 'platformAdmin',
    'operator_admin': 'operatorAdmin',
    'supervisor': 'supervisor',
    'driver': 'driver',
    'client_admin': 'clientAdmin',
    'employee': 'employee',
  };

  @override
  final Iterable<Type> types = const <Type>[Role];
  @override
  final String wireName = 'Role';

  @override
  Object serialize(Serializers serializers, Role object,
          {FullType specifiedType = FullType.unspecified}) =>
      _toWire[object.name] ?? object.name;

  @override
  Role deserialize(Serializers serializers, Object serialized,
          {FullType specifiedType = FullType.unspecified}) =>
      Role.valueOf(
          _fromWire[serialized] ?? (serialized is String ? serialized : ''));
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
