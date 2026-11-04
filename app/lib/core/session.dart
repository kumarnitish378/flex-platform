/// Who is using the app right now, and as which role (A01).
///
/// One install, one codebase, screens rendered by role after login (ADR-0003). A person
/// can legitimately hold more than one role - a supervisor who also rides to work - so
/// the *active* role is a separate thing from the set they hold, and every API call
/// carries it in `X-Active-Role` so the server authorises the role they are actually
/// using (hard rule 3).
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';


/// The roles the backend defines (`roles-and-permissions.md`). Kept in the same order
/// and spelling as `app/domain/enums.py`: these strings go on the wire.
enum Role {
  platformAdmin('platform_admin'),
  operatorAdmin('operator_admin'),
  supervisor('supervisor'),
  driver('driver'),
  clientAdmin('client_admin'),
  employee('employee');

  const Role(this.wireName);

  /// Exactly what the server sends and expects. Never `name`, which is camelCase.
  final String wireName;

  static Role? fromWire(String? value) {
    for (final Role role in Role.values) {
      if (role.wireName == value) {
        return role;
      }
    }
    return null;
  }
}

/// A signed-in person, or `Session.none` when nobody is.
class Session {
  const Session({
    required this.roles,
    this.activeRole,
    this.accessToken,
    this.userId,
  });

  /// Nobody signed in. Distinct from "signed in with no roles", which would be a
  /// server-side mistake worth seeing rather than hiding.
  static const Session none = Session(roles: <Role>[]);

  final List<Role> roles;
  final Role? activeRole;
  final String? accessToken;
  final String? userId;

  bool get isSignedIn => accessToken != null && activeRole != null;

  /// True when this person could switch to another role, which is what decides whether
  /// the role switcher appears at all (E/D/S common screens).
  bool get canSwitchRole => roles.length > 1;

  Session copyWith({
    List<Role>? roles,
    Role? activeRole,
    String? accessToken,
    String? userId,
  }) {
    return Session(
      roles: roles ?? this.roles,
      activeRole: activeRole ?? this.activeRole,
      accessToken: accessToken ?? this.accessToken,
      userId: userId ?? this.userId,
    );
  }
}

/// Holds the session and nothing else: no HTTP, no storage.
///
/// Signing in arrives with A03, and persistence with it - tokens belong in
/// `flutter_secure_storage`, never in shared preferences (`non-functional.md`, Privacy).
/// Until then this is deliberately empty rather than faked, so no screen can be built
/// against a pretend login.
class SessionNotifier extends Notifier<Session> {
  @override
  Session build() => Session.none;

  /// A token read back from storage, before `/auth/me` has confirmed anything.
  ///
  /// Deliberately not `signIn`: at this point the app has a token and no idea whether it
  /// is still valid or which roles it carries. `isSignedIn` stays false until a role is
  /// known, so the router keeps the person on the splash rather than flashing a screen
  /// that a dead token is about to empty.
  void restore({required String accessToken, Role? activeRole}) {
    state = Session(
      roles: state.roles,
      activeRole: activeRole,
      accessToken: accessToken,
      userId: state.userId,
    );
  }

  /// A confirmed session: `/auth/me` answered, so the roles are real.
  void signIn({
    required String userId,
    required List<Role> roles,
    required Role activeRole,
    required String accessToken,
  }) {
    state = Session(
      roles: roles,
      activeRole: activeRole,
      accessToken: accessToken,
      userId: userId,
    );
  }

  /// After a refresh. Only the token changes - who they are and the role they are using
  /// must survive, or every token rotation would quietly bounce them to login.
  void updateAccessToken(String accessToken) {
    state = state.copyWith(accessToken: accessToken);
  }

  /// Switch which of this person's roles the app is acting as.
  ///
  /// Refuses a role they do not hold. The server would refuse it too (hard rule 3), but
  /// a client that sends an impossible role produces a 403 that looks like a bug.
  void switchTo(Role role) {
    if (!state.roles.contains(role)) {
      return;
    }
    state = state.copyWith(activeRole: role);
  }

  void signOut() {
    state = Session.none;
  }
}

final NotifierProvider<SessionNotifier, Session> sessionProvider =
    NotifierProvider<SessionNotifier, Session>(SessionNotifier.new);
