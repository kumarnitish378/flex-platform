// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'office.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$Office extends Office {
  @override
  final String? clientId;
  @override
  final String? id;
  @override
  final String name;
  @override
  final LatLng location;
  @override
  final String? addressText;

  factory _$Office([void Function(OfficeBuilder)? updates]) =>
      (OfficeBuilder()..update(updates))._build();

  _$Office._(
      {this.clientId,
      this.id,
      required this.name,
      required this.location,
      this.addressText})
      : super._();
  @override
  Office rebuild(void Function(OfficeBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  OfficeBuilder toBuilder() => OfficeBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is Office &&
        clientId == other.clientId &&
        id == other.id &&
        name == other.name &&
        location == other.location &&
        addressText == other.addressText;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, clientId.hashCode);
    _$hash = $jc(_$hash, id.hashCode);
    _$hash = $jc(_$hash, name.hashCode);
    _$hash = $jc(_$hash, location.hashCode);
    _$hash = $jc(_$hash, addressText.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'Office')
          ..add('clientId', clientId)
          ..add('id', id)
          ..add('name', name)
          ..add('location', location)
          ..add('addressText', addressText))
        .toString();
  }
}

class OfficeBuilder
    implements Builder<Office, OfficeBuilder>, OfficeInputBuilder {
  _$Office? _$v;

  String? _clientId;
  String? get clientId => _$this._clientId;
  set clientId(covariant String? clientId) => _$this._clientId = clientId;

  String? _id;
  String? get id => _$this._id;
  set id(covariant String? id) => _$this._id = id;

  String? _name;
  String? get name => _$this._name;
  set name(covariant String? name) => _$this._name = name;

  LatLngBuilder? _location;
  LatLngBuilder get location => _$this._location ??= LatLngBuilder();
  set location(covariant LatLngBuilder? location) =>
      _$this._location = location;

  String? _addressText;
  String? get addressText => _$this._addressText;
  set addressText(covariant String? addressText) =>
      _$this._addressText = addressText;

  OfficeBuilder() {
    Office._defaults(this);
  }

  OfficeBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _clientId = $v.clientId;
      _id = $v.id;
      _name = $v.name;
      _location = $v.location.toBuilder();
      _addressText = $v.addressText;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(covariant Office other) {
    _$v = other as _$Office;
  }

  @override
  void update(void Function(OfficeBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  Office build() => _build();

  _$Office _build() {
    _$Office _$result;
    try {
      _$result = _$v ??
          _$Office._(
            clientId: clientId,
            id: id,
            name:
                BuiltValueNullFieldError.checkNotNull(name, r'Office', 'name'),
            location: location.build(),
            addressText: addressText,
          );
    } catch (_) {
      late String _$failedField;
      try {
        _$failedField = 'location';
        location.build();
      } catch (e) {
        throw BuiltValueNestedFieldError(
            r'Office', _$failedField, e.toString());
      }
      rethrow;
    }
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
