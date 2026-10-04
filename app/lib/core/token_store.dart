/// Where the tokens live (A03).
///
/// `non-functional.md` (Privacy) and `coding-standards.md` section 3: tokens go in
/// `flutter_secure_storage`, never in shared preferences. On Android that is the
/// Keystore-backed `EncryptedSharedPreferences`; shared preferences is a world-readable
/// XML file on a rooted device, and a refresh token is a login that lasts for weeks.
///
/// An interface, because every test that touches sign-in would otherwise need a platform
/// channel. The in-memory implementation lives in the tests, not here.
library;

import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// The pair the backend issues, plus which role the app was last acting as.
class StoredSession {
  const StoredSession({
    required this.accessToken,
    required this.refreshToken,
    this.activeRole,
  });

  final String accessToken;
  final String refreshToken;

  /// Restored so a returning driver is not dropped on the employee screen. `null` on a
  /// first run, or when the stored role is no longer one the person holds.
  final String? activeRole;
}

abstract class TokenStore {
  Future<StoredSession?> read();

  Future<void> write(StoredSession session);

  /// Called on sign-out and whenever a refresh is refused. Must leave nothing behind:
  /// a stale refresh token is the one credential worth stealing.
  Future<void> clear();
}

class SecureTokenStore implements TokenStore {
  SecureTokenStore({FlutterSecureStorage? storage})
    : _storage =
          storage ??
          const FlutterSecureStorage(
            aOptions: AndroidOptions(encryptedSharedPreferences: true),
          );

  final FlutterSecureStorage _storage;

  static const String _accessKey = 'access_token';
  static const String _refreshKey = 'refresh_token';
  static const String _roleKey = 'active_role';

  @override
  Future<StoredSession?> read() async {
    final String? access = await _storage.read(key: _accessKey);
    final String? refresh = await _storage.read(key: _refreshKey);
    if (access == null || refresh == null) {
      // Half a session is no session. Returning the access token alone would give a
      // signed-in-looking app that cannot recover when the token expires minutes later.
      return null;
    }
    return StoredSession(
      accessToken: access,
      refreshToken: refresh,
      activeRole: await _storage.read(key: _roleKey),
    );
  }

  @override
  Future<void> write(StoredSession session) async {
    await _storage.write(key: _accessKey, value: session.accessToken);
    await _storage.write(key: _refreshKey, value: session.refreshToken);
    final String? role = session.activeRole;
    if (role != null) {
      await _storage.write(key: _roleKey, value: role);
    }
  }

  @override
  Future<void> clear() async {
    await _storage.delete(key: _accessKey);
    await _storage.delete(key: _refreshKey);
    await _storage.delete(key: _roleKey);
  }
}
