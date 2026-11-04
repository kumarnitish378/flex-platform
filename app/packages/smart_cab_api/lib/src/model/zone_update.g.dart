// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'zone_update.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$ZoneUpdate extends ZoneUpdate {
  @override
  final String? name;
  @override
  final BuiltList<LatLng>? boundary;
  @override
  final bool? active;

  factory _$ZoneUpdate([void Function(ZoneUpdateBuilder)? updates]) =>
      (ZoneUpdateBuilder()..update(updates))._build();

  _$ZoneUpdate._({this.name, this.boundary, this.active}) : super._();
  @override
  ZoneUpdate rebuild(void Function(ZoneUpdateBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  ZoneUpdateBuilder toBuilder() => ZoneUpdateBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is ZoneUpdate &&
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
    return (newBuiltValueToStringHelper(r'ZoneUpdate')
          ..add('name', name)
          ..add('boundary', boundary)
          ..add('active', active))
        .toString();
  }
}

class ZoneUpdateBuilder implements Builder<ZoneUpdate, ZoneUpdateBuilder> {
  _$ZoneUpdate? _$v;

  String? _name;
  String? get name => _$this._name;
  set name(String? name) => _$this._name = name;

  ListBuilder<LatLng>? _boundary;
  ListBuilder<LatLng> get boundary =>
      _$this._boundary ??= ListBuilder<LatLng>();
  set boundary(ListBuilder<LatLng>? boundary) => _$this._boundary = boundary;

  bool? _active;
  bool? get active => _$this._active;
  set active(bool? active) => _$this._active = active;

  ZoneUpdateBuilder() {
    ZoneUpdate._defaults(this);
  }

  ZoneUpdateBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _name = $v.name;
      _boundary = $v.boundary?.toBuilder();
      _active = $v.active;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(ZoneUpdate other) {
    _$v = other as _$ZoneUpdate;
  }

  @override
  void update(void Function(ZoneUpdateBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  ZoneUpdate build() => _build();

  _$ZoneUpdate _build() {
    _$ZoneUpdate _$result;
    try {
      _$result = _$v ??
          _$ZoneUpdate._(
            name: name,
            boundary: _boundary?.build(),
            active: active,
          );
    } catch (_) {
      late String _$failedField;
      try {
        _$failedField = 'boundary';
        _boundary?.build();
      } catch (e) {
        throw BuiltValueNestedFieldError(
            r'ZoneUpdate', _$failedField, e.toString());
      }
      rethrow;
    }
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
