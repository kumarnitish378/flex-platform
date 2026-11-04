/// Puts the session on every request, and recovers from one expired token (A02).
///
/// Two headers, both required by the backend on every call:
///
/// * `Authorization: Bearer <access token>`.
/// * `X-Active-Role` - which of the caller's roles they are acting as. A person can hold
///   several (a supervisor who also rides to work), and the server authorises the role
///   they are *using*, not the best one they have (hard rule 3). Omitting it would let
///   the server pick, which is how a rider accidentally gets a supervisor's answer.
///
/// On a 401 it refreshes once and replays the request. Once, deliberately: a refresh
/// that itself 401s means the session is finished, and retrying in a loop turns an
/// expired login into a request storm against `/auth/refresh`.
library;

import 'dart:async';

import 'package:dio/dio.dart';


/// What the interceptor needs from the session. An interface rather than a Riverpod
/// dependency so it can be tested without a widget tree, and so `core/session.dart`
/// does not have to know about dio.
abstract class AuthTokens {
  /// The current access token, or `null` when nobody is signed in.
  String? get accessToken;

  /// The role the app is acting as, in the backend's spelling (`operator_admin`).
  String? get activeRole;

  /// Exchange the refresh token for a new access token.
  ///
  /// Returns the new access token, or `null` when the session cannot be recovered -
  /// which the caller turns into a sign-out rather than a retry.
  Future<String?> refresh();

  /// The session is over: clear it and send the person back to login.
  Future<void> onSessionLost();
}

class AuthInterceptor extends Interceptor {
  AuthInterceptor(this._tokens);

  final AuthTokens _tokens;

  /// Set while a refresh is in flight so several parallel 401s share one refresh
  /// instead of each firing their own. Five screens loading at once is normal.
  Future<String?>? _refreshing;

  /// Marks a request that has already been replayed, so it cannot be retried twice.
  static const String _retriedFlag = 'smart_cab_retried';

  /// Paths that must never carry a token or be retried: they are how a session is
  /// obtained in the first place, and a 401 from them is an answer, not an expiry.
  static bool _isAuthEndpoint(String path) =>
      path.contains('/auth/otp/') || path.contains('/auth/refresh');

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    if (!_isAuthEndpoint(options.path)) {
      final String? token = _tokens.accessToken;
      final String? role = _tokens.activeRole;
      if (token != null) {
        options.headers['Authorization'] = 'Bearer $token';
      }
      if (role != null) {
        options.headers['X-Active-Role'] = role;
      }
    }
    handler.next(options);
  }

  @override
  Future<void> onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    final RequestOptions request = err.requestOptions;
    final bool recoverable = err.response?.statusCode == 401 &&
        !_isAuthEndpoint(request.path) &&
        request.extra[_retriedFlag] != true;

    if (!recoverable) {
      handler.next(err);
      return;
    }

    final String? token = await (_refreshing ??= _refreshOnce());
    if (token == null) {
      await _tokens.onSessionLost();
      handler.next(err);
      return;
    }

    request.extra[_retriedFlag] = true;
    request.headers['Authorization'] = 'Bearer $token';
    try {
      final Response<dynamic> replayed = await Dio().fetch<dynamic>(request);
      handler.resolve(replayed);
    } on DioException catch (replayFailed) {
      handler.next(replayFailed);
    }
  }

  Future<String?> _refreshOnce() async {
    try {
      return await _tokens.refresh();
    } finally {
      // Cleared whatever happened, so the *next* 401 gets a fresh attempt rather than
      // the stale result of this one.
      _refreshing = null;
    }
  }
}
