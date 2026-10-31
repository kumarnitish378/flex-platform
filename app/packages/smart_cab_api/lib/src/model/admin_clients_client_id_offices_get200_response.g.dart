// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'admin_clients_client_id_offices_get200_response.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$AdminClientsClientIdOfficesGet200Response
    extends AdminClientsClientIdOfficesGet200Response {
  @override
  final BuiltList<Office> items;

  factory _$AdminClientsClientIdOfficesGet200Response(
          [void Function(AdminClientsClientIdOfficesGet200ResponseBuilder)?
              updates]) =>
      (AdminClientsClientIdOfficesGet200ResponseBuilder()..update(updates))
          ._build();

  _$AdminClientsClientIdOfficesGet200Response._({required this.items})
      : super._();
  @override
  AdminClientsClientIdOfficesGet200Response rebuild(
          void Function(AdminClientsClientIdOfficesGet200ResponseBuilder)
              updates) =>
      (toBuilder()..update(updates)).build();

  @override
  AdminClientsClientIdOfficesGet200ResponseBuilder toBuilder() =>
      AdminClientsClientIdOfficesGet200ResponseBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is AdminClientsClientIdOfficesGet200Response &&
        items == other.items;
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
    return (newBuiltValueToStringHelper(
            r'AdminClientsClientIdOfficesGet200Response')
          ..add('items', items))
        .toString();
  }
}

class AdminClientsClientIdOfficesGet200ResponseBuilder
    implements
        Builder<AdminClientsClientIdOfficesGet200Response,
            AdminClientsClientIdOfficesGet200ResponseBuilder> {
  _$AdminClientsClientIdOfficesGet200Response? _$v;

  ListBuilder<Office>? _items;
  ListBuilder<Office> get items => _$this._items ??= ListBuilder<Office>();
  set items(ListBuilder<Office>? items) => _$this._items = items;

  AdminClientsClientIdOfficesGet200ResponseBuilder() {
    AdminClientsClientIdOfficesGet200Response._defaults(this);
  }

  AdminClientsClientIdOfficesGet200ResponseBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _items = $v.items.toBuilder();
      _$v = null;
    }
    return this;
  }

  @override
  void replace(AdminClientsClientIdOfficesGet200Response other) {
    _$v = other as _$AdminClientsClientIdOfficesGet200Response;
  }

  @override
  void update(
      void Function(AdminClientsClientIdOfficesGet200ResponseBuilder)?
          updates) {
    if (updates != null) updates(this);
  }

  @override
  AdminClientsClientIdOfficesGet200Response build() => _build();

  _$AdminClientsClientIdOfficesGet200Response _build() {
    _$AdminClientsClientIdOfficesGet200Response _$result;
    try {
      _$result = _$v ??
          _$AdminClientsClientIdOfficesGet200Response._(
            items: items.build(),
          );
    } catch (_) {
      late String _$failedField;
      try {
        _$failedField = 'items';
        items.build();
      } catch (e) {
        throw BuiltValueNestedFieldError(
            r'AdminClientsClientIdOfficesGet200Response',
            _$failedField,
            e.toString());
      }
      rethrow;
    }
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
