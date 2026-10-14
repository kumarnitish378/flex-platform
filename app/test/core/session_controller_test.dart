import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_cab/core/session.dart';
import 'package:smart_cab/core/session_controller.dart';
import 'package:smart_cab/core/token_store.dart';
import 'package:smart_cab/data/api/auth_repository.dart';
import 'package:smart_cab_api/smart_cab_api.dart' as api;

void main() {
  late ProviderContainer container;
  late _TestAuthRepository authRepo;
  late _TestTokenStore tokenStore;

  setUp(() {
    authRepo = _TestAuthRepository();
    tokenStore = _TestTokenStore();

    container = ProviderContainer(
      overrides: [
        authRepositoryProvider.overrideWithValue(authRepo),
        tokenStoreProvider.overrideWithValue(tokenStore),
      ],
    );
  });

  tearDown(() {
    container.dispose();
  });

  group('SessionController restore', () {
    test('restore with empty token store leaves session signed out', () async {
      await container.read(sessionControllerProvider.notifier).restore();

      final Session session = container.read(sessionProvider);
      expect(session.isSignedIn, isFalse);
    });

    test('restore with stored tokens and valid identity signs in', () async {
      await tokenStore.write(
        const StoredSession(
          accessToken: 'valid-access',
          refreshToken: 'valid-refresh',
          activeRole: 'driver',
        ),
      );
      authRepo.identityToReturn = const Identity(
        userId: 'u-100',
        name: 'Test Driver',
        roles: <Role>[Role.driver, Role.employee],
      );

      await container.read(sessionControllerProvider.notifier).restore();

      final Session session = container.read(sessionProvider);
      expect(session.isSignedIn, isTrue);
      expect(session.userId, 'u-100');
      expect(session.activeRole, Role.driver);
      expect(session.roles, containsAll(<Role>[Role.driver, Role.employee]));
    });

    test('restore with invalid token clears store and leaves signed out', () async {
      await tokenStore.write(
        const StoredSession(
          accessToken: 'dead-access',
          refreshToken: 'dead-refresh',
        ),
      );
      authRepo.identityToReturn = null;

      await container.read(sessionControllerProvider.notifier).restore();

      final Session session = container.read(sessionProvider);
      expect(session.isSignedIn, isFalse);
      expect(await tokenStore.read(), isNull);
    });
  });

  group('SessionController requestCode & submitCode', () {
    test('requestCode moves stage to code', () async {
      final SessionController controller =
          container.read(sessionControllerProvider.notifier);

      await controller.requestCode('+919876543210');

      final SignInState state = container.read(sessionControllerProvider);
      expect(state.stage, SignInStage.code);
      expect(state.phone, '+919876543210');
      expect(authRepo.lastRequestedPhone, '+919876543210');
    });

    test('submitCode with valid code completes sign in and stores session', () async {
      final SessionController controller =
          container.read(sessionControllerProvider.notifier);

      await controller.requestCode('+919876543210');
      authRepo.identityToReturn = const Identity(
        userId: 'u-200',
        name: 'Employee',
        roles: <Role>[Role.employee],
      );

      final bool result = await controller.submitCode('123456');

      expect(result, isTrue);
      final Session session = container.read(sessionProvider);
      expect(session.isSignedIn, isTrue);
      expect(session.activeRole, Role.employee);

      final StoredSession? stored = await tokenStore.read();
      expect(stored, isNotNull);
      expect(stored?.accessToken, 'mock-access-token');
    });

    test('submitCode with rejected code sets rejected state', () async {
      final SessionController controller =
          container.read(sessionControllerProvider.notifier);

      await controller.requestCode('+919876543210');
      authRepo.shouldRejectVerify = true;

      final bool result = await controller.submitCode('000000');

      expect(result, isFalse);
      expect(container.read(sessionProvider).isSignedIn, isFalse);
      expect(container.read(sessionControllerProvider).rejected, isTrue);
    });
  });

  group('SessionController role switching & sign out', () {
    test('switchTo changes active role and updates token store', () async {
      authRepo.identityToReturn = const Identity(
        userId: 'u-300',
        name: 'Supervisor',
        roles: <Role>[Role.employee, Role.supervisor],
      );

      final SessionController controller =
          container.read(sessionControllerProvider.notifier);
      await controller.requestCode('+919876543210');
      await controller.submitCode('123456');

      expect(container.read(sessionProvider).activeRole, Role.employee);

      await controller.switchTo(Role.supervisor);

      expect(container.read(sessionProvider).activeRole, Role.supervisor);
      final StoredSession? stored = await tokenStore.read();
      expect(stored?.activeRole, Role.supervisor.wireName);
    });

    test('signOut clears token store and session', () async {
      await tokenStore.write(
        const StoredSession(
          accessToken: 'valid-access',
          refreshToken: 'valid-refresh',
        ),
      );
      authRepo.identityToReturn = const Identity(
        userId: 'u-400',
        name: 'User',
        roles: <Role>[Role.driver],
      );

      final SessionController controller =
          container.read(sessionControllerProvider.notifier);
      await controller.restore();

      expect(container.read(sessionProvider).isSignedIn, isTrue);

      await controller.signOut();

      expect(container.read(sessionProvider).isSignedIn, isFalse);
      expect(await tokenStore.read(), isNull);
      expect(authRepo.logoutCalled, isTrue);
    });
  });
}

class _TestTokenStore implements TokenStore {
  StoredSession? _stored;

  @override
  Future<StoredSession?> read() async => _stored;

  @override
  Future<void> write(StoredSession session) async {
    _stored = session;
  }

  @override
  Future<void> clear() async {
    _stored = null;
  }
}

class _TestAuthRepository implements AuthRepository {
  String? lastRequestedPhone;
  bool shouldRejectVerify = false;
  bool logoutCalled = false;
  Identity? identityToReturn;

  @override
  Future<void> requestCode(String phone) async {
    lastRequestedPhone = phone;
  }

  @override
  Future<api.TokenPair> verifyCode({required String phone, required String code}) async {
    if (shouldRejectVerify) {
      throw const OtpRejected();
    }
    return api.TokenPair(
      (api.TokenPairBuilder b) => b
        ..accessToken = 'mock-access-token'
        ..refreshToken = 'mock-refresh-token'
        ..expiresIn = 3600,
    );
  }

  @override
  Future<Identity?> me() async {
    return identityToReturn;
  }

  @override
  Future<void> logout() async {
    logoutCalled = true;
  }

  @override
  Future<api.TokenPair?> refresh(String refreshToken) async => null;
}
