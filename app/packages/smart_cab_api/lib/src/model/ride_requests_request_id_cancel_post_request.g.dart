// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'ride_requests_request_id_cancel_post_request.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$RideRequestsRequestIdCancelPostRequest
    extends RideRequestsRequestIdCancelPostRequest {
  @override
  final String? reason;

  factory _$RideRequestsRequestIdCancelPostRequest(
          [void Function(RideRequestsRequestIdCancelPostRequestBuilder)?
              updates]) =>
      (RideRequestsRequestIdCancelPostRequestBuilder()..update(updates))
          ._build();

  _$RideRequestsRequestIdCancelPostRequest._({this.reason}) : super._();
  @override
  RideRequestsRequestIdCancelPostRequest rebuild(
          void Function(RideRequestsRequestIdCancelPostRequestBuilder)
              updates) =>
      (toBuilder()..update(updates)).build();

  @override
  RideRequestsRequestIdCancelPostRequestBuilder toBuilder() =>
      RideRequestsRequestIdCancelPostRequestBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is RideRequestsRequestIdCancelPostRequest &&
        reason == other.reason;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, reason.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(
            r'RideRequestsRequestIdCancelPostRequest')
          ..add('reason', reason))
        .toString();
  }
}

class RideRequestsRequestIdCancelPostRequestBuilder
    implements
        Builder<RideRequestsRequestIdCancelPostRequest,
            RideRequestsRequestIdCancelPostRequestBuilder> {
  _$RideRequestsRequestIdCancelPostRequest? _$v;

  String? _reason;
  String? get reason => _$this._reason;
  set reason(String? reason) => _$this._reason = reason;

  RideRequestsRequestIdCancelPostRequestBuilder() {
    RideRequestsRequestIdCancelPostRequest._defaults(this);
  }

  RideRequestsRequestIdCancelPostRequestBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _reason = $v.reason;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(RideRequestsRequestIdCancelPostRequest other) {
    _$v = other as _$RideRequestsRequestIdCancelPostRequest;
  }

  @override
  void update(
      void Function(RideRequestsRequestIdCancelPostRequestBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  RideRequestsRequestIdCancelPostRequest build() => _build();

  _$RideRequestsRequestIdCancelPostRequest _build() {
    final _$result = _$v ??
        _$RideRequestsRequestIdCancelPostRequest._(
          reason: reason,
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
