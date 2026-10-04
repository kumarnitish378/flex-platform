// ignore: unused_import
import 'package:intl/intl.dart' as intl;

import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppTextEn extends AppText {
  AppTextEn([String locale = 'en']) : super(locale);

  @override
  String get appTitle => 'Smart Cab';

  @override
  String get splashTagline => 'Your cab, tracked';

  @override
  String get signIn => 'Sign in';

  @override
  String get signInNotReady =>
      'Signing in arrives with the login task. Nothing here is faked, so there is no way in yet.';

  @override
  String homeForRole(String role) {
    return 'Signed in as $role';
  }

  @override
  String get switchRole => 'Switch role';

  @override
  String get signOut => 'Sign out';
}
