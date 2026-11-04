// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'me.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$Me extends Me {
  @override
  final String? userId;
  @override
  final String? name;
  @override
  final String? phone;
  @override
  final BuiltList<MeRolesInner>? roles;

  factory _$Me([void Function(MeBuilder)? updates]) =>
      (MeBuilder()..update(updates))._build();

  _$Me._({this.userId, this.name, this.phone, this.roles}) : super._();
  @override
  Me rebuild(void Function(MeBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  MeBuilder toBuilder() => MeBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is Me &&
        userId == other.userId &&
        name == other.name &&
        phone == other.phone &&
        roles == other.roles;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, userId.hashCode);
    _$hash = $jc(_$hash, name.hashCode);
    _$hash = $jc(_$hash, phone.hashCode);
    _$hash = $jc(_$hash, roles.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'Me')
          ..add('userId', userId)
          ..add('name', name)
          ..add('phone', phone)
          ..add('roles', roles))
        .toString();
  }
}

class MeBuilder implements Builder<Me, MeBuilder> {
  _$Me? _$v;

  String? _userId;
  String? get userId => _$this._userId;
  set userId(String? userId) => _$this._userId = userId;

  String? _name;
  String? get name => _$this._name;
  set name(String? name) => _$this._name = name;

  String? _phone;
  String? get phone => _$this._phone;
  set phone(String? phone) => _$this._phone = phone;

  ListBuilder<MeRolesInner>? _roles;
  ListBuilder<MeRolesInner> get roles =>
      _$this._roles ??= ListBuilder<MeRolesInner>();
  set roles(ListBuilder<MeRolesInner>? roles) => _$this._roles = roles;

  MeBuilder() {
    Me._defaults(this);
  }

  MeBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _userId = $v.userId;
      _name = $v.name;
      _phone = $v.phone;
      _roles = $v.roles?.toBuilder();
      _$v = null;
    }
    return this;
  }

  @override
  void replace(Me other) {
    _$v = other as _$Me;
  }

  @override
  void update(void Function(MeBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  Me build() => _build();

  _$Me _build() {
    _$Me _$result;
    try {
      _$result = _$v ??
          _$Me._(
            userId: userId,
            name: name,
            phone: phone,
            roles: _roles?.build(),
          );
    } catch (_) {
      late String _$failedField;
      try {
        _$failedField = 'roles';
        _roles?.build();
      } catch (e) {
        throw BuiltValueNestedFieldError(r'Me', _$failedField, e.toString());
      }
      rethrow;
    }
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
