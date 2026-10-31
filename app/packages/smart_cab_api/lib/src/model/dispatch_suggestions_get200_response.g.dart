// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'dispatch_suggestions_get200_response.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$DispatchSuggestionsGet200Response
    extends DispatchSuggestionsGet200Response {
  @override
  final BuiltList<Suggestion>? items;

  factory _$DispatchSuggestionsGet200Response(
          [void Function(DispatchSuggestionsGet200ResponseBuilder)? updates]) =>
      (DispatchSuggestionsGet200ResponseBuilder()..update(updates))._build();

  _$DispatchSuggestionsGet200Response._({this.items}) : super._();
  @override
  DispatchSuggestionsGet200Response rebuild(
          void Function(DispatchSuggestionsGet200ResponseBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  DispatchSuggestionsGet200ResponseBuilder toBuilder() =>
      DispatchSuggestionsGet200ResponseBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is DispatchSuggestionsGet200Response && items == other.items;
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
    return (newBuiltValueToStringHelper(r'DispatchSuggestionsGet200Response')
          ..add('items', items))
        .toString();
  }
}

class DispatchSuggestionsGet200ResponseBuilder
    implements
        Builder<DispatchSuggestionsGet200Response,
            DispatchSuggestionsGet200ResponseBuilder> {
  _$DispatchSuggestionsGet200Response? _$v;

  ListBuilder<Suggestion>? _items;
  ListBuilder<Suggestion> get items =>
      _$this._items ??= ListBuilder<Suggestion>();
  set items(ListBuilder<Suggestion>? items) => _$this._items = items;

  DispatchSuggestionsGet200ResponseBuilder() {
    DispatchSuggestionsGet200Response._defaults(this);
  }

  DispatchSuggestionsGet200ResponseBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _items = $v.items?.toBuilder();
      _$v = null;
    }
    return this;
  }

  @override
  void replace(DispatchSuggestionsGet200Response other) {
    _$v = other as _$DispatchSuggestionsGet200Response;
  }

  @override
  void update(
      void Function(DispatchSuggestionsGet200ResponseBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  DispatchSuggestionsGet200Response build() => _build();

  _$DispatchSuggestionsGet200Response _build() {
    _$DispatchSuggestionsGet200Response _$result;
    try {
      _$result = _$v ??
          _$DispatchSuggestionsGet200Response._(
            items: _items?.build(),
          );
    } catch (_) {
      late String _$failedField;
      try {
        _$failedField = 'items';
        _items?.build();
      } catch (e) {
        throw BuiltValueNestedFieldError(
            r'DispatchSuggestionsGet200Response', _$failedField, e.toString());
      }
      rethrow;
    }
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
