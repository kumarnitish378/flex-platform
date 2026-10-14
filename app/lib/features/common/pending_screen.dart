/// A screen the navigation reaches but whose task has not been built yet (A04).
///
/// It exists because A04's job is the navigation, not the screens: every role needs
/// somewhere for each of its destinations to land, and the alternative - routing to a
/// screen that fakes a trip or a vehicle so the tab looks finished - is the one thing
/// this project will not do (AGENTS.md rule 10). So a missing screen says which task
/// builds it and nothing else.
///
/// Each of A06 to A12 replaces these with real screens, keeping the `Key`.
library;

import 'package:flutter/material.dart';

import '../../core/screens.dart';
import '../../l10n/app_localizations.dart';

class PendingScreen extends StatelessWidget {
  const PendingScreen({required this.screen, super.key});

  final AppScreen screen;

  @override
  Widget build(BuildContext context) {
    final AppText text = AppText.of(context);
    final ThemeData theme = Theme.of(context);
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[
            Icon(screen.icon, size: 56, color: theme.colorScheme.outline),
            const SizedBox(height: 16),
            Text(
              screen.label(text),
              style: theme.textTheme.titleLarge,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              text.screenNotBuiltYet(screen.id, screen.task),
              style: theme.textTheme.bodyMedium?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}
