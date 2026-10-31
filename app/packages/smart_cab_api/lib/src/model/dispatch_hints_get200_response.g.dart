// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'dispatch_hints_get200_response.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$DispatchHintsGet200Response extends DispatchHintsGet200Response {
  @override
  final BuiltList<RequestHint> items;

  factory _$DispatchHintsGet200Response(
          [void Function(DispatchHintsGet200ResponseBuilder)? updates]) =>
      (DispatchHintsGet200ResponseBuilder()..update(updates))._build();

  _$DispatchHintsGet200Response._({required this.items}) : super._();
  @override
  DispatchHintsGet200Response rebuild(
          void Function(DispatchHintsGet200ResponseBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  DispatchHintsGet200ResponseBuilder toBuilder() =>
      DispatchHintsGet200ResponseBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is DispatchHintsGet200Response && items == other.items;
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
    return (newBuiltValueToStringHelper(r'DispatchHintsGet200Response')
          ..add('items', items))
        .toString();
  }
}

class DispatchHintsGet200ResponseBuilder
    implements
        Builder<DispatchHintsGet200Response,
            DispatchHintsGet200ResponseBuilder> {
  _$DispatchHintsGet200Response? _$v;

  ListBuilder<RequestHint>? _items;
  ListBuilder<RequestHint> get items =>
      _$this._items ??= ListBuilder<RequestHint>();
  set items(ListBuilder<RequestHint>? items) => _$this._items = items;

  DispatchHintsGet200ResponseBuilder() {
    DispatchHintsGet200Response._defaults(this);
  }

  DispatchHintsGet200ResponseBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _items = $v.items.toBuilder();
      _$v = null;
    }
    return this;
  }

  @override
  void replace(DispatchHintsGet200Response other) {
    _$v = other as _$DispatchHintsGet200Response;
  }

  @override
  void update(void Function(DispatchHintsGet200ResponseBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  DispatchHintsGet200Response build() => _build();

  _$DispatchHintsGet200Response _build() {
    _$DispatchHintsGet200Response _$result;
    try {
      _$result = _$v ??
          _$DispatchHintsGet200Response._(
            items: items.build(),
          );
    } catch (_) {
      late String _$failedField;
      try {
        _$failedField = 'items';
        items.build();
      } catch (e) {
        throw BuiltValueNestedFieldError(
            r'DispatchHintsGet200Response', _$failedField, e.toString());
      }
      rethrow;
    }
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
