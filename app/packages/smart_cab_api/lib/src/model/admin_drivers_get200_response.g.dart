// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'admin_drivers_get200_response.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$AdminDriversGet200Response extends AdminDriversGet200Response {
  @override
  final BuiltList<Driver>? items;
  @override
  final String? nextCursor;

  factory _$AdminDriversGet200Response(
          [void Function(AdminDriversGet200ResponseBuilder)? updates]) =>
      (AdminDriversGet200ResponseBuilder()..update(updates))._build();

  _$AdminDriversGet200Response._({this.items, this.nextCursor}) : super._();
  @override
  AdminDriversGet200Response rebuild(
          void Function(AdminDriversGet200ResponseBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  AdminDriversGet200ResponseBuilder toBuilder() =>
      AdminDriversGet200ResponseBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is AdminDriversGet200Response &&
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
    return (newBuiltValueToStringHelper(r'AdminDriversGet200Response')
          ..add('items', items)
          ..add('nextCursor', nextCursor))
        .toString();
  }
}

class AdminDriversGet200ResponseBuilder
    implements
        Builder<AdminDriversGet200Response, AdminDriversGet200ResponseBuilder> {
  _$AdminDriversGet200Response? _$v;

  ListBuilder<Driver>? _items;
  ListBuilder<Driver> get items => _$this._items ??= ListBuilder<Driver>();
  set items(ListBuilder<Driver>? items) => _$this._items = items;

  String? _nextCursor;
  String? get nextCursor => _$this._nextCursor;
  set nextCursor(String? nextCursor) => _$this._nextCursor = nextCursor;

  AdminDriversGet200ResponseBuilder() {
    AdminDriversGet200Response._defaults(this);
  }

  AdminDriversGet200ResponseBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _items = $v.items?.toBuilder();
      _nextCursor = $v.nextCursor;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(AdminDriversGet200Response other) {
    _$v = other as _$AdminDriversGet200Response;
  }

  @override
  void update(void Function(AdminDriversGet200ResponseBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  AdminDriversGet200Response build() => _build();

  _$AdminDriversGet200Response _build() {
    _$AdminDriversGet200Response _$result;
    try {
      _$result = _$v ??
          _$AdminDriversGet200Response._(
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
            r'AdminDriversGet200Response', _$failedField, e.toString());
      }
      rethrow;
    }
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
