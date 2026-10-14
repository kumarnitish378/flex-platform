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
  String get phoneNumber => 'Phone number';

  @override
  String get enterPhoneNumber => 'Enter your phone number to sign in';

  @override
  String get sendCode => 'Send code';

  @override
  String get enterCode => 'Enter verification code';

  @override
  String codeSentTo(String phone) {
    return 'Code sent to $phone';
  }

  @override
  String get verifyCode => 'Verify code';

  @override
  String get resendCode => 'Resend code';

  @override
  String resendCodeIn(int seconds) {
    return 'Resend code in ${seconds}s';
  }

  @override
  String get changePhone => 'Change phone number';

  @override
  String get otpRejected => 'Invalid or expired code. Please try again.';

  @override
  String get authUnavailable =>
      'Could not reach the server. Please check your connection.';

  @override
  String get tooManyRequests => 'Too many requests. Please wait a moment.';

  @override
  String get noRolesAssigned =>
      'Your account has no assigned roles. Please contact support.';

  @override
  String get selectRole => 'Select active role';

  @override
  String get roleNameEmployee => 'Employee';

  @override
  String get roleNameDriver => 'Driver';

  @override
  String get roleNameSupervisor => 'Supervisor';

  @override
  String get roleNameOperatorAdmin => 'Operator Admin';

  @override
  String get roleNameClientAdmin => 'Client Admin';

  @override
  String get roleNamePlatformAdmin => 'Platform Admin';

  @override
  String homeForRole(String role) {
    return 'Signed in as $role';
  }

  @override
  String get switchRole => 'Switch role';

  @override
  String get signOut => 'Sign out';
}
