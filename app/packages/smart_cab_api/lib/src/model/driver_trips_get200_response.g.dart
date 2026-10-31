// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'driver_trips_get200_response.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$DriverTripsGet200Response extends DriverTripsGet200Response {
  @override
  final BuiltList<Trip> items;

  factory _$DriverTripsGet200Response(
          [void Function(DriverTripsGet200ResponseBuilder)? updates]) =>
      (DriverTripsGet200ResponseBuilder()..update(updates))._build();

  _$DriverTripsGet200Response._({required this.items}) : super._();
  @override
  DriverTripsGet200Response rebuild(
          void Function(DriverTripsGet200ResponseBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  DriverTripsGet200ResponseBuilder toBuilder() =>
      DriverTripsGet200ResponseBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is DriverTripsGet200Response && items == other.items;
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
    return (newBuiltValueToStringHelper(r'DriverTripsGet200Response')
          ..add('items', items))
        .toString();
  }
}

class DriverTripsGet200ResponseBuilder
    implements
        Builder<DriverTripsGet200Response, DriverTripsGet200ResponseBuilder> {
  _$DriverTripsGet200Response? _$v;

  ListBuilder<Trip>? _items;
  ListBuilder<Trip> get items => _$this._items ??= ListBuilder<Trip>();
  set items(ListBuilder<Trip>? items) => _$this._items = items;

  DriverTripsGet200ResponseBuilder() {
    DriverTripsGet200Response._defaults(this);
  }

  DriverTripsGet200ResponseBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _items = $v.items.toBuilder();
      _$v = null;
    }
    return this;
  }

  @override
  void replace(DriverTripsGet200Response other) {
    _$v = other as _$DriverTripsGet200Response;
  }

  @override
  void update(void Function(DriverTripsGet200ResponseBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  DriverTripsGet200Response build() => _build();

  _$DriverTripsGet200Response _build() {
    _$DriverTripsGet200Response _$result;
    try {
      _$result = _$v ??
          _$DriverTripsGet200Response._(
            items: items.build(),
          );
    } catch (_) {
      late String _$failedField;
      try {
        _$failedField = 'items';
        items.build();
      } catch (e) {
        throw BuiltValueNestedFieldError(
            r'DriverTripsGet200Response', _$failedField, e.toString());
      }
      rethrow;
    }
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
