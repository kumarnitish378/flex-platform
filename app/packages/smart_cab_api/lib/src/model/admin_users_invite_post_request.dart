//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//

// ignore_for_file: unused_element
import 'package:built_collection/built_collection.dart';
import 'package:built_value/built_value.dart';
import 'package:built_value/serializer.dart';

part 'admin_users_invite_post_request.g.dart';

/// AdminUsersInvitePostRequest
///
/// Properties:
/// * [phone] 
/// * [name] 
/// * [role] 
/// * [clientId] 
@BuiltValue()
abstract class AdminUsersInvitePostRequest implements Built<AdminUsersInvitePostRequest, AdminUsersInvitePostRequestBuilder> {
  @BuiltValueField(wireName: r'phone')
  String get phone;

  @BuiltValueField(wireName: r'name')
  String get name;

  @BuiltValueField(wireName: r'role')
  AdminUsersInvitePostRequestRoleEnum get role;
  // enum roleEnum {  supervisor,  client_admin,  operator_admin,  };

  @BuiltValueField(wireName: r'client_id')
  String? get clientId;

  AdminUsersInvitePostRequest._();

  factory AdminUsersInvitePostRequest([void updates(AdminUsersInvitePostRequestBuilder b)]) = _$AdminUsersInvitePostRequest;

  @BuiltValueHook(initializeBuilder: true)
  static void _defaults(AdminUsersInvitePostRequestBuilder b) => b;

  @BuiltValueSerializer(custom: true)
  static Serializer<AdminUsersInvitePostRequest> get serializer => _$AdminUsersInvitePostRequestSerializer();
}

class _$AdminUsersInvitePostRequestSerializer implements PrimitiveSerializer<AdminUsersInvitePostRequest> {
  @override
  final Iterable<Type> types = const [AdminUsersInvitePostRequest, _$AdminUsersInvitePostRequest];

  @override
  final String wireName = r'AdminUsersInvitePostRequest';

  Iterable<Object?> _serializeProperties(
    Serializers serializers,
    AdminUsersInvitePostRequest object, {
    FullType specifiedType = FullType.unspecified,
  }) sync* {
    yield r'phone';
    yield serializers.serialize(
      object.phone,
      specifiedType: const FullType(String),
    );
    yield r'name';
    yield serializers.serialize(
      object.name,
      specifiedType: const FullType(String),
    );
    yield r'role';
    yield serializers.serialize(
      object.role,
      specifiedType: const FullType(AdminUsersInvitePostRequestRoleEnum),
    );
    if (object.clientId != null) {
      yield r'client_id';
      yield serializers.serialize(
        object.clientId,
        specifiedType: const FullType.nullable(String),
      );
    }
  }

  @override
  Object serialize(
    Serializers serializers,
    AdminUsersInvitePostRequest object, {
    FullType specifiedType = FullType.unspecified,
  }) {
    return _serializeProperties(serializers, object, specifiedType: specifiedType).toList();
  }

  void _deserializeProperties(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
    required List<Object?> serializedList,
    required AdminUsersInvitePostRequestBuilder result,
    required List<Object?> unhandled,
  }) {
    for (var i = 0; i < serializedList.length; i += 2) {
      final key = serializedList[i] as String;
      final value = serializedList[i + 1];
      switch (key) {
        case r'phone':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.phone = valueDes;
          break;
        case r'name':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(String),
          ) as String;
          result.name = valueDes;
          break;
        case r'role':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType(AdminUsersInvitePostRequestRoleEnum),
          ) as AdminUsersInvitePostRequestRoleEnum;
          result.role = valueDes;
          break;
        case r'client_id':
          final valueDes = serializers.deserialize(
            value,
            specifiedType: const FullType.nullable(String),
          ) as String?;
          if (valueDes == null) continue;
          result.clientId = valueDes;
          break;
        default:
          unhandled.add(key);
          unhandled.add(value);
          break;
      }
    }
  }

  @override
  AdminUsersInvitePostRequest deserialize(
    Serializers serializers,
    Object serialized, {
    FullType specifiedType = FullType.unspecified,
  }) {
    final result = AdminUsersInvitePostRequestBuilder();
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

class AdminUsersInvitePostRequestRoleEnum extends EnumClass {

  @BuiltValueEnumConst(wireName: r'supervisor')
  static const AdminUsersInvitePostRequestRoleEnum supervisor = _$adminUsersInvitePostRequestRoleEnum_supervisor;
  @BuiltValueEnumConst(wireName: r'client_admin')
  static const AdminUsersInvitePostRequestRoleEnum clientAdmin = _$adminUsersInvitePostRequestRoleEnum_clientAdmin;
  @BuiltValueEnumConst(wireName: r'operator_admin')
  static const AdminUsersInvitePostRequestRoleEnum operatorAdmin = _$adminUsersInvitePostRequestRoleEnum_operatorAdmin;

  static Serializer<AdminUsersInvitePostRequestRoleEnum> get serializer => _$adminUsersInvitePostRequestRoleEnumSerializer;

  const AdminUsersInvitePostRequestRoleEnum._(String name): super(name);

  static BuiltSet<AdminUsersInvitePostRequestRoleEnum> get values => _$adminUsersInvitePostRequestRoleEnumValues;
  static AdminUsersInvitePostRequestRoleEnum valueOf(String name) => _$adminUsersInvitePostRequestRoleEnumValueOf(name);
}

