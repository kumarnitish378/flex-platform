/// Every screen the app routes to, with the id it carries in `screens-by-role.md` (A04).
///
/// One table, because role-based navigation goes wrong in two directions and a table
/// closes both. A screen nobody lists is unreachable; a screen reachable by the wrong
/// role is a row of buttons that each return 403 with nothing the person can act on.
/// Neither is security - the server authorises every call (hard rule 3) - but both are
/// defects, and both stay invisible until somebody signs in as that role.
///
/// A screen inherits its permitted roles from its [AppSection], which is its path
/// prefix. That is deliberate: adding `/admin/zones` in Phase 2 cannot accidentally be
/// reachable by a driver, because the gate reads the prefix rather than a per-screen
/// list somebody has to remember to fill in.
library;

import 'package:flutter/material.dart';

import '../l10n/app_localizations.dart';
import 'session.dart';

/// A part of the app, identified by its path prefix, and the roles that may open it.
///
/// The role sets come from the permission matrix in `roles-and-permissions.md`:
/// `operator_admin` and `platform_admin` may work the dispatch board; a `client_admin`
/// may not, being scoped to one client - the same reason B13 refused them the
/// operator-wide WebSocket feed; and a `supervisor` does not get the admin screens,
/// because the matrix denies them vehicles, clients, users and zones.
enum AppSection {
  /// Screens every signed-in person has, plus the two that precede a session.
  common('', <Role>{
    Role.platformAdmin,
    Role.operatorAdmin,
    Role.supervisor,
    Role.driver,
    Role.clientAdmin,
    Role.employee,
  }),
  employee('/employee', <Role>{Role.employee}),
  driver('/driver', <Role>{Role.driver}),
  supervisor('/supervisor', <Role>{
    Role.supervisor,
    Role.operatorAdmin,
    Role.platformAdmin,
  }),
  admin('/admin', <Role>{Role.operatorAdmin, Role.platformAdmin}),
  client('/client', <Role>{Role.clientAdmin});

  const AppSection(this.prefix, this.roles);

  /// The path prefix every screen in this section sits under. Empty for [common],
  /// whose screens are top-level and open to anybody signed in.
  final String prefix;

  final Set<Role> roles;
}

/// The screens that have routes today.
///
/// Phase 2 screens - E-08 ride offer, A-06 zones, S-05 overrides, S-06 modes, L-03
/// policies - are deliberately absent. A route to a screen that will not exist until
/// Phase 2 is a dead end a role can reach.
///
/// `task` names the task that replaces a placeholder with the real screen, so an
/// unbuilt screen says which work is missing instead of apologising vaguely.
enum AppScreen {
  splash('C-01', '/', AppSection.common, Icons.local_taxi, 'A01'),
  login('C-02', '/login', AppSection.common, Icons.login, 'A03'),
  profile('C-04', '/profile', AppSection.common, Icons.person_outline, 'A04'),
  notifications(
    'C-05',
    '/notifications',
    AppSection.common,
    Icons.notifications_none,
    'A07',
  ),

  employeeHome('E-01', '/employee', AppSection.employee, Icons.home_outlined, 'A06'),
  requestForm(
    'E-02',
    '/employee/request',
    AppSection.employee,
    Icons.add_location_alt_outlined,
    'A06',
  ),
  requestConfirmation(
    'E-03',
    '/employee/request/:requestId',
    AppSection.employee,
    Icons.receipt_long_outlined,
    'A06',
  ),
  liveTracking(
    'E-04',
    '/employee/trip/:tripId',
    AppSection.employee,
    Icons.my_location,
    'A08',
  ),
  tripCompleted(
    'E-05',
    '/employee/trip/:tripId/rate',
    AppSection.employee,
    Icons.star_outline,
    'A08',
  ),
  rideHistory('E-06', '/employee/history', AppSection.employee, Icons.history, 'A08'),
  savedPlaces(
    'E-07',
    '/employee/places',
    AppSection.employee,
    Icons.bookmark_outline,
    'A08',
  ),

  dutyHome('D-01', '/driver', AppSection.driver, Icons.toggle_on_outlined, 'A09'),
  locationPermission(
    'D-02',
    '/driver/permission',
    AppSection.driver,
    Icons.gps_fixed,
    'A09',
  ),
  driverTrips('D-03', '/driver/trips', AppSection.driver, Icons.list_alt, 'A10'),
  driverTripDetail(
    'D-04',
    '/driver/trips/:tripId',
    AppSection.driver,
    Icons.alt_route,
    'A10',
  ),
  driverNavigation(
    'D-05',
    '/driver/trips/:tripId/navigate',
    AppSection.driver,
    Icons.navigation_outlined,
    'A10',
  ),
  driverReportIssue(
    'D-06',
    '/driver/issue',
    AppSection.driver,
    Icons.report_outlined,
    'A10',
  ),

  dispatchMap('S-01', '/supervisor', AppSection.supervisor, Icons.map_outlined, 'A11'),
  pendingQueue(
    'S-02',
    '/supervisor/queue',
    AppSection.supervisor,
    Icons.pending_actions_outlined,
    'A11',
  ),
  assignPanel(
    'S-03',
    '/supervisor/queue/:requestId',
    AppSection.supervisor,
    Icons.how_to_reg_outlined,
    'A11',
  ),
  tripsBoard(
    'S-04',
    '/supervisor/trips',
    AppSection.supervisor,
    Icons.dashboard_outlined,
    'A11',
  ),
  alerts(
    'S-07',
    '/supervisor/alerts',
    AppSection.supervisor,
    Icons.warning_amber_outlined,
    'A11',
  ),
  requestOnBehalf(
    'S-08',
    '/supervisor/on-behalf',
    AppSection.supervisor,
    Icons.person_add_alt,
    'A11',
  ),
  suggestionsPanel(
    'S-05',
    '/supervisor/suggestions/:requestId',
    AppSection.supervisor,
    Icons.auto_awesome,
    'A13',
  ),

  adminDashboard('A-01', '/admin', AppSection.admin, Icons.insights_outlined, 'A12'),
  adminVehicles(
    'A-02',
    '/admin/vehicles',
    AppSection.admin,
    Icons.directions_car_outlined,
    'A12',
  ),
  adminDrivers('A-03', '/admin/drivers', AppSection.admin, Icons.badge_outlined, 'A12'),
  adminClients(
    'A-04',
    '/admin/clients',
    AppSection.admin,
    Icons.business_outlined,
    'A12',
  ),
  adminUsers(
    'A-05',
    '/admin/users',
    AppSection.admin,
    Icons.manage_accounts_outlined,
    'A12',
  ),
  adminReports(
    'A-07',
    '/admin/reports',
    AppSection.admin,
    Icons.table_chart_outlined,
    'A12',
  ),
  adminSettings('A-08', '/admin/settings', AppSection.admin, Icons.tune, 'A12'),
  adminModeSettings('A-06', '/admin/modes', AppSection.admin, Icons.toggle_off_outlined, 'A14'),

  clientEmployees('L-01', '/client', AppSection.client, Icons.groups_outlined, 'A12'),
  clientEmployeeForm(
    'L-02',
    '/client/employees/:employeeId',
    AppSection.client,
    Icons.edit_outlined,
    'A12',
  ),
  clientReports(
    'L-04',
    '/client/reports',
    AppSection.client,
    Icons.table_chart_outlined,
    'A12',
  );

  const AppScreen(this.id, this.path, this.section, this.icon, this.task);

  /// The id from `screens-by-role.md`. It is also the screen's widget `Key`, which is
  /// how every test in this project names a screen (coding-standards.md section 3).
  final String id;

  final String path;
  final AppSection section;
  final IconData icon;

  /// The task that builds the real screen.
  final String task;

  /// True when the path carries a parameter, which disqualifies it as a navigation
  /// destination: a tab bar has no sensible value to put in `:tripId`.
  bool get isParameterised => path.contains(':');
}

/// The destinations in each role's navigation bar, in order. The first is that role's
/// home - where login lands, and where an unauthorised deep link sends them.
///
/// Capped at four so the fifth slot can be "More". Material's navigation bar takes five
/// at the most and an operator admin has seven screens, so something has to give; what
/// gives is the screens that do not earn a permanent tab.
const Map<Role, List<AppScreen>> primaryDestinations = <Role, List<AppScreen>>{
  Role.employee: <AppScreen>[
    AppScreen.employeeHome,
    AppScreen.rideHistory,
    AppScreen.savedPlaces,
  ],
  Role.driver: <AppScreen>[AppScreen.dutyHome, AppScreen.driverTrips],
  Role.supervisor: <AppScreen>[
    AppScreen.dispatchMap,
    AppScreen.pendingQueue,
    AppScreen.tripsBoard,
    AppScreen.alerts,
  ],
  Role.operatorAdmin: <AppScreen>[
    AppScreen.adminDashboard,
    AppScreen.adminVehicles,
    AppScreen.adminDrivers,
    AppScreen.adminClients,
  ],
  Role.clientAdmin: <AppScreen>[AppScreen.clientEmployees, AppScreen.clientReports],
  Role.platformAdmin: <AppScreen>[
    AppScreen.adminDashboard,
    AppScreen.adminVehicles,
    AppScreen.adminDrivers,
    AppScreen.adminClients,
  ],
};

/// What each role has beyond its tabs. Notifications and the profile are added for
/// every role by [secondaryDestinations], so a role lists only what is its own.
const Map<Role, List<AppScreen>> _roleExtras = <Role, List<AppScreen>>{
  Role.employee: <AppScreen>[],
  Role.driver: <AppScreen>[AppScreen.driverReportIssue],
  Role.supervisor: <AppScreen>[AppScreen.requestOnBehalf],
  Role.operatorAdmin: <AppScreen>[
    AppScreen.adminUsers,
    AppScreen.adminReports,
    AppScreen.adminSettings,
    // An operator admin may work the board too (`roles-and-permissions.md`), so the
    // dispatch map is reachable rather than merely permitted.
    AppScreen.dispatchMap,
  ],
  Role.clientAdmin: <AppScreen>[],
  Role.platformAdmin: <AppScreen>[
    AppScreen.adminUsers,
    AppScreen.adminReports,
    AppScreen.adminSettings,
    AppScreen.dispatchMap,
  ],
};

/// What "More" offers this role.
List<AppScreen> secondaryDestinations(Role role) => <AppScreen>[
  ...?_roleExtras[role],
  AppScreen.notifications,
  AppScreen.profile,
];

/// Every screen a role can reach from the navigation, tabs and "More" together.
List<AppScreen> destinationsFor(Role role) => <AppScreen>[
  ...?primaryDestinations[role],
  ...secondaryDestinations(role),
];

/// Where each role lands after login, derived from its first destination so that the
/// home and the first tab can never disagree.
final Map<Role, String> homeForRole = <Role, String>{
  for (final Role role in Role.values) role: primaryDestinations[role]!.first.path,
};

/// Which roles may open a path prefix, derived from the sections so that a new screen
/// cannot be added without a gate.
final Map<String, Set<Role>> rolesForRoute = <String, Set<Role>>{
  for (final AppSection section in AppSection.values)
    if (section.prefix.isNotEmpty) section.prefix: section.roles,
};

/// The localized label a screen shows in the navigation.
extension AppScreenLabel on AppScreen {
  String label(AppText text) {
    return switch (this) {
      AppScreen.splash => text.appTitle,
      AppScreen.login => text.signIn,
      AppScreen.profile => text.navProfile,
      AppScreen.notifications => text.navNotifications,
      AppScreen.employeeHome => text.navHome,
      AppScreen.requestForm => text.navRequestCab,
      AppScreen.requestConfirmation => text.navRequestStatus,
      AppScreen.liveTracking => text.navLiveTracking,
      AppScreen.tripCompleted => text.navRateTrip,
      AppScreen.rideHistory => text.navHistory,
      AppScreen.savedPlaces => text.navSavedPlaces,
      AppScreen.dutyHome => text.navDuty,
      AppScreen.locationPermission => text.navLocationPermission,
      AppScreen.driverTrips => text.navTrips,
      AppScreen.driverTripDetail => text.navTripDetail,
      AppScreen.driverNavigation => text.navNavigate,
      AppScreen.driverReportIssue => text.navReportIssue,
      AppScreen.dispatchMap => text.navDispatchMap,
      AppScreen.pendingQueue => text.navPendingQueue,
      AppScreen.assignPanel => text.navAssign,
      AppScreen.tripsBoard => text.navTripsBoard,
      AppScreen.alerts => text.navAlerts,
      AppScreen.requestOnBehalf => text.navRequestOnBehalf,
      AppScreen.suggestionsPanel => 'Suggestions',
      AppScreen.adminDashboard => text.navDashboard,
      AppScreen.adminVehicles => text.navVehicles,
      AppScreen.adminDrivers => text.navDrivers,
      AppScreen.adminClients => text.navClients,
      AppScreen.adminUsers => text.navUsers,
      AppScreen.adminReports => text.navReports,
      AppScreen.adminSettings => text.navSettings,
      AppScreen.adminModeSettings => 'Mode Settings',
      AppScreen.clientEmployees => text.navEmployees,
      AppScreen.clientEmployeeForm => text.navEmployeeForm,
      AppScreen.clientReports => text.navReports,
    };
  }
}
