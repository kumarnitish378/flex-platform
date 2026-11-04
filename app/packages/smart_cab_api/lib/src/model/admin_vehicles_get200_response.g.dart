// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'admin_vehicles_get200_response.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$AdminVehiclesGet200Response extends AdminVehiclesGet200Response {
  @override
  final BuiltList<Vehicle>? items;
  @override
  final String? nextCursor;

  factory _$AdminVehiclesGet200Response(
          [void Function(AdminVehiclesGet200ResponseBuilder)? updates]) =>
      (AdminVehiclesGet200ResponseBuilder()..update(updates))._build();

  _$AdminVehiclesGet200Response._({this.items, this.nextCursor}) : super._();
  @override
  AdminVehiclesGet200Response rebuild(
          void Function(AdminVehiclesGet200ResponseBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  AdminVehiclesGet200ResponseBuilder toBuilder() =>
      AdminVehiclesGet200ResponseBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is AdminVehiclesGet200Response &&
        items == other.items &&
        nextCursor == other.nextCursor;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, items.hashCode);
    _$hash = $jc(_$hash, nextCursor.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'AdminVehiclesGet200Response')
          ..add('items', items)
          ..add('nextCursor', nextCursor))
        .toString();
  }
}

class AdminVehiclesGet200ResponseBuilder
    implements
        Builder<AdminVehiclesGet200Response,
            AdminVehiclesGet200ResponseBuilder> {
  _$AdminVehiclesGet200Response? _$v;

  ListBuilder<Vehicle>? _items;
  ListBuilder<Vehicle> get items => _$this._items ??= ListBuilder<Vehicle>();
  set items(ListBuilder<Vehicle>? items) => _$this._items = items;

  String? _nextCursor;
  String? get nextCursor => _$this._nextCursor;
  set nextCursor(String? nextCursor) => _$this._nextCursor = nextCursor;

  AdminVehiclesGet200ResponseBuilder() {
    AdminVehiclesGet200Response._defaults(this);
  }

  AdminVehiclesGet200ResponseBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _items = $v.items?.toBuilder();
      _nextCursor = $v.nextCursor;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(AdminVehiclesGet200Response other) {
    _$v = other as _$AdminVehiclesGet200Response;
  }

  @override
  void update(void Function(AdminVehiclesGet200ResponseBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  AdminVehiclesGet200Response build() => _build();

  _$AdminVehiclesGet200Response _build() {
    _$AdminVehiclesGet200Response _$result;
    try {
      _$result = _$v ??
          _$AdminVehiclesGet200Response._(
            items: _items?.build(),
            nextCursor: nextCursor,
          );
    } catch (_) {
      late String _$failedField;
      try {
        _$failedField = 'items';
        _items?.build();
      } catch (e) {
        throw BuiltValueNestedFieldError(
            r'AdminVehiclesGet200Response', _$failedField, e.toString());
      }
      rethrow;
    }
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
