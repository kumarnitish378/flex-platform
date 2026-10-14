import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/session.dart';
import '../../core/session_controller.dart';
import '../../l10n/app_localizations.dart';

/// Extension to get user-visible name for a Role.
extension RoleNameLocalization on Role {
  String displayName(AppText text) {
    return switch (this) {
      Role.employee => text.roleNameEmployee,
      Role.driver => text.roleNameDriver,
      Role.supervisor => text.roleNameSupervisor,
      Role.operatorAdmin => text.roleNameOperatorAdmin,
      Role.clientAdmin => text.roleNameClientAdmin,
      Role.platformAdmin => text.roleNamePlatformAdmin,
    };
  }
}

/// Role switcher modal bottom sheet (C-03).
///
/// Shown when a user holds more than one role (`session.canSwitchRole`).
/// Sets the active role for the current session and remembers it for future launches.
class RoleSwitcherModal extends ConsumerWidget {
  const RoleSwitcherModal({super.key});

  static Future<void> show(BuildContext context) {
    return showModalBottomSheet<void>(
      context: context,
      builder: (_) => const RoleSwitcherModal(),
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final AppText text = AppText.of(context);
    final Session session = ref.watch(sessionProvider);

    return Container(
      key: const Key('C-03'),
      padding: const EdgeInsets.symmetric(vertical: 24, horizontal: 16),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(
            text.selectRole,
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const SizedBox(height: 16),
          for (final Role role in session.roles)
            ListTile(
              key: Key('role-option-${role.wireName}'),
              title: Text(role.displayName(text)),
              trailing: role == session.activeRole
                  ? Icon(
                      Icons.check,
                      color: Theme.of(context).colorScheme.primary,
                    )
                  : null,
              onTap: () async {
                await ref.read(sessionControllerProvider.notifier).switchTo(role);
                if (context.mounted) {
                  Navigator.of(context).pop();
                }
              },
            ),
        ],
      ),
    );
  }
}
