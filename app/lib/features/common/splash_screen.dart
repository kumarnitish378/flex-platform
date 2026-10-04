import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/session.dart';
import '../../l10n/app_localizations.dart';

/// First frame, while the stored session is restored (A01).
///
/// It exists because the alternative is showing the login screen to somebody who is
/// already signed in, for however long the secure-storage read takes - a flash of the
/// wrong screen on every cold start. Restoring the session is A03's job; until then
/// this moves straight on, which is also what a genuinely signed-out user sees.
class SplashScreen extends ConsumerStatefulWidget {
  const SplashScreen({super.key});

  @override
  ConsumerState<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends ConsumerState<SplashScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _decide());
  }

  void _decide() {
    if (!mounted) {
      return;
    }
    final Session session = ref.read(sessionProvider);
    context.go(
      session.isSignedIn ? homeOf(session.activeRole) : '/login',
    );
  }

  @override
  Widget build(BuildContext context) {
    final AppText text = AppText.of(context);
    final ThemeData theme = Theme.of(context);
    return Scaffold(
      key: const Key('splash'),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[
            Icon(
              Icons.local_taxi,
              size: 72,
              color: theme.colorScheme.primary,
            ),
            const SizedBox(height: 16),
            Text(text.appTitle, style: theme.textTheme.headlineMedium),
            const SizedBox(height: 8),
            Text(text.splashTagline, style: theme.textTheme.bodyMedium),
          ],
        ),
      ),
    );
  }
}

/// Home for a role, without importing the router and creating a cycle.
String homeOf(Role? role) {
  switch (role) {
    case Role.driver:
      return '/driver';
    case Role.supervisor:
      return '/supervisor';
    case Role.operatorAdmin:
    case Role.platformAdmin:
      return '/admin';
    case Role.clientAdmin:
      return '/client';
    case Role.employee:
    case null:
      return '/employee';
  }
}
