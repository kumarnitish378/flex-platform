// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'admin_clients_get200_response.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$AdminClientsGet200Response extends AdminClientsGet200Response {
  @override
  final BuiltList<Client> items;

  factory _$AdminClientsGet200Response(
          [void Function(AdminClientsGet200ResponseBuilder)? updates]) =>
      (AdminClientsGet200ResponseBuilder()..update(updates))._build();

  _$AdminClientsGet200Response._({required this.items}) : super._();
  @override
  AdminClientsGet200Response rebuild(
          void Function(AdminClientsGet200ResponseBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  AdminClientsGet200ResponseBuilder toBuilder() =>
      AdminClientsGet200ResponseBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is AdminClientsGet200Response && items == other.items;
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
    return (newBuiltValueToStringHelper(r'AdminClientsGet200Response')
          ..add('items', items))
        .toString();
  }
}

class AdminClientsGet200ResponseBuilder
    implements
        Builder<AdminClientsGet200Response, AdminClientsGet200ResponseBuilder> {
  _$AdminClientsGet200Response? _$v;

  ListBuilder<Client>? _items;
  ListBuilder<Client> get items => _$this._items ??= ListBuilder<Client>();
  set items(ListBuilder<Client>? items) => _$this._items = items;

  AdminClientsGet200ResponseBuilder() {
    AdminClientsGet200Response._defaults(this);
  }

  AdminClientsGet200ResponseBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _items = $v.items.toBuilder();
      _$v = null;
    }
    return this;
  }

  @override
  void replace(AdminClientsGet200Response other) {
    _$v = other as _$AdminClientsGet200Response;
  }

  @override
  void update(void Function(AdminClientsGet200ResponseBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  AdminClientsGet200Response build() => _build();

  _$AdminClientsGet200Response _build() {
    _$AdminClientsGet200Response _$result;
    try {
      _$result = _$v ??
          _$AdminClientsGet200Response._(
            items: items.build(),
          );
    } catch (_) {
      late String _$failedField;
      try {
        _$failedField = 'items';
        items.build();
      } catch (e) {
        throw BuiltValueNestedFieldError(
            r'AdminClientsGet200Response', _$failedField, e.toString());
      }
      rethrow;
    }
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
