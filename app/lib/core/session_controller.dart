/// Sign in, restore, switch role, sign out (A03).
///
/// Separate from `session.dart`, which holds the plain state and nothing else. This is
/// the part with the storage and the HTTP in it, so a widget test can override one and
/// leave the other alone.
library;

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:smart_cab_api/smart_cab_api.dart' as api;

import '../data/api/auth_interceptor.dart';
import '../data/api/auth_repository.dart';
import 'env.dart';
import 'session.dart';
import 'token_store.dart';

/// The dio instance every repository shares, with the auth interceptor attached.
final Provider<Dio> dioProvider = Provider<Dio>((Ref ref) {
  final Dio dio = Dio(BaseOptions(baseUrl: Env.apiBaseUrl));
  dio.interceptors.add(AuthInterceptor(ref.read(authTokensProvider)));
  return dio;
});

final Provider<TokenStore> tokenStoreProvider = Provider<TokenStore>(
  (Ref ref) => SecureTokenStore(),
);

final Provider<AuthRepository> authRepositoryProvider = Provider<AuthRepository>((Ref ref) {
  return AuthRepository(api.AuthApi(ref.read(dioProvider), api.standardSerializers));
});

/// Bridges the session to the interceptor without either importing the other.
final Provider<AuthTokens> authTokensProvider = Provider<AuthTokens>(
  (Ref ref) => _SessionTokens(ref),
);

class _SessionTokens implements AuthTokens {
  _SessionTokens(this._ref);

  final Ref _ref;

  @override
  String? get accessToken => _ref.read(sessionProvider).accessToken;

  @override
  String? get activeRole => _ref.read(sessionProvider).activeRole?.wireName;

  @override
  Future<String?> refresh() => _ref.read(sessionControllerProvider.notifier).refreshTokens();

  @override
  Future<void> onSessionLost() =>
      _ref.read(sessionControllerProvider.notifier).signOut(revoke: false);
}

/// How far a sign-in attempt has got. Drives C-02 without the screen holding state.
enum SignInStage { phone, code }

class SignInState {
  const SignInState({
    this.stage = SignInStage.phone,
    this.phone = '',
    this.busy = false,
    this.rejected = false,
    this.unavailable,
  });

  final SignInStage stage;
  final String phone;
  final bool busy;

  /// The code was refused. One flag for every reason, because the server gives one
  /// answer for all of them (OQ-24) and guessing which would be inventing information.
  final bool rejected;

  /// Set when the backend could not be reached at all - a different message from a
  /// refused code, and not the person's fault.
  final String? unavailable;

  SignInState copyWith({
    SignInStage? stage,
    String? phone,
    bool? busy,
    bool? rejected,
    String? unavailable,
  }) {
    return SignInState(
      stage: stage ?? this.stage,
      phone: phone ?? this.phone,
      busy: busy ?? this.busy,
      rejected: rejected ?? false,
      unavailable: unavailable,
    );
  }
}

/// Owns sign-in and the session's lifecycle.
class SessionController extends Notifier<SignInState> {
  @override
  SignInState build() => const SignInState();

  AuthRepository get _auth => ref.read(authRepositoryProvider);

  TokenStore get _store => ref.read(tokenStoreProvider);

  SessionNotifier get _session => ref.read(sessionProvider.notifier);

  /// C-01: put a stored session back, refreshing it if the access token has expired.
  ///
  /// Always ends with a definite answer - signed in or not - because the splash waits on
  /// it, and an exception here would leave the app on the splash screen forever.
  Future<void> restore() async {
    final StoredSession? stored = await _store.read();
    if (stored == null) {
      return;
    }

    _session.restore(
      accessToken: stored.accessToken,
      activeRole: Role.fromWire(stored.activeRole),
    );

    // `/auth/me` both validates the token and tells us the roles. If it fails, the
    // interceptor has already tried a refresh, so this is a dead session.
    final Identity? identity = await _auth.me();
    if (identity == null || identity.roles.isEmpty) {
      await signOut(revoke: false);
      return;
    }
    _session.signIn(
      userId: identity.userId,
      roles: identity.roles,
      activeRole: _chooseRole(identity.roles, Role.fromWire(stored.activeRole)),
      accessToken: stored.accessToken,
    );
  }

  /// C-02, first step: ask for a code.
  Future<void> requestCode(String phone) async {
    state = state.copyWith(phone: phone, busy: true);
    try {
      await _auth.requestCode(phone);
      // Straight to the code step whatever the number was: the server answers 202 for
      // any well-formed phone, and showing "no such user" here would turn the screen
      // into a directory of an operator's staff (OQ-24).
      state = state.copyWith(stage: SignInStage.code, busy: false);
    } on AuthUnavailable catch (error) {
      state = state.copyWith(busy: false, unavailable: error.cause);
    }
  }

  /// C-02, second step: exchange the code for a session.
  Future<bool> submitCode(String code) async {
    state = state.copyWith(busy: true);
    try {
      final api.TokenPair pair = await _auth.verifyCode(phone: state.phone, code: code);
      final String access = pair.accessToken;
      await _store.write(
        StoredSession(accessToken: access, refreshToken: pair.refreshToken),
      );
      _session.restore(accessToken: access, activeRole: null);

      final Identity? identity = await _auth.me();
      if (identity == null || identity.roles.isEmpty) {
        // Signed in with no role is a server-side problem, not something to paper over
        // with a default: there is no screen such a person should see.
        await signOut(revoke: false);
        state = state.copyWith(busy: false, unavailable: 'no_roles');
        return false;
      }
      final Role role = _chooseRole(identity.roles, null);
      _session.signIn(
        userId: identity.userId,
        roles: identity.roles,
        activeRole: role,
        accessToken: access,
      );
      await _store.write(
        StoredSession(
          accessToken: access,
          refreshToken: pair.refreshToken,
          activeRole: role.wireName,
        ),
      );
      state = const SignInState();
      return true;
    } on OtpRejected {
      state = state.copyWith(busy: false, rejected: true);
      return false;
    } on AuthUnavailable catch (error) {
      state = state.copyWith(busy: false, unavailable: error.cause);
      return false;
    }
  }

  /// Rotate the tokens. Returns the new access token, or `null` if the session is over.
  Future<String?> refreshTokens() async {
    final StoredSession? stored = await _store.read();
    if (stored == null) {
      return null;
    }
    final api.TokenPair? pair = await _auth.refresh(stored.refreshToken);
    if (pair == null) {
      return null;
    }
    await _store.write(
      StoredSession(
        accessToken: pair.accessToken,
        // Rotated by the server on every refresh (api-spec: "refresh token rotated"),
        // so storing the old one would make the *next* refresh fail.
        refreshToken: pair.refreshToken,
        activeRole: stored.activeRole,
      ),
    );
    _session.updateAccessToken(pair.accessToken);
    return pair.accessToken;
  }

  /// C-03: act as a different role, and remember it for next launch.
  Future<void> switchTo(Role role) async {
    _session.switchTo(role);
    final StoredSession? stored = await _store.read();
    if (stored != null) {
      await _store.write(
        StoredSession(
          accessToken: stored.accessToken,
          refreshToken: stored.refreshToken,
          activeRole: role.wireName,
        ),
      );
    }
  }

  /// End the session on this device, always.
  ///
  /// `revoke: false` when the server has already refused us - there is nothing left to
  /// revoke, and calling `/auth/logout` with a dead token just waits for a timeout while
  /// the person stares at a screen they are no longer allowed to see.
  Future<void> signOut({bool revoke = true}) async {
    if (revoke) {
      await _auth.logout();
    }
    await _store.clear();
    _session.signOut();
    state = const SignInState();
  }

  /// Which role to land on: the remembered one if they still hold it, else the first.
  ///
  /// The server's order is meaningful - `roles-and-permissions.md` lists them from most
  /// to least privileged - so "the first" is the most capable role they have, which is
  /// the right default for someone who has never chosen.
  Role _chooseRole(List<Role> roles, Role? remembered) {
    if (remembered != null && roles.contains(remembered)) {
      return remembered;
    }
    return roles.first;
  }
}

final NotifierProvider<SessionController, SignInState> sessionControllerProvider =
    NotifierProvider<SessionController, SignInState>(SessionController.new);
