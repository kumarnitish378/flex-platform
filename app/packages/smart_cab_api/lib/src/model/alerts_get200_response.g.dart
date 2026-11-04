// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'alerts_get200_response.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$AlertsGet200Response extends AlertsGet200Response {
  @override
  final BuiltList<Alert> items;

  factory _$AlertsGet200Response(
          [void Function(AlertsGet200ResponseBuilder)? updates]) =>
      (AlertsGet200ResponseBuilder()..update(updates))._build();

  _$AlertsGet200Response._({required this.items}) : super._();
  @override
  AlertsGet200Response rebuild(
          void Function(AlertsGet200ResponseBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  AlertsGet200ResponseBuilder toBuilder() =>
      AlertsGet200ResponseBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is AlertsGet200Response && items == other.items;
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
    return (newBuiltValueToStringHelper(r'AlertsGet200Response')
          ..add('items', items))
        .toString();
  }
}

class AlertsGet200ResponseBuilder
    implements Builder<AlertsGet200Response, AlertsGet200ResponseBuilder> {
  _$AlertsGet200Response? _$v;

  ListBuilder<Alert>? _items;
  ListBuilder<Alert> get items => _$this._items ??= ListBuilder<Alert>();
  set items(ListBuilder<Alert>? items) => _$this._items = items;

  AlertsGet200ResponseBuilder() {
    AlertsGet200Response._defaults(this);
  }

  AlertsGet200ResponseBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _items = $v.items.toBuilder();
      _$v = null;
    }
    return this;
  }

  @override
  void replace(AlertsGet200Response other) {
    _$v = other as _$AlertsGet200Response;
  }

  @override
  void update(void Function(AlertsGet200ResponseBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  AlertsGet200Response build() => _build();

  _$AlertsGet200Response _build() {
    _$AlertsGet200Response _$result;
    try {
      _$result = _$v ??
          _$AlertsGet200Response._(
            items: items.build(),
          );
    } catch (_) {
      late String _$failedField;
      try {
        _$failedField = 'items';
        items.build();
      } catch (e) {
        throw BuiltValueNestedFieldError(
            r'AlertsGet200Response', _$failedField, e.toString());
      }
      rethrow;
    }
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
