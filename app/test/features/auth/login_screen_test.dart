import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_cab/core/session.dart';
import 'package:smart_cab/core/session_controller.dart';
import 'package:smart_cab/core/token_store.dart';
import 'package:smart_cab/data/api/auth_repository.dart';
import 'package:smart_cab/features/auth/login_screen.dart';
import 'package:smart_cab/l10n/app_localizations.dart';
import 'package:smart_cab_api/smart_cab_api.dart' as api;

void main() {
  Widget buildTestableWidget({
    required Widget child,
    AuthRepository? authRepository,
    TokenStore? tokenStore,
  }) {
    return ProviderScope(
      overrides: [
        authRepositoryProvider.overrideWithValue(
          authRepository ?? _FakeAuthRepository(),
        ),
        tokenStoreProvider.overrideWithValue(
          tokenStore ?? _FakeTokenStore(),
        ),
      ],
      child: MaterialApp(
        localizationsDelegates: AppText.localizationsDelegates,
        supportedLocales: AppText.supportedLocales,
        home: child,
      ),
    );
  }

  testWidgets('renders phone input stage by default with +91', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(
      buildTestableWidget(child: const LoginScreen()),
    );
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('C-02')), findsOneWidget);
    expect(find.byKey(const Key('phone-input')), findsOneWidget);
    expect(find.byKey(const Key('send-code')), findsOneWidget);
    expect(find.text('+91'), findsOneWidget);
  });

  testWidgets('requesting OTP transitions to code stage with resend countdown', (
    WidgetTester tester,
  ) async {
    final _FakeAuthRepository auth = _FakeAuthRepository();
    await tester.pumpWidget(
      buildTestableWidget(
        child: const LoginScreen(),
        authRepository: auth,
      ),
    );
    await tester.pumpAndSettle();

    await tester.enterText(find.byKey(const Key('phone-input')), '+919876543210');
    await tester.tap(find.byKey(const Key('send-code')));
    await tester.pumpAndSettle();

    expect(auth.requestedPhone, '+919876543210');
    expect(find.byKey(const Key('code-input')), findsOneWidget);
    expect(find.byKey(const Key('verify-code')), findsOneWidget);
    expect(find.byKey(const Key('resend-code')), findsOneWidget);
    expect(find.byKey(const Key('change-phone')), findsOneWidget);
  });

  testWidgets('refused OTP code shows single error message (OQ-24)', (
    WidgetTester tester,
  ) async {
    final _FakeAuthRepository auth = _FakeAuthRepository(shouldRejectCode: true);
    await tester.pumpWidget(
      buildTestableWidget(
        child: const LoginScreen(),
        authRepository: auth,
      ),
    );
    await tester.pumpAndSettle();

    // Move to code stage
    await tester.tap(find.byKey(const Key('send-code')));
    await tester.pumpAndSettle();

    // Submit invalid code
    await tester.enterText(find.byKey(const Key('code-input')), '123456');
    await tester.pump();
    await tester.tap(find.byKey(const Key('verify-code')));
    await tester.pump(const Duration(milliseconds: 100));

    expect(
      find.text('Invalid or expired code. Please try again.'),
      findsOneWidget,
    );
  });

  testWidgets('server network error shows connection error', (
    WidgetTester tester,
  ) async {
    final _FakeAuthRepository auth = _FakeAuthRepository(shouldFailNetwork: true);
    await tester.pumpWidget(
      buildTestableWidget(
        child: const LoginScreen(),
        authRepository: auth,
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('send-code')));
    await tester.pumpAndSettle();

    expect(
      find.text('Could not reach the server. Please check your connection.'),
      findsOneWidget,
    );
  });

  testWidgets('rate limit (429) shows too many requests message', (
    WidgetTester tester,
  ) async {
    final _FakeAuthRepository auth = _FakeAuthRepository(shouldRateLimit: true);
    await tester.pumpWidget(
      buildTestableWidget(
        child: const LoginScreen(),
        authRepository: auth,
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('send-code')));
    await tester.pumpAndSettle();

    expect(
      find.text('Too many requests. Please wait a moment.'),
      findsOneWidget,
    );
  });

  testWidgets('tapping change phone returns to phone step', (
    WidgetTester tester,
  ) async {
    final _FakeAuthRepository auth = _FakeAuthRepository();
    await tester.pumpWidget(
      buildTestableWidget(
        child: const LoginScreen(),
        authRepository: auth,
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('send-code')));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('code-input')), findsOneWidget);

    await tester.tap(find.byKey(const Key('change-phone')));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('phone-input')), findsOneWidget);
  });
}

class _FakeTokenStore implements TokenStore {
  StoredSession? session;

  @override
  Future<StoredSession?> read() async => session;

  @override
  Future<void> write(StoredSession session) async {
    this.session = session;
  }

  @override
  Future<void> clear() async {
    session = null;
  }
}

class _FakeAuthRepository implements AuthRepository {
  _FakeAuthRepository({
    this.shouldRejectCode = false,
    this.shouldFailNetwork = false,
    this.shouldRateLimit = false,
  });

  final bool shouldRejectCode;
  final bool shouldFailNetwork;
  final bool shouldRateLimit;

  String? requestedPhone;

  @override
  Future<void> requestCode(String phone) async {
    if (shouldRateLimit) {
      throw const AuthUnavailable('too_many_requests');
    }
    if (shouldFailNetwork) {
      throw const AuthUnavailable('network_error');
    }
    requestedPhone = phone;
  }

  @override
  Future<api.TokenPair> verifyCode({required String phone, required String code}) async {
    if (shouldRejectCode) {
      throw const OtpRejected();
    }
    if (shouldFailNetwork) {
      throw const AuthUnavailable('network_error');
    }
    return api.TokenPair(
      (api.TokenPairBuilder b) => b
        ..accessToken = 'fake-access'
        ..refreshToken = 'fake-refresh'
        ..expiresIn = 3600,
    );
  }

  @override
  Future<Identity?> me() async {
    return const Identity(
      userId: 'user-1',
      name: 'Test User',
      roles: <Role>[Role.employee],
    );
  }

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}
