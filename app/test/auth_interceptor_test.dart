import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_cab/data/api/auth_interceptor.dart';

/// The auth interceptor (A02's "interceptor unit-tested").
///
/// Worth testing directly rather than through a screen: every single call in the app
/// goes through it, and the failure modes are all invisible. A missing `X-Active-Role`
/// gets the wrong authorisation; a retry loop turns one expired token into a storm
/// against `/auth/refresh`; and a token attached to the OTP endpoints would send a
/// stale credential to the one place that must not trust it.
void main() {
  group('headers on the way out', () {
    test('a signed-in call carries the token and the active role', () {
      final _Tokens tokens = _Tokens(accessToken: 'abc', activeRole: 'supervisor');
      final RequestOptions options = _request('/dispatch/requests');

      AuthInterceptor(tokens).onRequest(options, _CaptureRequest());

      expect(options.headers['Authorization'], 'Bearer abc');
      expect(options.headers['X-Active-Role'], 'supervisor');
    });

    test('the role is the backend spelling, not camelCase', () {
      final _Tokens tokens = _Tokens(accessToken: 'abc', activeRole: 'operator_admin');
      final RequestOptions options = _request('/admin/vehicles');

      AuthInterceptor(tokens).onRequest(options, _CaptureRequest());

      expect(options.headers['X-Active-Role'], 'operator_admin');
    });

    test('a signed-out call carries neither', () {
      final RequestOptions options = _request('/ride-requests');

      AuthInterceptor(_Tokens()).onRequest(options, _CaptureRequest());

      expect(options.headers.containsKey('Authorization'), isFalse);
      expect(options.headers.containsKey('X-Active-Role'), isFalse);
    });

    test('the OTP endpoints are never given a token', () {
      // They are how a session is obtained. Sending a stale credential to the one
      // endpoint that must not trust it is how a logged-out person stays logged in.
      final _Tokens tokens = _Tokens(accessToken: 'stale', activeRole: 'employee');
      final AuthInterceptor interceptor = AuthInterceptor(tokens);

      for (final String path in <String>[
        '/auth/otp/request',
        '/auth/otp/verify',
        '/auth/refresh',
      ]) {
        final RequestOptions options = _request(path);
        interceptor.onRequest(options, _CaptureRequest());
        expect(
          options.headers.containsKey('Authorization'),
          isFalse,
          reason: '$path must not carry a token',
        );
      }
    });
  });

  group('a 401 is refreshed once', () {
    test('a refusal that is not a 401 is passed straight through', () async {
      final _Tokens tokens = _Tokens(accessToken: 'abc', activeRole: 'driver');
      final _CaptureError handler = _CaptureError();

      await AuthInterceptor(tokens).onError(_error('/driver/trips', 403), handler);

      expect(tokens.refreshCalls, 0, reason: 'a 403 is an answer, not an expiry');
      expect(handler.passedThrough, isTrue);
    });

    test('a 401 from the refresh endpoint does not refresh again', () async {
      final _Tokens tokens = _Tokens(accessToken: 'abc', activeRole: 'driver');
      final _CaptureError handler = _CaptureError();

      await AuthInterceptor(tokens).onError(_error('/auth/refresh', 401), handler);

      expect(tokens.refreshCalls, 0, reason: 'that is the loop this guards against');
      expect(handler.passedThrough, isTrue);
    });

    test('a failed refresh ends the session instead of retrying', () async {
      final _Tokens tokens = _Tokens(
        accessToken: 'expired',
        activeRole: 'employee',
        refreshResult: null,
      );
      final _CaptureError handler = _CaptureError();

      await AuthInterceptor(tokens).onError(_error('/ride-requests', 401), handler);

      expect(tokens.refreshCalls, 1);
      expect(tokens.sessionLost, isTrue);
      expect(handler.passedThrough, isTrue, reason: 'the caller still sees the failure');
    });

    test('a request already replayed is not replayed again', () async {
      final _Tokens tokens = _Tokens(accessToken: 'abc', activeRole: 'employee');
      final _CaptureError handler = _CaptureError();
      final DioException second = _error('/ride-requests', 401, retried: true);

      await AuthInterceptor(tokens).onError(second, handler);

      expect(tokens.refreshCalls, 0, reason: 'one retry, then give up');
      expect(handler.passedThrough, isTrue);
    });

    test('several parallel 401s share one refresh', () async {
      // Five screens load at once, all with the same expired token. Five refreshes
      // would race, and four of them would be using a refresh token the first one had
      // already rotated.
      final _Tokens tokens = _Tokens(
        accessToken: 'expired',
        activeRole: 'employee',
        refreshResult: null,
        refreshDelay: const Duration(milliseconds: 20),
      );
      final AuthInterceptor interceptor = AuthInterceptor(tokens);

      await Future.wait<void>(<Future<void>>[
        for (int i = 0; i < 5; i++)
          interceptor.onError(_error('/ride-requests', 401), _CaptureError()),
      ]);

      expect(tokens.refreshCalls, 1);
    });
  });
}

RequestOptions _request(String path) => RequestOptions(path: path, baseUrl: 'http://x/api/v1');

DioException _error(String path, int status, {bool retried = false}) {
  final RequestOptions options = _request(path);
  if (retried) {
    options.extra['smart_cab_retried'] = true;
  }
  return DioException(
    requestOptions: options,
    response: Response<dynamic>(requestOptions: options, statusCode: status),
    type: DioExceptionType.badResponse,
  );
}

class _Tokens implements AuthTokens {
  _Tokens({
    this.accessToken,
    this.activeRole,
    this.refreshResult,
    this.refreshDelay = Duration.zero,
  });

  @override
  String? accessToken;

  @override
  String? activeRole;

  final String? refreshResult;
  final Duration refreshDelay;

  int refreshCalls = 0;
  bool sessionLost = false;

  @override
  Future<String?> refresh() async {
    refreshCalls++;
    if (refreshDelay != Duration.zero) {
      await Future<void>.delayed(refreshDelay);
    }
    return refreshResult;
  }

  @override
  Future<void> onSessionLost() async {
    sessionLost = true;
  }
}

class _CaptureRequest extends RequestInterceptorHandler {}

class _CaptureError extends ErrorInterceptorHandler {
  bool passedThrough = false;

  @override
  void next(DioException err) {
    passedThrough = true;
  }
}
