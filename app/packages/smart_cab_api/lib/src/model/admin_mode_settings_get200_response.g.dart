// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'admin_mode_settings_get200_response.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$AdminModeSettingsGet200Response
    extends AdminModeSettingsGet200Response {
  @override
  final BuiltList<ModeSetting>? items;
  @override
  final BuiltList<BuiltList<String>>? overlapping;

  factory _$AdminModeSettingsGet200Response(
          [void Function(AdminModeSettingsGet200ResponseBuilder)? updates]) =>
      (AdminModeSettingsGet200ResponseBuilder()..update(updates))._build();

  _$AdminModeSettingsGet200Response._({this.items, this.overlapping})
      : super._();
  @override
  AdminModeSettingsGet200Response rebuild(
          void Function(AdminModeSettingsGet200ResponseBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  AdminModeSettingsGet200ResponseBuilder toBuilder() =>
      AdminModeSettingsGet200ResponseBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is AdminModeSettingsGet200Response &&
        items == other.items &&
        overlapping == other.overlapping;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, items.hashCode);
    _$hash = $jc(_$hash, overlapping.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'AdminModeSettingsGet200Response')
          ..add('items', items)
          ..add('overlapping', overlapping))
        .toString();
  }
}

class AdminModeSettingsGet200ResponseBuilder
    implements
        Builder<AdminModeSettingsGet200Response,
            AdminModeSettingsGet200ResponseBuilder> {
  _$AdminModeSettingsGet200Response? _$v;

  ListBuilder<ModeSetting>? _items;
  ListBuilder<ModeSetting> get items =>
      _$this._items ??= ListBuilder<ModeSetting>();
  set items(ListBuilder<ModeSetting>? items) => _$this._items = items;

  ListBuilder<BuiltList<String>>? _overlapping;
  ListBuilder<BuiltList<String>> get overlapping =>
      _$this._overlapping ??= ListBuilder<BuiltList<String>>();
  set overlapping(ListBuilder<BuiltList<String>>? overlapping) =>
      _$this._overlapping = overlapping;

  AdminModeSettingsGet200ResponseBuilder() {
    AdminModeSettingsGet200Response._defaults(this);
  }

  AdminModeSettingsGet200ResponseBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _items = $v.items?.toBuilder();
      _overlapping = $v.overlapping?.toBuilder();
      _$v = null;
    }
    return this;
  }

  @override
  void replace(AdminModeSettingsGet200Response other) {
    _$v = other as _$AdminModeSettingsGet200Response;
  }

  @override
  void update(void Function(AdminModeSettingsGet200ResponseBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  AdminModeSettingsGet200Response build() => _build();

  _$AdminModeSettingsGet200Response _build() {
    _$AdminModeSettingsGet200Response _$result;
    try {
      _$result = _$v ??
          _$AdminModeSettingsGet200Response._(
            items: _items?.build(),
            overlapping: _overlapping?.build(),
          );
    } catch (_) {
      late String _$failedField;
      try {
        _$failedField = 'items';
        _items?.build();
        _$failedField = 'overlapping';
        _overlapping?.build();
      } catch (e) {
        throw BuiltValueNestedFieldError(
            r'AdminModeSettingsGet200Response', _$failedField, e.toString());
      }
      rethrow;
    }
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
