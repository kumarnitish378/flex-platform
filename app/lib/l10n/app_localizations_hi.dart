// ignore: unused_import
import 'package:intl/intl.dart' as intl;

import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Hindi (`hi`).
class AppTextHi extends AppText {
  AppTextHi([String locale = 'hi']) : super(locale);

  @override
  String get appTitle => 'स्मार्ट कैब';

  @override
  String get splashTagline => 'आपकी कैब, लाइव ट्रैकिंग';

  @override
  String get signIn => 'साइन इन करें';

  @override
  String get phoneNumber => 'फ़ोन नंबर';

  @override
  String get enterPhoneNumber => 'साइन इन करने के लिए अपना फ़ोन नंबर दर्ज करें';

  @override
  String get sendCode => 'कोड भेजें';

  @override
  String get enterCode => 'सत्यापन कोड दर्ज करें';

  @override
  String codeSentTo(String phone) {
    return '$phone पर कोड भेजा गया';
  }

  @override
  String get verifyCode => 'कोड सत्यापित करें';

  @override
  String get resendCode => 'पुनः कोड भेजें';

  @override
  String resendCodeIn(int seconds) {
    return '$seconds सेकंड में पुनः कोड भेजें';
  }

  @override
  String get changePhone => 'फ़ोन नंबर बदलें';

  @override
  String get otpRejected => 'अमान्य या अमान्य कोड। कृपया पुनः प्रयास करें।';

  @override
  String get authUnavailable => 'सर्वर से कनेक्ट नहीं हो सका। नेटवर्क जांचें।';

  @override
  String get tooManyRequests => 'अत्यधिक अनुरोध। कृपया कुछ समय प्रतीक्षा करें।';

  @override
  String get noRolesAssigned => 'आपके खाते में कोई भूमिका असाइन नहीं है।';

  @override
  String get selectRole => 'सक्रिय भूमिका चुनें';

  @override
  String get roleNameEmployee => 'कर्मचारी';

  @override
  String get roleNameDriver => 'ड्राइवर';

  @override
  String get roleNameSupervisor => 'सुपरवाइजर';

  @override
  String get roleNameOperatorAdmin => 'ऑपरेटर एडमिन';

  @override
  String get roleNameClientAdmin => 'क्लाइंट एडमिन';

  @override
  String get roleNamePlatformAdmin => 'प्लेटफॉर्म एडमिन';

  @override
  String get switchRole => 'भूमिका बदलें';

  @override
  String get signOut => 'साइन आउट करें';

  @override
  String get more => 'अधिक';

  @override
  String screenNotBuiltYet(String screen, String task) {
    return '$screen स्क्रीन कार्य $task के साथ उपलब्ध होगी।';
  }

  @override
  String get navHome => 'होम';

  @override
  String get navHistory => 'इतिहास';

  @override
  String get navSavedPlaces => 'स्थान';

  @override
  String get navRequestCab => 'कैब बुक करें';

  @override
  String get navRequestStatus => 'अनुरोध स्थिति';

  @override
  String get navLiveTracking => 'लाइव ट्रैकिंग';

  @override
  String get navRateTrip => 'मूल्यांकन करें';

  @override
  String get navProfile => 'प्रोफ़ाइल';

  @override
  String get navNotifications => 'सूचनाएं';

  @override
  String get navDuty => 'ड्यूटी';

  @override
  String get navLocationPermission => 'स्थान अनुमति';

  @override
  String get navTrips => 'ट्रिप';

  @override
  String get navTripDetail => 'ट्रिप विवरण';

  @override
  String get navNavigate => 'नेविगेट करें';

  @override
  String get navReportIssue => 'समस्या रिपोर्ट करें';

  @override
  String get navDispatchMap => 'मानचित्र';

  @override
  String get navPendingQueue => 'कतार';

  @override
  String get navAssign => 'असाइन करें';

  @override
  String get navTripsBoard => 'बोर्ड';

  @override
  String get navAlerts => 'अलर्ट';

  @override
  String get navRequestOnBehalf => 'किसी अन्य के लिए अनुरोध करें';

  @override
  String get navDashboard => 'डैशबोर्ड';

  @override
  String get navVehicles => 'वाहन';

  @override
  String get navDrivers => 'ड्राइवर';

  @override
  String get navClients => 'क्लाइंट';

  @override
  String get navUsers => 'उपयोगकर्ता';

  @override
  String get navReports => 'रिपोर्ट्स';

  @override
  String get navSettings => 'सेटिंग्स';

  @override
  String get navEmployees => 'कर्मचारी';

  @override
  String get navEmployeeForm => 'कर्मचारी फ़ॉर्म';
}
