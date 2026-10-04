// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'driver_input.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

abstract class DriverInputBuilder {
  void replace(DriverInput other);
  void update(void Function(DriverInputBuilder) updates);
  String? get name;
  set name(String? name);

  String? get phone;
  set phone(String? phone);

  String? get licenceLast4;
  set licenceLast4(String? licenceLast4);

  String? get defaultVehicleId;
  set defaultVehicleId(String? defaultVehicleId);

  bool? get active;
  set active(bool? active);
}

class _$$DriverInput extends $DriverInput {
  @override
  final String name;
  @override
  final String phone;
  @override
  final String? licenceLast4;
  @override
  final String? defaultVehicleId;
  @override
  final bool? active;

  factory _$$DriverInput([void Function($DriverInputBuilder)? updates]) =>
      ($DriverInputBuilder()..update(updates))._build();

  _$$DriverInput._(
      {required this.name,
      required this.phone,
      this.licenceLast4,
      this.defaultVehicleId,
      this.active})
      : super._();
  @override
  $DriverInput rebuild(void Function($DriverInputBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  $DriverInputBuilder toBuilder() => $DriverInputBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is $DriverInput &&
        name == other.name &&
        phone == other.phone &&
        licenceLast4 == other.licenceLast4 &&
        defaultVehicleId == other.defaultVehicleId &&
        active == other.active;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, name.hashCode);
    _$hash = $jc(_$hash, phone.hashCode);
    _$hash = $jc(_$hash, licenceLast4.hashCode);
    _$hash = $jc(_$hash, defaultVehicleId.hashCode);
    _$hash = $jc(_$hash, active.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'$DriverInput')
          ..add('name', name)
          ..add('phone', phone)
          ..add('licenceLast4', licenceLast4)
          ..add('defaultVehicleId', defaultVehicleId)
          ..add('active', active))
        .toString();
  }
}

class $DriverInputBuilder
    implements Builder<$DriverInput, $DriverInputBuilder>, DriverInputBuilder {
  _$$DriverInput? _$v;

  String? _name;
  String? get name => _$this._name;
  set name(covariant String? name) => _$this._name = name;

  String? _phone;
  String? get phone => _$this._phone;
  set phone(covariant String? phone) => _$this._phone = phone;

  String? _licenceLast4;
  String? get licenceLast4 => _$this._licenceLast4;
  set licenceLast4(covariant String? licenceLast4) =>
      _$this._licenceLast4 = licenceLast4;

  String? _defaultVehicleId;
  String? get defaultVehicleId => _$this._defaultVehicleId;
  set defaultVehicleId(covariant String? defaultVehicleId) =>
      _$this._defaultVehicleId = defaultVehicleId;

  bool? _active;
  bool? get active => _$this._active;
  set active(covariant bool? active) => _$this._active = active;

  $DriverInputBuilder() {
    $DriverInput._defaults(this);
  }

  $DriverInputBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _name = $v.name;
      _phone = $v.phone;
      _licenceLast4 = $v.licenceLast4;
      _defaultVehicleId = $v.defaultVehicleId;
      _active = $v.active;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(covariant $DriverInput other) {
    _$v = other as _$$DriverInput;
  }

  @override
  void update(void Function($DriverInputBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  $DriverInput build() => _build();

  _$$DriverInput _build() {
    final _$result = _$v ??
        _$$DriverInput._(
          name: BuiltValueNullFieldError.checkNotNull(
              name, r'$DriverInput', 'name'),
          phone: BuiltValueNullFieldError.checkNotNull(
              phone, r'$DriverInput', 'phone'),
          licenceLast4: licenceLast4,
          defaultVehicleId: defaultVehicleId,
          active: active,
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
