// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'ride_requests_mine_get200_response.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$RideRequestsMineGet200Response extends RideRequestsMineGet200Response {
  @override
  final BuiltList<RideRequest>? items;
  @override
  final String? nextCursor;

  factory _$RideRequestsMineGet200Response(
          [void Function(RideRequestsMineGet200ResponseBuilder)? updates]) =>
      (RideRequestsMineGet200ResponseBuilder()..update(updates))._build();

  _$RideRequestsMineGet200Response._({this.items, this.nextCursor}) : super._();
  @override
  RideRequestsMineGet200Response rebuild(
          void Function(RideRequestsMineGet200ResponseBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  RideRequestsMineGet200ResponseBuilder toBuilder() =>
      RideRequestsMineGet200ResponseBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is RideRequestsMineGet200Response &&
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
    return (newBuiltValueToStringHelper(r'RideRequestsMineGet200Response')
          ..add('items', items)
          ..add('nextCursor', nextCursor))
        .toString();
  }
}

class RideRequestsMineGet200ResponseBuilder
    implements
        Builder<RideRequestsMineGet200Response,
            RideRequestsMineGet200ResponseBuilder> {
  _$RideRequestsMineGet200Response? _$v;

  ListBuilder<RideRequest>? _items;
  ListBuilder<RideRequest> get items =>
      _$this._items ??= ListBuilder<RideRequest>();
  set items(ListBuilder<RideRequest>? items) => _$this._items = items;

  String? _nextCursor;
  String? get nextCursor => _$this._nextCursor;
  set nextCursor(String? nextCursor) => _$this._nextCursor = nextCursor;

  RideRequestsMineGet200ResponseBuilder() {
    RideRequestsMineGet200Response._defaults(this);
  }

  RideRequestsMineGet200ResponseBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _items = $v.items?.toBuilder();
      _nextCursor = $v.nextCursor;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(RideRequestsMineGet200Response other) {
    _$v = other as _$RideRequestsMineGet200Response;
  }

  @override
  void update(void Function(RideRequestsMineGet200ResponseBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  RideRequestsMineGet200Response build() => _build();

  _$RideRequestsMineGet200Response _build() {
    _$RideRequestsMineGet200Response _$result;
    try {
      _$result = _$v ??
          _$RideRequestsMineGet200Response._(
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
            r'RideRequestsMineGet200Response', _$failedField, e.toString());
      }
      rethrow;
    }
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
