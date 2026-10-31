// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'dispatch_vehicles_get200_response.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$DispatchVehiclesGet200Response extends DispatchVehiclesGet200Response {
  @override
  final BuiltList<VehicleLive> items;

  factory _$DispatchVehiclesGet200Response(
          [void Function(DispatchVehiclesGet200ResponseBuilder)? updates]) =>
      (DispatchVehiclesGet200ResponseBuilder()..update(updates))._build();

  _$DispatchVehiclesGet200Response._({required this.items}) : super._();
  @override
  DispatchVehiclesGet200Response rebuild(
          void Function(DispatchVehiclesGet200ResponseBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  DispatchVehiclesGet200ResponseBuilder toBuilder() =>
      DispatchVehiclesGet200ResponseBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is DispatchVehiclesGet200Response && items == other.items;
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
    return (newBuiltValueToStringHelper(r'DispatchVehiclesGet200Response')
          ..add('items', items))
        .toString();
  }
}

class DispatchVehiclesGet200ResponseBuilder
    implements
        Builder<DispatchVehiclesGet200Response,
            DispatchVehiclesGet200ResponseBuilder> {
  _$DispatchVehiclesGet200Response? _$v;

  ListBuilder<VehicleLive>? _items;
  ListBuilder<VehicleLive> get items =>
      _$this._items ??= ListBuilder<VehicleLive>();
  set items(ListBuilder<VehicleLive>? items) => _$this._items = items;

  DispatchVehiclesGet200ResponseBuilder() {
    DispatchVehiclesGet200Response._defaults(this);
  }

  DispatchVehiclesGet200ResponseBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _items = $v.items.toBuilder();
      _$v = null;
    }
    return this;
  }

  @override
  void replace(DispatchVehiclesGet200Response other) {
    _$v = other as _$DispatchVehiclesGet200Response;
  }

  @override
  void update(void Function(DispatchVehiclesGet200ResponseBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  DispatchVehiclesGet200Response build() => _build();

  _$DispatchVehiclesGet200Response _build() {
    _$DispatchVehiclesGet200Response _$result;
    try {
      _$result = _$v ??
          _$DispatchVehiclesGet200Response._(
            items: items.build(),
          );
    } catch (_) {
      late String _$failedField;
      try {
        _$failedField = 'items';
        items.build();
      } catch (e) {
        throw BuiltValueNestedFieldError(
            r'DispatchVehiclesGet200Response', _$failedField, e.toString());
      }
      rethrow;
    }
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
