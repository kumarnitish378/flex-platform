/// The navigation every role shares, filled from that role's destinations (A04).
///
/// One shell, not five. A person can hold more than one role and switch between them
/// mid-session (C-03), so the navigation has to be a function of the *active* role
/// rather than something chosen once at login: five separate shells would each hold
/// their own idea of where the person is, and switching would strand them.
///
/// Hiding a destination is not a permission check - the server authorises every call
/// (hard rule 3). It is there so a role is not offered a screen whose every button
/// would 403 with nothing it could tell them.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/screens.dart';
import '../../core/session.dart';
import '../../core/session_controller.dart';
import '../../l10n/app_localizations.dart';
import 'role_switcher.dart';

/// Above this width the destinations go in a rail beside the content, which is what
/// `screens-by-role.md` asks for on tablets - and it has room for every destination, so
/// there is no "More" to open.
const double _railBreakpoint = 840;

class AppShell extends ConsumerWidget {
  const AppShell({required this.child, super.key});

  final Widget child;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final AppText text = AppText.of(context);
    final Session session = ref.watch(sessionProvider);
    final Role? role = session.activeRole;
    if (role == null) {
      // The router's redirect sends a signed-out person to login; until it runs there
      // is nothing to put in a navigation bar, and guessing a role would be worse.
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    final String location = GoRouterState.of(context).matchedLocation;
    final List<AppScreen> primary = primaryDestinations[role]!;
    final List<AppScreen> secondary = secondaryDestinations(role);
    final AppScreen current = _currentScreen(role, location) ?? primary.first;
    final bool wide = MediaQuery.sizeOf(context).width >= _railBreakpoint;

    final Widget body = wide
        ? Row(
            children: <Widget>[
              _Rail(
                role: role,
                current: current,
                destinations: <AppScreen>[...primary, ...secondary],
              ),
              const VerticalDivider(width: 1),
              Expanded(child: child),
            ],
          )
        : child;

    return Scaffold(
      key: Key('shell-${role.wireName}'),
      appBar: AppBar(
        title: Text(current.label(text)),
        actions: <Widget>[
          if (session.canSwitchRole)
            IconButton(
              key: const Key('switch-role'),
              tooltip: text.switchRole,
              icon: const Icon(Icons.swap_horiz),
              onPressed: () => RoleSwitcherModal.show(context),
            ),
          IconButton(
            key: const Key('sign-out'),
            tooltip: text.signOut,
            icon: const Icon(Icons.logout),
            onPressed: () => ref.read(sessionControllerProvider.notifier).signOut(),
          ),
        ],
      ),
      body: body,
      bottomNavigationBar: wide
          ? null
          : _Bar(role: role, current: current, primary: primary, secondary: secondary),
    );
  }
}

/// Which destination the current location belongs to.
///
/// Longest prefix wins, because `/employee/history` also starts with `/employee`: the
/// shorter match would light up the Home tab while the person is reading their history.
AppScreen? _currentScreen(Role role, String location) {
  AppScreen? best;
  for (final AppScreen screen in destinationsFor(role)) {
    if (screen.isParameterised) {
      continue;
    }
    final bool matches =
        location == screen.path || location.startsWith('${screen.path}/');
    if (matches && (best == null || screen.path.length > best.path.length)) {
      best = screen;
    }
  }
  return best;
}

class _Bar extends StatelessWidget {
  const _Bar({
    required this.role,
    required this.current,
    required this.primary,
    required this.secondary,
  });

  final Role role;
  final AppScreen current;
  final List<AppScreen> primary;
  final List<AppScreen> secondary;

  @override
  Widget build(BuildContext context) {
    final AppText text = AppText.of(context);
    final int selected = primary.indexOf(current);
    return NavigationBar(
      key: Key('nav-bar-${role.wireName}'),
      // A screen reached from "More" selects "More" rather than nothing: a navigation
      // bar with no selection looks broken, and `selectedIndex` cannot be null.
      selectedIndex: selected >= 0 ? selected : primary.length,
      onDestinationSelected: (int index) {
        if (index < primary.length) {
          context.go(primary[index].path);
        } else {
          _showMore(context, role, secondary);
        }
      },
      destinations: <Widget>[
        for (final AppScreen screen in primary)
          NavigationDestination(
            key: Key('nav-${screen.id}'),
            icon: Icon(screen.icon),
            label: screen.label(text),
          ),
        NavigationDestination(
          key: const Key('nav-more'),
          icon: const Icon(Icons.more_horiz),
          label: text.more,
        ),
      ],
    );
  }
}

class _Rail extends StatelessWidget {
  const _Rail({
    required this.role,
    required this.current,
    required this.destinations,
  });

  final Role role;
  final AppScreen current;
  final List<AppScreen> destinations;

  @override
  Widget build(BuildContext context) {
    final AppText text = AppText.of(context);
    final int selected = destinations.indexOf(current);
    return NavigationRail(
      key: Key('nav-rail-${role.wireName}'),
      selectedIndex: selected >= 0 ? selected : 0,
      labelType: NavigationRailLabelType.all,
      onDestinationSelected: (int index) => context.go(destinations[index].path),
      destinations: <NavigationRailDestination>[
        for (final AppScreen screen in destinations)
          NavigationRailDestination(
            // `NavigationRailDestination` takes no key of its own, so the icon carries
            // it: tests still name a destination the same way in either layout.
            icon: Icon(screen.icon, key: Key('nav-${screen.id}')),
            label: Text(screen.label(text)),
          ),
      ],
    );
  }
}

void _showMore(BuildContext context, Role role, List<AppScreen> secondary) {
  showModalBottomSheet<void>(
    context: context,
    builder: (BuildContext sheetContext) {
      final AppText text = AppText.of(sheetContext);
      return SafeArea(
        key: const Key('more-sheet'),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            for (final AppScreen screen in secondary)
              ListTile(
                key: Key('more-${screen.id}'),
                leading: Icon(screen.icon),
                title: Text(screen.label(text)),
                onTap: () {
                  Navigator.of(sheetContext).pop();
                  context.go(screen.path);
                },
              ),
          ],
        ),
      );
    },
  );
}
