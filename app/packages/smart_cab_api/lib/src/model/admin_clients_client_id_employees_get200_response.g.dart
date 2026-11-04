// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'admin_clients_client_id_employees_get200_response.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$AdminClientsClientIdEmployeesGet200Response
    extends AdminClientsClientIdEmployeesGet200Response {
  @override
  final BuiltList<Employee>? items;
  @override
  final String? nextCursor;

  factory _$AdminClientsClientIdEmployeesGet200Response(
          [void Function(AdminClientsClientIdEmployeesGet200ResponseBuilder)?
              updates]) =>
      (AdminClientsClientIdEmployeesGet200ResponseBuilder()..update(updates))
          ._build();

  _$AdminClientsClientIdEmployeesGet200Response._({this.items, this.nextCursor})
      : super._();
  @override
  AdminClientsClientIdEmployeesGet200Response rebuild(
          void Function(AdminClientsClientIdEmployeesGet200ResponseBuilder)
              updates) =>
      (toBuilder()..update(updates)).build();

  @override
  AdminClientsClientIdEmployeesGet200ResponseBuilder toBuilder() =>
      AdminClientsClientIdEmployeesGet200ResponseBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is AdminClientsClientIdEmployeesGet200Response &&
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
    return (newBuiltValueToStringHelper(
            r'AdminClientsClientIdEmployeesGet200Response')
          ..add('items', items)
          ..add('nextCursor', nextCursor))
        .toString();
  }
}

class AdminClientsClientIdEmployeesGet200ResponseBuilder
    implements
        Builder<AdminClientsClientIdEmployeesGet200Response,
            AdminClientsClientIdEmployeesGet200ResponseBuilder> {
  _$AdminClientsClientIdEmployeesGet200Response? _$v;

  ListBuilder<Employee>? _items;
  ListBuilder<Employee> get items => _$this._items ??= ListBuilder<Employee>();
  set items(ListBuilder<Employee>? items) => _$this._items = items;

  String? _nextCursor;
  String? get nextCursor => _$this._nextCursor;
  set nextCursor(String? nextCursor) => _$this._nextCursor = nextCursor;

  AdminClientsClientIdEmployeesGet200ResponseBuilder() {
    AdminClientsClientIdEmployeesGet200Response._defaults(this);
  }

  AdminClientsClientIdEmployeesGet200ResponseBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _items = $v.items?.toBuilder();
      _nextCursor = $v.nextCursor;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(AdminClientsClientIdEmployeesGet200Response other) {
    _$v = other as _$AdminClientsClientIdEmployeesGet200Response;
  }

  @override
  void update(
      void Function(AdminClientsClientIdEmployeesGet200ResponseBuilder)?
          updates) {
    if (updates != null) updates(this);
  }

  @override
  AdminClientsClientIdEmployeesGet200Response build() => _build();

  _$AdminClientsClientIdEmployeesGet200Response _build() {
    _$AdminClientsClientIdEmployeesGet200Response _$result;
    try {
      _$result = _$v ??
          _$AdminClientsClientIdEmployeesGet200Response._(
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
            r'AdminClientsClientIdEmployeesGet200Response',
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
