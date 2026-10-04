// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'office_input.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

abstract class OfficeInputBuilder {
  void replace(OfficeInput other);
  void update(void Function(OfficeInputBuilder) updates);
  String? get name;
  set name(String? name);

  LatLngBuilder get location;
  set location(LatLngBuilder? location);

  String? get addressText;
  set addressText(String? addressText);
}

class _$$OfficeInput extends $OfficeInput {
  @override
  final String name;
  @override
  final LatLng location;
  @override
  final String? addressText;

  factory _$$OfficeInput([void Function($OfficeInputBuilder)? updates]) =>
      ($OfficeInputBuilder()..update(updates))._build();

  _$$OfficeInput._(
      {required this.name, required this.location, this.addressText})
      : super._();
  @override
  $OfficeInput rebuild(void Function($OfficeInputBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  $OfficeInputBuilder toBuilder() => $OfficeInputBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is $OfficeInput &&
        name == other.name &&
        location == other.location &&
        addressText == other.addressText;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, name.hashCode);
    _$hash = $jc(_$hash, location.hashCode);
    _$hash = $jc(_$hash, addressText.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'$OfficeInput')
          ..add('name', name)
          ..add('location', location)
          ..add('addressText', addressText))
        .toString();
  }
}

class $OfficeInputBuilder
    implements Builder<$OfficeInput, $OfficeInputBuilder>, OfficeInputBuilder {
  _$$OfficeInput? _$v;

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

  $OfficeInputBuilder() {
    $OfficeInput._defaults(this);
  }

  $OfficeInputBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _name = $v.name;
      _location = $v.location.toBuilder();
      _addressText = $v.addressText;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(covariant $OfficeInput other) {
    _$v = other as _$$OfficeInput;
  }

  @override
  void update(void Function($OfficeInputBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  $OfficeInput build() => _build();

  _$$OfficeInput _build() {
    _$$OfficeInput _$result;
    try {
      _$result = _$v ??
          _$$OfficeInput._(
            name: BuiltValueNullFieldError.checkNotNull(
                name, r'$OfficeInput', 'name'),
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
            r'$OfficeInput', _$failedField, e.toString());
      }
      rethrow;
    }
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
