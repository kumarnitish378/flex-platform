// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'me_roles_inner.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$MeRolesInner extends MeRolesInner {
  @override
  final Role? role;
  @override
  final String? operatorId;
  @override
  final String? clientId;
  @override
  final String? employeeId;
  @override
  final String? driverId;
  @override
  final BuiltList<String>? permissions;

  factory _$MeRolesInner([void Function(MeRolesInnerBuilder)? updates]) =>
      (MeRolesInnerBuilder()..update(updates))._build();

  _$MeRolesInner._(
      {this.role,
      this.operatorId,
      this.clientId,
      this.employeeId,
      this.driverId,
      this.permissions})
      : super._();
  @override
  MeRolesInner rebuild(void Function(MeRolesInnerBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  MeRolesInnerBuilder toBuilder() => MeRolesInnerBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is MeRolesInner &&
        role == other.role &&
        operatorId == other.operatorId &&
        clientId == other.clientId &&
        employeeId == other.employeeId &&
        driverId == other.driverId &&
        permissions == other.permissions;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, role.hashCode);
    _$hash = $jc(_$hash, operatorId.hashCode);
    _$hash = $jc(_$hash, clientId.hashCode);
    _$hash = $jc(_$hash, employeeId.hashCode);
    _$hash = $jc(_$hash, driverId.hashCode);
    _$hash = $jc(_$hash, permissions.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'MeRolesInner')
          ..add('role', role)
          ..add('operatorId', operatorId)
          ..add('clientId', clientId)
          ..add('employeeId', employeeId)
          ..add('driverId', driverId)
          ..add('permissions', permissions))
        .toString();
  }
}

class MeRolesInnerBuilder
    implements Builder<MeRolesInner, MeRolesInnerBuilder> {
  _$MeRolesInner? _$v;

  Role? _role;
  Role? get role => _$this._role;
  set role(Role? role) => _$this._role = role;

  String? _operatorId;
  String? get operatorId => _$this._operatorId;
  set operatorId(String? operatorId) => _$this._operatorId = operatorId;

  String? _clientId;
  String? get clientId => _$this._clientId;
  set clientId(String? clientId) => _$this._clientId = clientId;

  String? _employeeId;
  String? get employeeId => _$this._employeeId;
  set employeeId(String? employeeId) => _$this._employeeId = employeeId;

  String? _driverId;
  String? get driverId => _$this._driverId;
  set driverId(String? driverId) => _$this._driverId = driverId;

  ListBuilder<String>? _permissions;
  ListBuilder<String> get permissions =>
      _$this._permissions ??= ListBuilder<String>();
  set permissions(ListBuilder<String>? permissions) =>
      _$this._permissions = permissions;

  MeRolesInnerBuilder() {
    MeRolesInner._defaults(this);
  }

  MeRolesInnerBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _role = $v.role;
      _operatorId = $v.operatorId;
      _clientId = $v.clientId;
      _employeeId = $v.employeeId;
      _driverId = $v.driverId;
      _permissions = $v.permissions?.toBuilder();
      _$v = null;
    }
    return this;
  }

  @override
  void replace(MeRolesInner other) {
    _$v = other as _$MeRolesInner;
  }

  @override
  void update(void Function(MeRolesInnerBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  MeRolesInner build() => _build();

  _$MeRolesInner _build() {
    _$MeRolesInner _$result;
    try {
      _$result = _$v ??
          _$MeRolesInner._(
            role: role,
            operatorId: operatorId,
            clientId: clientId,
            employeeId: employeeId,
            driverId: driverId,
            permissions: _permissions?.build(),
          );
    } catch (_) {
      late String _$failedField;
      try {
        _$failedField = 'permissions';
        _permissions?.build();
      } catch (e) {
        throw BuiltValueNestedFieldError(
            r'MeRolesInner', _$failedField, e.toString());
      }
      rethrow;
    }
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
