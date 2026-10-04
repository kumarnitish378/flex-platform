// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'client_input.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

abstract class ClientInputBuilder {
  void replace(ClientInput other);
  void update(void Function(ClientInputBuilder) updates);
  String? get name;
  set name(String? name);

  String? get contactName;
  set contactName(String? contactName);

  String? get contactPhone;
  set contactPhone(String? contactPhone);
}

class _$$ClientInput extends $ClientInput {
  @override
  final String name;
  @override
  final String? contactName;
  @override
  final String? contactPhone;

  factory _$$ClientInput([void Function($ClientInputBuilder)? updates]) =>
      ($ClientInputBuilder()..update(updates))._build();

  _$$ClientInput._({required this.name, this.contactName, this.contactPhone})
      : super._();
  @override
  $ClientInput rebuild(void Function($ClientInputBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  $ClientInputBuilder toBuilder() => $ClientInputBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is $ClientInput &&
        name == other.name &&
        contactName == other.contactName &&
        contactPhone == other.contactPhone;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, name.hashCode);
    _$hash = $jc(_$hash, contactName.hashCode);
    _$hash = $jc(_$hash, contactPhone.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'$ClientInput')
          ..add('name', name)
          ..add('contactName', contactName)
          ..add('contactPhone', contactPhone))
        .toString();
  }
}

class $ClientInputBuilder
    implements Builder<$ClientInput, $ClientInputBuilder>, ClientInputBuilder {
  _$$ClientInput? _$v;

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

  $ClientInputBuilder() {
    $ClientInput._defaults(this);
  }

  $ClientInputBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _name = $v.name;
      _contactName = $v.contactName;
      _contactPhone = $v.contactPhone;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(covariant $ClientInput other) {
    _$v = other as _$$ClientInput;
  }

  @override
  void update(void Function($ClientInputBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  $ClientInput build() => _build();

  _$$ClientInput _build() {
    final _$result = _$v ??
        _$$ClientInput._(
          name: BuiltValueNullFieldError.checkNotNull(
              name, r'$ClientInput', 'name'),
          contactName: contactName,
          contactPhone: contactPhone,
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
