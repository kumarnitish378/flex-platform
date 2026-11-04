// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'admin_zones_get200_response.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$AdminZonesGet200Response extends AdminZonesGet200Response {
  @override
  final BuiltList<Zone>? items;

  factory _$AdminZonesGet200Response(
          [void Function(AdminZonesGet200ResponseBuilder)? updates]) =>
      (AdminZonesGet200ResponseBuilder()..update(updates))._build();

  _$AdminZonesGet200Response._({this.items}) : super._();
  @override
  AdminZonesGet200Response rebuild(
          void Function(AdminZonesGet200ResponseBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  AdminZonesGet200ResponseBuilder toBuilder() =>
      AdminZonesGet200ResponseBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is AdminZonesGet200Response && items == other.items;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, items.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'AdminZonesGet200Response')
          ..add('items', items))
        .toString();
  }
}

class AdminZonesGet200ResponseBuilder
    implements
        Builder<AdminZonesGet200Response, AdminZonesGet200ResponseBuilder> {
  _$AdminZonesGet200Response? _$v;

  ListBuilder<Zone>? _items;
  ListBuilder<Zone> get items => _$this._items ??= ListBuilder<Zone>();
  set items(ListBuilder<Zone>? items) => _$this._items = items;

  AdminZonesGet200ResponseBuilder() {
    AdminZonesGet200Response._defaults(this);
  }

  AdminZonesGet200ResponseBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _items = $v.items?.toBuilder();
      _$v = null;
    }
    return this;
  }

  @override
  void replace(AdminZonesGet200Response other) {
    _$v = other as _$AdminZonesGet200Response;
  }

  @override
  void update(void Function(AdminZonesGet200ResponseBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  AdminZonesGet200Response build() => _build();

  _$AdminZonesGet200Response _build() {
    _$AdminZonesGet200Response _$result;
    try {
      _$result = _$v ??
          _$AdminZonesGet200Response._(
            items: _items?.build(),
          );
    } catch (_) {
      late String _$failedField;
      try {
        _$failedField = 'items';
        _items?.build();
      } catch (e) {
        throw BuiltValueNestedFieldError(
            r'AdminZonesGet200Response', _$failedField, e.toString());
      }
      rethrow;
    }
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
