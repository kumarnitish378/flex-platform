// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'request_hint.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$RequestHint extends RequestHint {
  @override
  final String? requestId;
  @override
  final String? vehicleId;
  @override
  final String? tripId;
  @override
  final BuiltList<String>? riderOrder;
  @override
  final num? pickupEtaMinutes;
  @override
  final num? cost;
  @override
  final BuiltList<String>? reasons;
  @override
  final DateTime? createdAt;

  factory _$RequestHint([void Function(RequestHintBuilder)? updates]) =>
      (RequestHintBuilder()..update(updates))._build();

  _$RequestHint._(
      {this.requestId,
      this.vehicleId,
      this.tripId,
      this.riderOrder,
      this.pickupEtaMinutes,
      this.cost,
      this.reasons,
      this.createdAt})
      : super._();
  @override
  RequestHint rebuild(void Function(RequestHintBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  RequestHintBuilder toBuilder() => RequestHintBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is RequestHint &&
        requestId == other.requestId &&
        vehicleId == other.vehicleId &&
        tripId == other.tripId &&
        riderOrder == other.riderOrder &&
        pickupEtaMinutes == other.pickupEtaMinutes &&
        cost == other.cost &&
        reasons == other.reasons &&
        createdAt == other.createdAt;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, requestId.hashCode);
    _$hash = $jc(_$hash, vehicleId.hashCode);
    _$hash = $jc(_$hash, tripId.hashCode);
    _$hash = $jc(_$hash, riderOrder.hashCode);
    _$hash = $jc(_$hash, pickupEtaMinutes.hashCode);
    _$hash = $jc(_$hash, cost.hashCode);
    _$hash = $jc(_$hash, reasons.hashCode);
    _$hash = $jc(_$hash, createdAt.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'RequestHint')
          ..add('requestId', requestId)
          ..add('vehicleId', vehicleId)
          ..add('tripId', tripId)
          ..add('riderOrder', riderOrder)
          ..add('pickupEtaMinutes', pickupEtaMinutes)
          ..add('cost', cost)
          ..add('reasons', reasons)
          ..add('createdAt', createdAt))
        .toString();
  }
}

class RequestHintBuilder implements Builder<RequestHint, RequestHintBuilder> {
  _$RequestHint? _$v;

  String? _requestId;
  String? get requestId => _$this._requestId;
  set requestId(String? requestId) => _$this._requestId = requestId;

  String? _vehicleId;
  String? get vehicleId => _$this._vehicleId;
  set vehicleId(String? vehicleId) => _$this._vehicleId = vehicleId;

  String? _tripId;
  String? get tripId => _$this._tripId;
  set tripId(String? tripId) => _$this._tripId = tripId;

  ListBuilder<String>? _riderOrder;
  ListBuilder<String> get riderOrder =>
      _$this._riderOrder ??= ListBuilder<String>();
  set riderOrder(ListBuilder<String>? riderOrder) =>
      _$this._riderOrder = riderOrder;

  num? _pickupEtaMinutes;
  num? get pickupEtaMinutes => _$this._pickupEtaMinutes;
  set pickupEtaMinutes(num? pickupEtaMinutes) =>
      _$this._pickupEtaMinutes = pickupEtaMinutes;

  num? _cost;
  num? get cost => _$this._cost;
  set cost(num? cost) => _$this._cost = cost;

  ListBuilder<String>? _reasons;
  ListBuilder<String> get reasons => _$this._reasons ??= ListBuilder<String>();
  set reasons(ListBuilder<String>? reasons) => _$this._reasons = reasons;

  DateTime? _createdAt;
  DateTime? get createdAt => _$this._createdAt;
  set createdAt(DateTime? createdAt) => _$this._createdAt = createdAt;

  RequestHintBuilder() {
    RequestHint._defaults(this);
  }

  RequestHintBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _requestId = $v.requestId;
      _vehicleId = $v.vehicleId;
      _tripId = $v.tripId;
      _riderOrder = $v.riderOrder?.toBuilder();
      _pickupEtaMinutes = $v.pickupEtaMinutes;
      _cost = $v.cost;
      _reasons = $v.reasons?.toBuilder();
      _createdAt = $v.createdAt;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(RequestHint other) {
    _$v = other as _$RequestHint;
  }

  @override
  void update(void Function(RequestHintBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  RequestHint build() => _build();

  _$RequestHint _build() {
    _$RequestHint _$result;
    try {
      _$result = _$v ??
          _$RequestHint._(
            requestId: requestId,
            vehicleId: vehicleId,
            tripId: tripId,
            riderOrder: _riderOrder?.build(),
            pickupEtaMinutes: pickupEtaMinutes,
            cost: cost,
            reasons: _reasons?.build(),
            createdAt: createdAt,
          );
    } catch (_) {
      late String _$failedField;
      try {
        _$failedField = 'riderOrder';
        _riderOrder?.build();

        _$failedField = 'reasons';
        _reasons?.build();
      } catch (e) {
        throw BuiltValueNestedFieldError(
            r'RequestHint', _$failedField, e.toString());
      }
      rethrow;
    }
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
