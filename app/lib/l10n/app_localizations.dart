import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_en.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppText
/// returned by `AppText.of(context)`.
///
/// Applications need to include `AppText.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'l10n/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppText.localizationsDelegates,
///   supportedLocales: AppText.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppText.supportedLocales
/// property.
abstract class AppText {
  AppText(String locale)
    : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppText of(BuildContext context) {
    return Localizations.of<AppText>(context, AppText)!;
  }

  static const LocalizationsDelegate<AppText> delegate = _AppTextDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates =
      <LocalizationsDelegate<dynamic>>[
        delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
      ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[Locale('en')];

  /// Shown on the splash screen and as the Android task name. The product name is not final (OQ-18), which is one reason every string lives here from day one.
  ///
  /// In en, this message translates to:
  /// **'Smart Cab'**
  String get appTitle;

  /// One line under the app name while the session is being restored.
  ///
  /// In en, this message translates to:
  /// **'Your cab, tracked'**
  String get splashTagline;

  /// Button on the login screen.
  ///
  /// In en, this message translates to:
  /// **'Sign in'**
  String get signIn;

  /// Placeholder on the login screen until A03 lands. Deliberately honest rather than a fake login.
  ///
  /// In en, this message translates to:
  /// **'Signing in arrives with the login task. Nothing here is faked, so there is no way in yet.'**
  String get signInNotReady;

  /// Label for the phone input field.
  ///
  /// In en, this message translates to:
  /// **'Phone number'**
  String get phoneNumber;

  /// Instruction text on the phone step of login.
  ///
  /// In en, this message translates to:
  /// **'Enter your phone number to sign in'**
  String get enterPhoneNumber;

  /// Button to request OTP code.
  ///
  /// In en, this message translates to:
  /// **'Send code'**
  String get sendCode;

  /// Heading for the OTP code entry step.
  ///
  /// In en, this message translates to:
  /// **'Enter verification code'**
  String get enterCode;

  /// Subtitle showing which phone number received the OTP.
  ///
  /// In en, this message translates to:
  /// **'Code sent to {phone}'**
  String codeSentTo(String phone);

  /// Button to submit the OTP verification code.
  ///
  /// In en, this message translates to:
  /// **'Verify code'**
  String get verifyCode;

  /// Button to resend the OTP code.
  ///
  /// In en, this message translates to:
  /// **'Resend code'**
  String get resendCode;

  /// Disabled button text during OTP resend countdown.
  ///
  /// In en, this message translates to:
  /// **'Resend code in {seconds}s'**
  String resendCodeIn(int seconds);

  /// Action to go back and edit the phone number.
  ///
  /// In en, this message translates to:
  /// **'Change phone number'**
  String get changePhone;

  /// Single error message shown when OTP verification fails for any reason (B03, OQ-24).
  ///
  /// In en, this message translates to:
  /// **'Invalid or expired code. Please try again.'**
  String get otpRejected;

  /// Error message when backend network request fails.
  ///
  /// In en, this message translates to:
  /// **'Could not reach the server. Please check your connection.'**
  String get authUnavailable;

  /// Error message when rate limit (429) is hit.
  ///
  /// In en, this message translates to:
  /// **'Too many requests. Please wait a moment.'**
  String get tooManyRequests;

  /// Error message when authenticated user has no roles.
  ///
  /// In en, this message translates to:
  /// **'Your account has no assigned roles. Please contact support.'**
  String get noRolesAssigned;

  /// Title for the role switcher bottom sheet or screen (C-03).
  ///
  /// In en, this message translates to:
  /// **'Select active role'**
  String get selectRole;

  /// Display name for Employee role.
  ///
  /// In en, this message translates to:
  /// **'Employee'**
  String get roleNameEmployee;

  /// Display name for Driver role.
  ///
  /// In en, this message translates to:
  /// **'Driver'**
  String get roleNameDriver;

  /// Display name for Supervisor role.
  ///
  /// In en, this message translates to:
  /// **'Supervisor'**
  String get roleNameSupervisor;

  /// Display name for Operator Admin role.
  ///
  /// In en, this message translates to:
  /// **'Operator Admin'**
  String get roleNameOperatorAdmin;

  /// Display name for Client Admin role.
  ///
  /// In en, this message translates to:
  /// **'Client Admin'**
  String get roleNameClientAdmin;

  /// Display name for Platform Admin role.
  ///
  /// In en, this message translates to:
  /// **'Platform Admin'**
  String get roleNamePlatformAdmin;

  /// Placeholder home screen heading until each role's screens are built.
  ///
  /// In en, this message translates to:
  /// **'Signed in as {role}'**
  String homeForRole(String role);

  /// Opens the role switcher. Only shown when the person holds more than one role.
  ///
  /// In en, this message translates to:
  /// **'Switch role'**
  String get switchRole;

  /// Ends the session. Also stops the driver's location service (coding-standards.md section 3 rule 6).
  ///
  /// In en, this message translates to:
  /// **'Sign out'**
  String get signOut;
}

class _AppTextDelegate extends LocalizationsDelegate<AppText> {
  const _AppTextDelegate();

  @override
  Future<AppText> load(Locale locale) {
    return SynchronousFuture<AppText>(lookupAppText(locale));
  }

  @override
  bool isSupported(Locale locale) =>
      <String>['en'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppTextDelegate old) => false;
}

AppText lookupAppText(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'en':
      return AppTextEn();
  }

  throw FlutterError(
    'AppText.delegate failed to load unsupported locale "$locale". This is likely '
    'an issue with the localizations generation tool. Please file an issue '
    'on GitHub with a reproducible sample app and the gen-l10n configuration '
    'that was used.',
  );
}
