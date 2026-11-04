// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'simctl_optimizer_put_request.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$SimctlOptimizerPutRequest extends SimctlOptimizerPutRequest {
  @override
  final bool available;

  factory _$SimctlOptimizerPutRequest(
          [void Function(SimctlOptimizerPutRequestBuilder)? updates]) =>
      (SimctlOptimizerPutRequestBuilder()..update(updates))._build();

  _$SimctlOptimizerPutRequest._({required this.available}) : super._();
  @override
  SimctlOptimizerPutRequest rebuild(
          void Function(SimctlOptimizerPutRequestBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  SimctlOptimizerPutRequestBuilder toBuilder() =>
      SimctlOptimizerPutRequestBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is SimctlOptimizerPutRequest && available == other.available;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, available.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'SimctlOptimizerPutRequest')
          ..add('available', available))
        .toString();
  }
}

class SimctlOptimizerPutRequestBuilder
    implements
        Builder<SimctlOptimizerPutRequest, SimctlOptimizerPutRequestBuilder> {
  _$SimctlOptimizerPutRequest? _$v;

  bool? _available;
  bool? get available => _$this._available;
  set available(bool? available) => _$this._available = available;

  SimctlOptimizerPutRequestBuilder() {
    SimctlOptimizerPutRequest._defaults(this);
  }

  SimctlOptimizerPutRequestBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _available = $v.available;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(SimctlOptimizerPutRequest other) {
    _$v = other as _$SimctlOptimizerPutRequest;
  }

  @override
  void update(void Function(SimctlOptimizerPutRequestBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  SimctlOptimizerPutRequest build() => _build();

  _$SimctlOptimizerPutRequest _build() {
    final _$result = _$v ??
        _$SimctlOptimizerPutRequest._(
          available: BuiltValueNullFieldError.checkNotNull(
              available, r'SimctlOptimizerPutRequest', 'available'),
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
