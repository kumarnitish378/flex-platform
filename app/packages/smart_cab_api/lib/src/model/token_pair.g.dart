// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'token_pair.dart';

// **************************************************************************
// BuiltValueGenerator
// **************************************************************************

class _$TokenPair extends TokenPair {
  @override
  final String accessToken;
  @override
  final String refreshToken;
  @override
  final int expiresIn;

  factory _$TokenPair([void Function(TokenPairBuilder)? updates]) =>
      (TokenPairBuilder()..update(updates))._build();

  _$TokenPair._(
      {required this.accessToken,
      required this.refreshToken,
      required this.expiresIn})
      : super._();
  @override
  TokenPair rebuild(void Function(TokenPairBuilder) updates) =>
      (toBuilder()..update(updates)).build();

  @override
  TokenPairBuilder toBuilder() => TokenPairBuilder()..replace(this);

  @override
  bool operator ==(Object other) {
    if (identical(other, this)) return true;
    return other is TokenPair &&
        accessToken == other.accessToken &&
        refreshToken == other.refreshToken &&
        expiresIn == other.expiresIn;
  }

  @override
  int get hashCode {
    var _$hash = 0;
    _$hash = $jc(_$hash, accessToken.hashCode);
    _$hash = $jc(_$hash, refreshToken.hashCode);
    _$hash = $jc(_$hash, expiresIn.hashCode);
    _$hash = $jf(_$hash);
    return _$hash;
  }

  @override
  String toString() {
    return (newBuiltValueToStringHelper(r'TokenPair')
          ..add('accessToken', accessToken)
          ..add('refreshToken', refreshToken)
          ..add('expiresIn', expiresIn))
        .toString();
  }
}

class TokenPairBuilder implements Builder<TokenPair, TokenPairBuilder> {
  _$TokenPair? _$v;

  String? _accessToken;
  String? get accessToken => _$this._accessToken;
  set accessToken(String? accessToken) => _$this._accessToken = accessToken;

  String? _refreshToken;
  String? get refreshToken => _$this._refreshToken;
  set refreshToken(String? refreshToken) => _$this._refreshToken = refreshToken;

  int? _expiresIn;
  int? get expiresIn => _$this._expiresIn;
  set expiresIn(int? expiresIn) => _$this._expiresIn = expiresIn;

  TokenPairBuilder() {
    TokenPair._defaults(this);
  }

  TokenPairBuilder get _$this {
    final $v = _$v;
    if ($v != null) {
      _accessToken = $v.accessToken;
      _refreshToken = $v.refreshToken;
      _expiresIn = $v.expiresIn;
      _$v = null;
    }
    return this;
  }

  @override
  void replace(TokenPair other) {
    _$v = other as _$TokenPair;
  }

  @override
  void update(void Function(TokenPairBuilder)? updates) {
    if (updates != null) updates(this);
  }

  @override
  TokenPair build() => _build();

  _$TokenPair _build() {
    final _$result = _$v ??
        _$TokenPair._(
          accessToken: BuiltValueNullFieldError.checkNotNull(
              accessToken, r'TokenPair', 'accessToken'),
          refreshToken: BuiltValueNullFieldError.checkNotNull(
              refreshToken, r'TokenPair', 'refreshToken'),
          expiresIn: BuiltValueNullFieldError.checkNotNull(
              expiresIn, r'TokenPair', 'expiresIn'),
        );
    replace(_$result);
    return _$result;
  }
}

// ignore_for_file: deprecated_member_use_from_same_package,type=lint
