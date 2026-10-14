/// Routing, with the active role deciding what exists (A01, A04).
///
/// `coding-standards.md` section 3 rule 2: routes come from the active role, and an
/// unauthorised route redirects home rather than showing an empty screen. Hiding a
/// screen is **not** security - the server authorises every call (hard rule 3) - but a
/// driver who can reach the admin screens will eventually tap something and get a 403
/// they cannot explain, so the app should not offer it.
///
/// The routes are built from the catalogue in `screens.dart`, which also carries the
/// role gate. One table, so a screen cannot exist without a gate and a gate cannot
/// point at a screen that does not exist.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../features/auth/login_screen.dart';
import '../features/common/app_shell.dart';
import '../features/common/detail_scaffold.dart';
import '../features/common/pending_screen.dart';
import '../features/common/splash_screen.dart';
import 'screens.dart';
import 'session.dart';

export 'screens.dart' show AppScreen, AppSection, homeForRole, primaryDestinations;

/// True when this role may open this location.
///
/// The match is on path segments, not characters: `/driverish` is not under `/driver`,
/// and a plain `startsWith` would say that it was.
bool roleMayOpen(Role? role, String location) {
  if (role == null) {
    return false;
  }
  for (final MapEntry<String, Set<Role>> entry in rolesForRoute.entries) {
    if (location == entry.key || location.startsWith('${entry.key}/')) {
      return entry.value.contains(role);
    }
  }
  // Routes nobody has claimed - the splash, login, and the screens every role has -
  // are open to anyone signed in.
  return true;
}

/// The screens that live inside the navigation shell: everything any role reaches from
/// a tab or from "More".
final Set<AppScreen> _shellScreens = <AppScreen>{
  for (final Role role in Role.values) ...destinationsFor(role),
};

/// Everything else with a route: the screens a person is pushed into from a
/// destination. Longest path first, so `/driver/trips/:tripId/navigate` is matched
/// before `/driver/trips/:tripId` rather than being swallowed by it.
List<AppScreen> get _detailScreens {
  final List<AppScreen> screens = AppScreen.values
      .where(
        (AppScreen screen) =>
            screen != AppScreen.splash &&
            screen != AppScreen.login &&
            !_shellScreens.contains(screen),
      )
      .toList()
    ..sort((AppScreen a, AppScreen b) => b.path.length.compareTo(a.path.length));
  return screens;
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
    initialLocation: AppScreen.splash.path,
    refreshListenable: refresh,
    routes: <RouteBase>[
      GoRoute(path: AppScreen.splash.path, builder: (_, _) => const SplashScreen()),
      GoRoute(path: AppScreen.login.path, builder: (_, _) => const LoginScreen()),
      ShellRoute(
        builder: (_, _, Widget child) => AppShell(child: child),
        routes: <RouteBase>[
          for (final AppScreen screen in _shellScreens)
            GoRoute(
              path: screen.path,
              builder: (_, _) => PendingScreen(screen: screen, key: Key(screen.id)),
            ),
        ],
      ),
      for (final AppScreen screen in _detailScreens)
        GoRoute(
          path: screen.path,
          builder: (_, _) => DetailScaffold(
            screen: screen,
            body: PendingScreen(screen: screen, key: Key(screen.id)),
          ),
        ),
    ],
    redirect: (_, GoRouterState state) {
      final Session session = ref.read(sessionProvider);
      final String location = state.matchedLocation;

      if (!session.isSignedIn) {
        // The splash decides when to leave; everything else waits at login.
        return location == AppScreen.splash.path || location == AppScreen.login.path
            ? null
            : AppScreen.login.path;
      }
      final String home =
          homeForRole[session.activeRole] ?? AppScreen.employeeHome.path;
      if (location == AppScreen.splash.path || location == AppScreen.login.path) {
        return home;
      }
      return roleMayOpen(session.activeRole, location) ? null : home;
    },
  );
});
