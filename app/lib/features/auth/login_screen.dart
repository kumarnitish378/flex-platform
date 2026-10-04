import 'package:flutter/material.dart';

import '../../l10n/app_localizations.dart';

/// Phone + OTP sign-in (A03).
///
/// Deliberately not a working login. The backend's OTP flow answers 202 to every
/// request and gives one indistinguishable error for wrong, expired, missing and
/// locked-out codes (B03, OQ-24), and getting that wrong in the client is how a login
/// screen becomes a directory of an operator's staff. It is built properly in A03
/// rather than stubbed here.
class LoginScreen extends StatelessWidget {
  const LoginScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final AppText text = AppText.of(context);
    return Scaffold(
      key: const Key('login'),
      appBar: AppBar(title: Text(text.signIn)),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Center(
          child: Text(
            text.signInNotReady,
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodyLarge,
          ),
        ),
      ),
    );
  }
}
