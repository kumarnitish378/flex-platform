// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'admin_users_invite_post_request.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

const AdminUsersInvitePostRequestRoleEnum
    _$adminUsersInvitePostRequestRoleEnum_supervisor =
    const AdminUsersInvitePostRequestRoleEnum._('supervisor');
const AdminUsersInvitePostRequestRoleEnum
    _$adminUsersInvitePostRequestRoleEnum_clientAdmin =
    const AdminUsersInvitePostRequestRoleEnum._('clientAdmin');
const AdminUsersInvitePostRequestRoleEnum
    _$adminUsersInvitePostRequestRoleEnum_operatorAdmin =
    const AdminUsersInvitePostRequestRoleEnum._('operatorAdmin');

AdminUsersInvitePostRequestRoleEnum
    _$adminUsersInvitePostRequestRoleEnumValueOf(String name) {
  switch (name) {
    case 'supervisor':
      return _$adminUsersInvitePostRequestRoleEnum_supervisor;
    case 'clientAdmin':
      return _$adminUsersInvitePostRequestRoleEnum_clientAdmin;
    case 'operatorAdmin':
      return _$adminUsersInvitePostRequestRoleEnum_operatorAdmin;
    default:
      throw ArgumentError(name);
  }
}

final BuiltSet<AdminUsersInvitePostRequestRoleEnum>
    _$adminUsersInvitePostRequestRoleEnumValues = BuiltSet<
        AdminUsersInvitePostRequestRoleEnum>(const <AdminUsersInvitePostRequestRoleEnum>[
  _$adminUsersInvitePostRequestRoleEnum_supervisor,
  _$adminUsersInvitePostRequestRoleEnum_clientAdmin,
  _$adminUsersInvitePostRequestRoleEnum_operatorAdmin,
]);

Serializer<AdminUsersInvitePostRequestRoleEnum>
    _$adminUsersInvitePostRequestRoleEnumSerializer =
    _$AdminUsersInvitePostRequestRoleEnumSerializer();

class _$AdminUsersInvitePostRequestRoleEnumSerializer
    implements PrimitiveSerializer<AdminUsersInvitePostRequestRoleEnum> {
  static const Map<String, Object> _toWire = const <String, Object>{
    'supervisor': 'supervisor',
    'clientAdmin': 'client_admin',
    'operatorAdmin': 'operator_admin',
  };
  static const Map<Object, String> _fromWire = const <Object, String>{
    'supervisor': 'supervisor',
    'client_admin': 'clientAdmin',
    'operator_admin': 'operatorAdmin',
  };

  @override
  final Iterable<Type> types = const <Type>[
    AdminUsersInvitePostRequestRoleEnum
  ];
  @override
  final String wireName = 'AdminUsersInvitePostRequestRoleEnum';

  @override
  Object serialize(
          Serializers serializers, AdminUsersInvitePostRequestRoleEnum object,
          {FullType specifiedType = FullType.unspecified}) =>
      _toWire[object.name] ?? object.name;

  @override
  AdminUsersInvitePostRequestRoleEnum deserialize(
          Serializers serializers, Object serialized,
          {FullType specifiedType = FullType.unspecified}) =>
      AdminUsersInvitePostRequestRoleEnum.valueOf(
          _fromWire[serialized] ?? (serialized is String ? serialized : ''));
}

class _$AdminUsersInvitePostRequest extends AdminUsersInvitePostRequest {
  @override
  final String phone;
  @override
  final String name;
  @override
  final AdminUsersInvitePostRequestRoleEnum role;
  @override
  final String? clientId;

  factory _$AdminUsersInvitePostRequest(
          [void Function(AdminUsersInvitePostRequestBuilder)? updates]) =>
      (AdminUsersInvitePostRequestBuilder()..update(updates))._build();

  _$AdminUsersInvitePostRequest._(
      {required this.phone,
      required this.name,
      required this.role,
      this.clientId})
      : super._();
  @override
  AdminUsersInvitePostRequest rebuild(
          void Function(AdminUsersInvitePostRequestBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  AdminUsersInvitePostRequestBuilder toBuilder() =>
      AdminUsersInvitePostRequestBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is AdminUsersInvitePostRequest &&
        phone == other.phone &&
        name == other.name &&
        role == other.role &&
        clientId == other.clientId;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, phone.hashCode);
    _$hash = $jc(_$hash, name.hashCode);
    _$hash = $jc(_$hash, role.hashCode);
    _$hash = $jc(_$hash, clientId.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'AdminUsersInvitePostRequest')
          ..add('phone', phone)
          ..add('name', name)
          ..add('role', role)
          ..add('clientId', clientId))
        .toString();
  }
}

class AdminUsersInvitePostRequestBuilder
    implements
        Builder<AdminUsersInvitePostRequest,
            AdminUsersInvitePostRequestBuilder> {
  _$AdminUsersInvitePostRequest? _$v;

  String? _phone;
  String? get phone => _$this._phone;
  set phone(String? phone) => _$this._phone = phone;

  String? _name;
  String? get name => _$this._name;
  set name(String? name) => _$this._name = name;

  AdminUsersInvitePostRequestRoleEnum? _role;
  AdminUsersInvitePostRequestRoleEnum? get role => _$this._role;
  set role(AdminUsersInvitePostRequestRoleEnum? role) => _$this._role = role;

  String? _clientId;
  String? get clientId => _$this._clientId;
  set clientId(String? clientId) => _$this._clientId = clientId;

  AdminUsersInvitePostRequestBuilder() {
    AdminUsersInvitePostRequest._defaults(this);
  }

  AdminUsersInvitePostRequestBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _phone = $v.phone;
      _name = $v.name;
      _role = $v.role;
      _clientId = $v.clientId;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(AdminUsersInvitePostRequest other) {
    _$v = other as _$AdminUsersInvitePostRequest;
  }

  @override
  void update(void Function(AdminUsersInvitePostRequestBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  AdminUsersInvitePostRequest build() => _build();

  _$AdminUsersInvitePostRequest _build() {
    final _$result = _$v ??
        _$AdminUsersInvitePostRequest._(
          phone: BuiltValueNullFieldError.checkNotNull(
              phone, r'AdminUsersInvitePostRequest', 'phone'),
          name: BuiltValueNullFieldError.checkNotNull(
              name, r'AdminUsersInvitePostRequest', 'name'),
          role: BuiltValueNullFieldError.checkNotNull(
              role, r'AdminUsersInvitePostRequest', 'role'),
          clientId: clientId,
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
