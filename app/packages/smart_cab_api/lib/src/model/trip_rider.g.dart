// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'trip_rider.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$TripRider extends TripRider {
  @override
  final String? requestId;
  @override
  final String? riderFirstName;
  @override
  final num? addedMinutes;

  factory _$TripRider([void Function(TripRiderBuilder)? updates]) =>
      (TripRiderBuilder()..update(updates))._build();

  _$TripRider._({this.requestId, this.riderFirstName, this.addedMinutes})
      : super._();
  @override
  TripRider rebuild(void Function(TripRiderBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  TripRiderBuilder toBuilder() => TripRiderBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is TripRider &&
        requestId == other.requestId &&
        riderFirstName == other.riderFirstName &&
        addedMinutes == other.addedMinutes;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, requestId.hashCode);
    _$hash = $jc(_$hash, riderFirstName.hashCode);
    _$hash = $jc(_$hash, addedMinutes.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'TripRider')
          ..add('requestId', requestId)
          ..add('riderFirstName', riderFirstName)
          ..add('addedMinutes', addedMinutes))
        .toString();
  }
}

class TripRiderBuilder implements Builder<TripRider, TripRiderBuilder> {
  _$TripRider? _$v;

  String? _requestId;
  String? get requestId => _$this._requestId;
  set requestId(String? requestId) => _$this._requestId = requestId;

  String? _riderFirstName;
  String? get riderFirstName => _$this._riderFirstName;
  set riderFirstName(String? riderFirstName) =>
      _$this._riderFirstName = riderFirstName;

  num? _addedMinutes;
  num? get addedMinutes => _$this._addedMinutes;
  set addedMinutes(num? addedMinutes) => _$this._addedMinutes = addedMinutes;

  TripRiderBuilder() {
    TripRider._defaults(this);
  }

  TripRiderBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _requestId = $v.requestId;
      _riderFirstName = $v.riderFirstName;
      _addedMinutes = $v.addedMinutes;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(TripRider other) {
    _$v = other as _$TripRider;
  }

  @override
  void update(void Function(TripRiderBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  TripRider build() => _build();

  _$TripRider _build() {
    final _$result = _$v ??
        _$TripRider._(
          requestId: requestId,
          riderFirstName: riderFirstName,
          addedMinutes: addedMinutes,
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
