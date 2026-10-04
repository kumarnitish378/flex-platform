/// Routing, with the active role deciding where "home" is (A01).
///
/// `coding-standards.md` section 3 rule 2: routes come from the active role, and an
/// unauthorised route redirects home rather than showing an empty screen. Hiding a
/// screen is **not** security - the server authorises every call (hard rule 3) - but a
/// driver who can reach the admin screens will eventually tap something and get a 403
/// they cannot explain, so the app should not offer it.
library;

import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../features/auth/login_screen.dart';
import '../features/common/home_by_role_screen.dart';
import '../features/common/splash_screen.dart';
import 'session.dart';


/// Where each role lands after login. The screen ids are from `screens-by-role.md`.
const Map<Role, String> homeForRole = <Role, String>{
  Role.employee: '/employee',
  Role.driver: '/driver',
  Role.supervisor: '/supervisor',
  Role.operatorAdmin: '/admin',
  Role.clientAdmin: '/client',
  Role.platformAdmin: '/admin',
};

/// Which roles may open a route prefix. Checked on every navigation.
const Map<String, Set<Role>> rolesForRoute = <String, Set<Role>>{
  '/employee': <Role>{Role.employee},
  '/driver': <Role>{Role.driver},
  '/supervisor': <Role>{Role.supervisor, Role.operatorAdmin, Role.platformAdmin},
  '/admin': <Role>{Role.operatorAdmin, Role.platformAdmin},
  '/client': <Role>{Role.clientAdmin},
};

/// True when this role may open this location.
bool roleMayOpen(Role? role, String location) {
  if (role == null) {
    return false;
  }
  for (final MapEntry<String, Set<Role>> entry in rolesForRoute.entries) {
    if (location == entry.key || location.startsWith('${entry.key}/')) {
      return entry.value.contains(role);
    }
  }
  // Routes nobody has claimed - the splash and login - are open to everyone.
  return true;
}

/// Nudges the router whenever the session changes.
///
/// `redirect` is only consulted on navigation, so without this a sign-out would clear
/// the session and leave the person looking at the screen they are no longer allowed to
/// see - until they happened to navigate. A widget test caught exactly that.
class _SessionRefresh extends ChangeNotifier {
  _SessionRefresh(this._ref) {
    _ref.listen<Session>(
      sessionProvider,
      (Session? previous, Session next) {
        // Only an actual change of who-or-what-role matters; token refreshes do not
        // move anybody, and rebuilding the router on those would discard the back stack.
        if (previous?.isSignedIn != next.isSignedIn ||
            previous?.activeRole != next.activeRole) {
          notifyListeners();
        }
      },
      fireImmediately: false,
    );
  }

  final Ref _ref;
}

final Provider<GoRouter> routerProvider = Provider<GoRouter>((Ref ref) {
  final _SessionRefresh refresh = _SessionRefresh(ref);
  ref.onDispose(refresh.dispose);

  return GoRouter(
    initialLocation: '/',
    refreshListenable: refresh,
    routes: <RouteBase>[
      GoRoute(path: '/', builder: (_, _) => const SplashScreen()),
      GoRoute(path: '/login', builder: (_, _) => const LoginScreen()),
      for (final MapEntry<Role, String> entry in homeForRole.entries)
        if (entry.key != Role.platformAdmin)
          GoRoute(
            path: entry.value,
            builder: (_, _) => HomeByRoleScreen(role: entry.key),
          ),
    ],
    redirect: (_, GoRouterState state) {
      final Session session = ref.read(sessionProvider);
      final String location = state.matchedLocation;

      if (!session.isSignedIn) {
        // The splash decides when to leave; everything else waits at login.
        return location == '/' || location == '/login' ? null : '/login';
      }
      final String home = homeForRole[session.activeRole] ?? '/employee';
      if (location == '/' || location == '/login') {
        return home;
      }
      return roleMayOpen(session.activeRole, location) ? null : home;
    },
  );
});
