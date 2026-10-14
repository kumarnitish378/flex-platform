/// The frame a screen pushed on top of a destination gets (A04).
///
/// Detail screens - a request form, a trip, an assign panel - sit outside the shell on
/// purpose. They are somewhere a person went, not somewhere they are, so they get a
/// back arrow rather than the navigation bar: a bottom bar on a trip detail invites a
/// tap that silently abandons half-entered work.
library;

import 'package:flutter/material.dart';

import '../../core/screens.dart';
import '../../l10n/app_localizations.dart';

class DetailScaffold extends StatelessWidget {
  const DetailScaffold({required this.screen, required this.body, super.key});

  final AppScreen screen;
  final Widget body;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(screen.label(AppText.of(context)))),
      body: body,
    );
  }
}
