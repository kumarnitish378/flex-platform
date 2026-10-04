// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'dispatch_trips_get200_response.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$DispatchTripsGet200Response extends DispatchTripsGet200Response {
  @override
  final BuiltList<Trip>? items;

  factory _$DispatchTripsGet200Response(
          [void Function(DispatchTripsGet200ResponseBuilder)? updates]) =>
      (DispatchTripsGet200ResponseBuilder()..update(updates))._build();

  _$DispatchTripsGet200Response._({this.items}) : super._();
  @override
  DispatchTripsGet200Response rebuild(
          void Function(DispatchTripsGet200ResponseBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  DispatchTripsGet200ResponseBuilder toBuilder() =>
      DispatchTripsGet200ResponseBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is DispatchTripsGet200Response && items == other.items;
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
    return (newBuiltValueToStringHelper(r'DispatchTripsGet200Response')
          ..add('items', items))
        .toString();
  }
}

class DispatchTripsGet200ResponseBuilder
    implements
        Builder<DispatchTripsGet200Response,
            DispatchTripsGet200ResponseBuilder> {
  _$DispatchTripsGet200Response? _$v;

  ListBuilder<Trip>? _items;
  ListBuilder<Trip> get items => _$this._items ??= ListBuilder<Trip>();
  set items(ListBuilder<Trip>? items) => _$this._items = items;

  DispatchTripsGet200ResponseBuilder() {
    DispatchTripsGet200Response._defaults(this);
  }

  DispatchTripsGet200ResponseBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _items = $v.items?.toBuilder();
      _$v = null;
    }
    return this;
  }

  @override
  void replace(DispatchTripsGet200Response other) {
    _$v = other as _$DispatchTripsGet200Response;
  }

  @override
  void update(void Function(DispatchTripsGet200ResponseBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  DispatchTripsGet200Response build() => _build();

  _$DispatchTripsGet200Response _build() {
    _$DispatchTripsGet200Response _$result;
    try {
      _$result = _$v ??
          _$DispatchTripsGet200Response._(
            items: _items?.build(),
          );
    } catch (_) {
      late String _$failedField;
      try {
        _$failedField = 'items';
        _items?.build();
      } catch (e) {
        throw BuiltValueNestedFieldError(
            r'DispatchTripsGet200Response', _$failedField, e.toString());
      }
      rethrow;
    }
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
