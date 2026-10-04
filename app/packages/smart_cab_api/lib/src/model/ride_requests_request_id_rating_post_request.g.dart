// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'ride_requests_request_id_rating_post_request.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$RideRequestsRequestIdRatingPostRequest
    extends RideRequestsRequestIdRatingPostRequest {
  @override
  final int rating;
  @override
  final String? comment;

  factory _$RideRequestsRequestIdRatingPostRequest(
          [void Function(RideRequestsRequestIdRatingPostRequestBuilder)?
              updates]) =>
      (RideRequestsRequestIdRatingPostRequestBuilder()..update(updates))
          ._build();

  _$RideRequestsRequestIdRatingPostRequest._(
      {required this.rating, this.comment})
      : super._();
  @override
  RideRequestsRequestIdRatingPostRequest rebuild(
          void Function(RideRequestsRequestIdRatingPostRequestBuilder)
              updates) =>
      (toBuilder()..update(updates)).build();

  @override
  RideRequestsRequestIdRatingPostRequestBuilder toBuilder() =>
      RideRequestsRequestIdRatingPostRequestBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is RideRequestsRequestIdRatingPostRequest &&
        rating == other.rating &&
        comment == other.comment;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, rating.hashCode);
    _$hash = $jc(_$hash, comment.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(
            r'RideRequestsRequestIdRatingPostRequest')
          ..add('rating', rating)
          ..add('comment', comment))
        .toString();
  }
}

class RideRequestsRequestIdRatingPostRequestBuilder
    implements
        Builder<RideRequestsRequestIdRatingPostRequest,
            RideRequestsRequestIdRatingPostRequestBuilder> {
  _$RideRequestsRequestIdRatingPostRequest? _$v;

  int? _rating;
  int? get rating => _$this._rating;
  set rating(int? rating) => _$this._rating = rating;

  String? _comment;
  String? get comment => _$this._comment;
  set comment(String? comment) => _$this._comment = comment;

  RideRequestsRequestIdRatingPostRequestBuilder() {
    RideRequestsRequestIdRatingPostRequest._defaults(this);
  }

  RideRequestsRequestIdRatingPostRequestBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _rating = $v.rating;
      _comment = $v.comment;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(RideRequestsRequestIdRatingPostRequest other) {
    _$v = other as _$RideRequestsRequestIdRatingPostRequest;
  }

  @override
  void update(
      void Function(RideRequestsRequestIdRatingPostRequestBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  RideRequestsRequestIdRatingPostRequest build() => _build();

  _$RideRequestsRequestIdRatingPostRequest _build() {
    final _$result = _$v ??
        _$RideRequestsRequestIdRatingPostRequest._(
          rating: BuiltValueNullFieldError.checkNotNull(
              rating, r'RideRequestsRequestIdRatingPostRequest', 'rating'),
          comment: comment,
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
