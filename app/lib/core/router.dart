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

import '../features/admin/clients_screen.dart';
import '../features/admin/dashboard_screen.dart';
import '../features/admin/drivers_screen.dart';
import '../features/admin/mode_settings_screen.dart';
import '../features/admin/reports_screen.dart';
import '../features/admin/settings_screen.dart';
import '../features/admin/users_screen.dart';
import '../features/admin/vehicles_screen.dart';
import '../features/auth/login_screen.dart';
import '../features/client/client_reports_screen.dart';
import '../features/client/employee_form_screen.dart';
import '../features/client/employees_screen.dart';
import '../features/common/app_shell.dart';
import '../features/common/detail_scaffold.dart';
import '../features/common/pending_screen.dart';
import '../features/common/splash_screen.dart';
import '../features/driver/duty_home_screen.dart';
import '../features/driver/navigation_map_screen.dart';
import '../features/driver/permission_explainer_screen.dart';
import '../features/driver/report_issue_screen.dart';
import '../features/driver/trip_detail_screen.dart';
import '../features/driver/trip_list_screen.dart';
import '../features/employee/employee_home_screen.dart';
import '../features/employee/live_tracking_screen.dart';
import '../features/employee/request_confirmation_screen.dart';
import '../features/employee/request_form_screen.dart';
import '../features/employee/ride_history_screen.dart';
import '../features/employee/saved_places_screen.dart';
import '../features/employee/trip_completed_screen.dart';
import '../features/supervisor/alerts_list_screen.dart';
import '../features/supervisor/assign_panel_screen.dart';
import '../features/supervisor/live_map_screen.dart';
import '../features/supervisor/pending_queue_screen.dart';
import '../features/supervisor/suggestions_panel_screen.dart';
import '../features/supervisor/trips_board_screen.dart';
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
              builder: (_, _) {
                if (screen == AppScreen.employeeHome) {
                  return const EmployeeHomeScreen();
                }
                if (screen == AppScreen.rideHistory) {
                  return const RideHistoryScreen();
                }
                if (screen == AppScreen.savedPlaces) {
                  return const SavedPlacesScreen();
                }
                if (screen == AppScreen.dutyHome) {
                  return const DutyHomeScreen();
                }
                if (screen == AppScreen.driverTrips) {
                  return const TripListScreen();
                }
                if (screen == AppScreen.dispatchMap) {
                  return const SupervisorLiveMapScreen();
                }
                if (screen == AppScreen.pendingQueue) {
                  return const PendingQueueScreen();
                }
                if (screen == AppScreen.tripsBoard) {
                  return const TripsBoardScreen();
                }
                if (screen == AppScreen.alerts) {
                  return const AlertsListScreen();
                }
                if (screen == AppScreen.adminDashboard) {
                  return const DashboardScreen();
                }
                if (screen == AppScreen.adminVehicles) {
                  return const VehiclesScreen();
                }
                if (screen == AppScreen.adminDrivers) {
                  return const DriversScreen();
                }
                if (screen == AppScreen.adminClients) {
                  return const ClientsScreen();
                }
                if (screen == AppScreen.adminUsers) {
                  return const UsersScreen();
                }
                if (screen == AppScreen.adminReports) {
                  return const ReportsScreen();
                }
                if (screen == AppScreen.adminSettings) {
                  return const SettingsScreen();
                }
                if (screen == AppScreen.adminModeSettings) {
                  return const ModeSettingsScreen();
                }
                if (screen == AppScreen.clientEmployees) {
                  return const ClientEmployeesScreen();
                }
                if (screen == AppScreen.clientReports) {
                  return const ClientReportsScreen();
                }
                return PendingScreen(screen: screen, key: Key(screen.id));
              },
            ),
        ],
      ),
      for (final AppScreen screen in _detailScreens)
        GoRoute(
          path: screen.path,
          builder: (_, GoRouterState state) {
            if (screen == AppScreen.requestForm) {
              return const DetailScaffold(
                screen: AppScreen.requestForm,
                body: RequestFormScreen(),
              );
            }
            if (screen == AppScreen.requestConfirmation) {
              final String reqId = state.pathParameters['requestId'] ?? '';
              return DetailScaffold(
                screen: AppScreen.requestConfirmation,
                body: RequestConfirmationScreen(requestId: reqId),
              );
            }
            if (screen == AppScreen.liveTracking) {
              final String tripId = state.pathParameters['tripId'] ?? '';
              return DetailScaffold(
                screen: AppScreen.liveTracking,
                body: LiveTrackingScreen(tripId: tripId),
              );
            }
            if (screen == AppScreen.tripCompleted) {
              final String tripId = state.pathParameters['tripId'] ?? '';
              return DetailScaffold(
                screen: AppScreen.tripCompleted,
                body: TripCompletedScreen(tripId: tripId),
              );
            }
            if (screen == AppScreen.driverTripDetail) {
              final String tripId = state.pathParameters['tripId'] ?? '';
              return DetailScaffold(
                screen: AppScreen.driverTripDetail,
                body: TripDetailScreen(tripId: tripId),
              );
            }
            if (screen == AppScreen.driverNavigation) {
              final String tripId = state.pathParameters['tripId'] ?? '';
              return DetailScaffold(
                screen: AppScreen.driverNavigation,
                body: NavigationMapScreen(tripId: tripId),
              );
            }
            if (screen == AppScreen.driverReportIssue) {
              return const DetailScaffold(
                screen: AppScreen.driverReportIssue,
                body: ReportIssueScreen(),
              );
            }
            if (screen == AppScreen.assignPanel) {
              final String reqId = state.pathParameters['requestId'] ?? '';
              return DetailScaffold(
                screen: AppScreen.assignPanel,
                body: AssignPanelScreen(requestId: reqId),
              );
            }
            if (screen == AppScreen.suggestionsPanel) {
              final String reqId = state.pathParameters['requestId'] ?? '';
              return DetailScaffold(
                screen: AppScreen.suggestionsPanel,
                body: SuggestionsPanelScreen(requestId: reqId),
              );
            }
            if (screen == AppScreen.locationPermission) {
              return const DetailScaffold(
                screen: AppScreen.locationPermission,
                body: PermissionExplainerScreen(),
              );
            }
            if (screen == AppScreen.clientEmployeeForm) {
              final String? empId = state.pathParameters['employeeId'];
              return DetailScaffold(
                screen: AppScreen.clientEmployeeForm,
                body: EmployeeFormScreen(employeeId: empId == 'new' ? null : empId),
              );
            }
            return DetailScaffold(
              screen: screen,
              body: PendingScreen(screen: screen, key: Key(screen.id)),
            );
          },
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
