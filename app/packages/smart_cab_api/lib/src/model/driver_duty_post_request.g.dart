// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'driver_duty_post_request.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$DriverDutyPostRequest extends DriverDutyPostRequest {
  @override
  final bool onDuty;
  @override
  final String? vehicleId;

  factory _$DriverDutyPostRequest(
          [void Function(DriverDutyPostRequestBuilder)? updates]) =>
      (DriverDutyPostRequestBuilder()..update(updates))._build();

  _$DriverDutyPostRequest._({required this.onDuty, this.vehicleId}) : super._();
  @override
  DriverDutyPostRequest rebuild(
          void Function(DriverDutyPostRequestBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  DriverDutyPostRequestBuilder toBuilder() =>
      DriverDutyPostRequestBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is DriverDutyPostRequest &&
        onDuty == other.onDuty &&
        vehicleId == other.vehicleId;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, onDuty.hashCode);
    _$hash = $jc(_$hash, vehicleId.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'DriverDutyPostRequest')
          ..add('onDuty', onDuty)
          ..add('vehicleId', vehicleId))
        .toString();
  }
}

class DriverDutyPostRequestBuilder
    implements Builder<DriverDutyPostRequest, DriverDutyPostRequestBuilder> {
  _$DriverDutyPostRequest? _$v;

  bool? _onDuty;
  bool? get onDuty => _$this._onDuty;
  set onDuty(bool? onDuty) => _$this._onDuty = onDuty;

  String? _vehicleId;
  String? get vehicleId => _$this._vehicleId;
  set vehicleId(String? vehicleId) => _$this._vehicleId = vehicleId;

  DriverDutyPostRequestBuilder() {
    DriverDutyPostRequest._defaults(this);
  }

  DriverDutyPostRequestBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _onDuty = $v.onDuty;
      _vehicleId = $v.vehicleId;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(DriverDutyPostRequest other) {
    _$v = other as _$DriverDutyPostRequest;
  }

  @override
  void update(void Function(DriverDutyPostRequestBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  DriverDutyPostRequest build() => _build();

  _$DriverDutyPostRequest _build() {
    final _$result = _$v ??
        _$DriverDutyPostRequest._(
          onDuty: BuiltValueNullFieldError.checkNotNull(
              onDuty, r'DriverDutyPostRequest', 'onDuty'),
          vehicleId: vehicleId,
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
