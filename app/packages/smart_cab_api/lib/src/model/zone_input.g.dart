// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'zone_input.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

abstract class ZoneInputBuilder {
  void replace(ZoneInput other);
  void update(void Function(ZoneInputBuilder) updates);
  String? get name;
  set name(String? name);

  ListBuilder<LatLng> get boundary;
  set boundary(ListBuilder<LatLng>? boundary);

  bool? get active;
  set active(bool? active);
}

class _$$ZoneInput extends $ZoneInput {
  @override
  final String name;
  @override
  final BuiltList<LatLng> boundary;
  @override
  final bool? active;

  factory _$$ZoneInput([void Function($ZoneInputBuilder)? updates]) =>
      ($ZoneInputBuilder()..update(updates))._build();

  _$$ZoneInput._({required this.name, required this.boundary, this.active})
      : super._();
  @override
  $ZoneInput rebuild(void Function($ZoneInputBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  $ZoneInputBuilder toBuilder() => $ZoneInputBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is $ZoneInput &&
        name == other.name &&
        boundary == other.boundary &&
        active == other.active;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, name.hashCode);
    _$hash = $jc(_$hash, boundary.hashCode);
    _$hash = $jc(_$hash, active.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'$ZoneInput')
          ..add('name', name)
          ..add('boundary', boundary)
          ..add('active', active))
        .toString();
  }
}

class $ZoneInputBuilder
    implements Builder<$ZoneInput, $ZoneInputBuilder>, ZoneInputBuilder {
  _$$ZoneInput? _$v;

  String? _name;
  String? get name => _$this._name;
  set name(covariant String? name) => _$this._name = name;

  ListBuilder<LatLng>? _boundary;
  ListBuilder<LatLng> get boundary =>
      _$this._boundary ??= ListBuilder<LatLng>();
  set boundary(covariant ListBuilder<LatLng>? boundary) =>
      _$this._boundary = boundary;

  bool? _active;
  bool? get active => _$this._active;
  set active(covariant bool? active) => _$this._active = active;

  $ZoneInputBuilder() {
    $ZoneInput._defaults(this);
  }

  $ZoneInputBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _name = $v.name;
      _boundary = $v.boundary.toBuilder();
      _active = $v.active;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(covariant $ZoneInput other) {
    _$v = other as _$$ZoneInput;
  }

  @override
  void update(void Function($ZoneInputBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  $ZoneInput build() => _build();

  _$$ZoneInput _build() {
    _$$ZoneInput _$result;
    try {
      _$result = _$v ??
          _$$ZoneInput._(
            name: BuiltValueNullFieldError.checkNotNull(
                name, r'$ZoneInput', 'name'),
            boundary: boundary.build(),
            active: active,
          );
    } catch (_) {
      late String _$failedField;
      try {
        _$failedField = 'boundary';
        boundary.build();
      } catch (e) {
        throw BuiltValueNestedFieldError(
            r'$ZoneInput', _$failedField, e.toString());
      }
      rethrow;
    }
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
