// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'zone.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$Zone extends Zone {
  @override
  final String? id;
  @override
  final int? employeeCount;
  @override
  final String name;
  @override
  final BuiltList<LatLng> boundary;
  @override
  final bool? active;

  factory _$Zone([void Function(ZoneBuilder)? updates]) =>
      (ZoneBuilder()..update(updates))._build();

  _$Zone._(
      {this.id,
      this.employeeCount,
      required this.name,
      required this.boundary,
      this.active})
      : super._();
  @override
  Zone rebuild(void Function(ZoneBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  ZoneBuilder toBuilder() => ZoneBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is Zone &&
        id == other.id &&
        employeeCount == other.employeeCount &&
        name == other.name &&
        boundary == other.boundary &&
        active == other.active;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, id.hashCode);
    _$hash = $jc(_$hash, employeeCount.hashCode);
    _$hash = $jc(_$hash, name.hashCode);
    _$hash = $jc(_$hash, boundary.hashCode);
    _$hash = $jc(_$hash, active.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'Zone')
          ..add('id', id)
          ..add('employeeCount', employeeCount)
          ..add('name', name)
          ..add('boundary', boundary)
          ..add('active', active))
        .toString();
  }
}

class ZoneBuilder implements Builder<Zone, ZoneBuilder>, ZoneInputBuilder {
  _$Zone? _$v;

  String? _id;
  String? get id => _$this._id;
  set id(covariant String? id) => _$this._id = id;

  int? _employeeCount;
  int? get employeeCount => _$this._employeeCount;
  set employeeCount(covariant int? employeeCount) =>
      _$this._employeeCount = employeeCount;

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

  ZoneBuilder() {
    Zone._defaults(this);
  }

  ZoneBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _id = $v.id;
      _employeeCount = $v.employeeCount;
      _name = $v.name;
      _boundary = $v.boundary.toBuilder();
      _active = $v.active;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(covariant Zone other) {
    _$v = other as _$Zone;
  }

  @override
  void update(void Function(ZoneBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  Zone build() => _build();

  _$Zone _build() {
    _$Zone _$result;
    try {
      _$result = _$v ??
          _$Zone._(
            id: id,
            employeeCount: employeeCount,
            name: BuiltValueNullFieldError.checkNotNull(name, r'Zone', 'name'),
            boundary: boundary.build(),
            active: active,
          );
    } catch (_) {
      late String _$failedField;
      try {
        _$failedField = 'boundary';
        boundary.build();
      } catch (e) {
        throw BuiltValueNestedFieldError(r'Zone', _$failedField, e.toString());
      }
      rethrow;
    }
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
