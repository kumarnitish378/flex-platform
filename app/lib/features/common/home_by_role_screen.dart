import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/session.dart';
import '../../l10n/app_localizations.dart';

/// The landing screen for whichever role is active (A01).
///
/// A placeholder with a real job: it proves the role-based routing works end to end,
/// and it is where each role's actual home screen lands - E-01, D-01, S-01 - as those
/// tasks are built. The `Key` is the screen id from `screens-by-role.md`, which is how
/// widget tests name screens (coding-standards.md section 3 rule 9).
class HomeByRoleScreen extends ConsumerWidget {
  const HomeByRoleScreen({required this.role, super.key});

  final Role role;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final AppText text = AppText.of(context);
    final Session session = ref.watch(sessionProvider);
    return Scaffold(
      key: Key('home-${role.wireName}'),
      appBar: AppBar(
        title: Text(text.appTitle),
        actions: <Widget>[
          if (session.canSwitchRole)
            IconButton(
              key: const Key('switch-role'),
              tooltip: text.switchRole,
              icon: const Icon(Icons.swap_horiz),
              onPressed: () {},
            ),
          IconButton(
            key: const Key('sign-out'),
            tooltip: text.signOut,
            icon: const Icon(Icons.logout),
            onPressed: () => ref.read(sessionProvider.notifier).signOut(),
          ),
        ],
      ),
      body: Center(child: Text(text.homeForRole(role.wireName))),
    );
  }
}
