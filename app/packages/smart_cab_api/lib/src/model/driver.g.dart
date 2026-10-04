// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'driver.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$Driver extends Driver {
  @override
  final String? id;
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

  factory _$Driver([void Function(DriverBuilder)? updates]) =>
      (DriverBuilder()..update(updates))._build();

  _$Driver._(
      {this.id,
      required this.name,
      required this.phone,
      this.licenceLast4,
      this.defaultVehicleId,
      this.active})
      : super._();
  @override
  Driver rebuild(void Function(DriverBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  DriverBuilder toBuilder() => DriverBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is Driver &&
        id == other.id &&
        name == other.name &&
        phone == other.phone &&
        licenceLast4 == other.licenceLast4 &&
        defaultVehicleId == other.defaultVehicleId &&
        active == other.active;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, id.hashCode);
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
    return (newBuiltValueToStringHelper(r'Driver')
          ..add('id', id)
          ..add('name', name)
          ..add('phone', phone)
          ..add('licenceLast4', licenceLast4)
          ..add('defaultVehicleId', defaultVehicleId)
          ..add('active', active))
        .toString();
  }
}

class DriverBuilder
    implements Builder<Driver, DriverBuilder>, DriverInputBuilder {
  _$Driver? _$v;

  String? _id;
  String? get id => _$this._id;
  set id(covariant String? id) => _$this._id = id;

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

  DriverBuilder() {
    Driver._defaults(this);
  }

  DriverBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _id = $v.id;
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
  void replace(covariant Driver other) {
    _$v = other as _$Driver;
  }

  @override
  void update(void Function(DriverBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  Driver build() => _build();

  _$Driver _build() {
    final _$result = _$v ??
        _$Driver._(
          id: id,
          name: BuiltValueNullFieldError.checkNotNull(name, r'Driver', 'name'),
          phone:
              BuiltValueNullFieldError.checkNotNull(phone, r'Driver', 'phone'),
          licenceLast4: licenceLast4,
          defaultVehicleId: defaultVehicleId,
          active: active,
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
