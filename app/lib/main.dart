import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'core/router.dart';
import 'core/theme.dart';
import 'l10n/app_localizations.dart';

void main() {
  runApp(const ProviderScope(child: SmartCabApp()));
}

/// One app for every role (ADR-0003).
class SmartCabApp extends ConsumerWidget {
  const SmartCabApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final GoRouter router = ref.watch(routerProvider);
    return MaterialApp.router(
      routerConfig: router,
      onGenerateTitle: (BuildContext context) => AppText.of(context).appTitle,
      theme: AppTheme.light(),
      darkTheme: AppTheme.dark(),
      localizationsDelegates: const <LocalizationsDelegate<Object>>[
        AppText.delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      supportedLocales: AppText.supportedLocales,
      debugShowCheckedModeBanner: false,
    );
  }
}
