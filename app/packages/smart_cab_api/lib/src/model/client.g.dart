// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'client.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$Client extends Client {
  @override
  final String? id;
  @override
  final String name;
  @override
  final String? contactName;
  @override
  final String? contactPhone;

  factory _$Client([void Function(ClientBuilder)? updates]) =>
      (ClientBuilder()..update(updates))._build();

  _$Client._({this.id, required this.name, this.contactName, this.contactPhone})
      : super._();
  @override
  Client rebuild(void Function(ClientBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  ClientBuilder toBuilder() => ClientBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is Client &&
        id == other.id &&
        name == other.name &&
        contactName == other.contactName &&
        contactPhone == other.contactPhone;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, id.hashCode);
    _$hash = $jc(_$hash, name.hashCode);
    _$hash = $jc(_$hash, contactName.hashCode);
    _$hash = $jc(_$hash, contactPhone.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'Client')
          ..add('id', id)
          ..add('name', name)
          ..add('contactName', contactName)
          ..add('contactPhone', contactPhone))
        .toString();
  }
}

class ClientBuilder
    implements Builder<Client, ClientBuilder>, ClientInputBuilder {
  _$Client? _$v;

  String? _id;
  String? get id => _$this._id;
  set id(covariant String? id) => _$this._id = id;

  String? _name;
  String? get name => _$this._name;
  set name(covariant String? name) => _$this._name = name;

  String? _contactName;
  String? get contactName => _$this._contactName;
  set contactName(covariant String? contactName) =>
      _$this._contactName = contactName;

  String? _contactPhone;
  String? get contactPhone => _$this._contactPhone;
  set contactPhone(covariant String? contactPhone) =>
      _$this._contactPhone = contactPhone;

  ClientBuilder() {
    Client._defaults(this);
  }

  ClientBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _id = $v.id;
      _name = $v.name;
      _contactName = $v.contactName;
      _contactPhone = $v.contactPhone;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(covariant Client other) {
    _$v = other as _$Client;
  }

  @override
  void update(void Function(ClientBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  Client build() => _build();

  _$Client _build() {
    final _$result = _$v ??
        _$Client._(
          id: id,
          name: BuiltValueNullFieldError.checkNotNull(name, r'Client', 'name'),
          contactName: contactName,
          contactPhone: contactPhone,
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
