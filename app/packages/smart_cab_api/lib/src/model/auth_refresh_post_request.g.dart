// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'auth_refresh_post_request.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$AuthRefreshPostRequest extends AuthRefreshPostRequest {
  @override
  final String refreshToken;

  factory _$AuthRefreshPostRequest(
          [void Function(AuthRefreshPostRequestBuilder)? updates]) =>
      (AuthRefreshPostRequestBuilder()..update(updates))._build();

  _$AuthRefreshPostRequest._({required this.refreshToken}) : super._();
  @override
  AuthRefreshPostRequest rebuild(
          void Function(AuthRefreshPostRequestBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  AuthRefreshPostRequestBuilder toBuilder() =>
      AuthRefreshPostRequestBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is AuthRefreshPostRequest &&
        refreshToken == other.refreshToken;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, refreshToken.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'AuthRefreshPostRequest')
          ..add('refreshToken', refreshToken))
        .toString();
  }
}

class AuthRefreshPostRequestBuilder
    implements Builder<AuthRefreshPostRequest, AuthRefreshPostRequestBuilder> {
  _$AuthRefreshPostRequest? _$v;

  String? _refreshToken;
  String? get refreshToken => _$this._refreshToken;
  set refreshToken(String? refreshToken) => _$this._refreshToken = refreshToken;

  AuthRefreshPostRequestBuilder() {
    AuthRefreshPostRequest._defaults(this);
  }

  AuthRefreshPostRequestBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _refreshToken = $v.refreshToken;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(AuthRefreshPostRequest other) {
    _$v = other as _$AuthRefreshPostRequest;
  }

  @override
  void update(void Function(AuthRefreshPostRequestBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  AuthRefreshPostRequest build() => _build();

  _$AuthRefreshPostRequest _build() {
    final _$result = _$v ??
        _$AuthRefreshPostRequest._(
          refreshToken: BuiltValueNullFieldError.checkNotNull(
              refreshToken, r'AuthRefreshPostRequest', 'refreshToken'),
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
