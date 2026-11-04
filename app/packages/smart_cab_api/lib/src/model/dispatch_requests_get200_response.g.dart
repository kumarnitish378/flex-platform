// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'dispatch_requests_get200_response.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$DispatchRequestsGet200Response extends DispatchRequestsGet200Response {
  @override
  final BuiltList<RideRequest> items;

  factory _$DispatchRequestsGet200Response(
          [void Function(DispatchRequestsGet200ResponseBuilder)? updates]) =>
      (DispatchRequestsGet200ResponseBuilder()..update(updates))._build();

  _$DispatchRequestsGet200Response._({required this.items}) : super._();
  @override
  DispatchRequestsGet200Response rebuild(
          void Function(DispatchRequestsGet200ResponseBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  DispatchRequestsGet200ResponseBuilder toBuilder() =>
      DispatchRequestsGet200ResponseBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is DispatchRequestsGet200Response && items == other.items;
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
    return (newBuiltValueToStringHelper(r'DispatchRequestsGet200Response')
          ..add('items', items))
        .toString();
  }
}

class DispatchRequestsGet200ResponseBuilder
    implements
        Builder<DispatchRequestsGet200Response,
            DispatchRequestsGet200ResponseBuilder> {
  _$DispatchRequestsGet200Response? _$v;

  ListBuilder<RideRequest>? _items;
  ListBuilder<RideRequest> get items =>
      _$this._items ??= ListBuilder<RideRequest>();
  set items(ListBuilder<RideRequest>? items) => _$this._items = items;

  DispatchRequestsGet200ResponseBuilder() {
    DispatchRequestsGet200Response._defaults(this);
  }

  DispatchRequestsGet200ResponseBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _items = $v.items.toBuilder();
      _$v = null;
    }
    return this;
  }

  @override
  void replace(DispatchRequestsGet200Response other) {
    _$v = other as _$DispatchRequestsGet200Response;
  }

  @override
  void update(void Function(DispatchRequestsGet200ResponseBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  DispatchRequestsGet200Response build() => _build();

  _$DispatchRequestsGet200Response _build() {
    _$DispatchRequestsGet200Response _$result;
    try {
      _$result = _$v ??
          _$DispatchRequestsGet200Response._(
            items: items.build(),
          );
    } catch (_) {
      late String _$failedField;
      try {
        _$failedField = 'items';
        items.build();
      } catch (e) {
        throw BuiltValueNestedFieldError(
            r'DispatchRequestsGet200Response', _$failedField, e.toString());
      }
      rethrow;
    }
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
