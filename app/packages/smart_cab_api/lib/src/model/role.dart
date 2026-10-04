//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_collection/built_collection.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'role.g.dart';

class Role extends EnumClass {

  @BuiltValueEnumConst(wireName: r'platform_admin')
  static const Role platformAdmin = _$platformAdmin;
  @BuiltValueEnumConst(wireName: r'operator_admin')
  static const Role operatorAdmin = _$operatorAdmin;
  @BuiltValueEnumConst(wireName: r'supervisor')
  static const Role supervisor = _$supervisor;
  @BuiltValueEnumConst(wireName: r'driver')
  static const Role driver = _$driver;
  @BuiltValueEnumConst(wireName: r'client_admin')
  static const Role clientAdmin = _$clientAdmin;
  @BuiltValueEnumConst(wireName: r'employee')
  static const Role employee = _$employee;

  static Serializer<Role> get serializer => _$roleSerializer;

  const Role._(String name): super(name);

  static BuiltSet<Role> get values => _$values;
  static Role valueOf(String name) => _$valueOf(name);
}

/// Optionally, enum_class can generate a mixin to go with your enum for use
/// with Angular. It exposes your enum constants as getters. So, if you mix it
/// in to your Dart component class, the values become available to the
/// corresponding Angular template.
///
/// Trigger mixin generation by writing a line like this one next to your enum.
abstract class RoleMixin = Object with _$RoleMixin;

