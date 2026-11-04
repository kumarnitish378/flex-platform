import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('A16: Every key in app_en.arb exists in app_hi.arb', () {
    final File enFile = File('lib/l10n/app_en.arb');
    final File hiFile = File('lib/l10n/app_hi.arb');

    expect(enFile.existsSync(), isTrue, reason: 'app_en.arb must exist');
    expect(hiFile.existsSync(), isTrue, reason: 'app_hi.arb must exist');

    final Map<String, dynamic> enJson =
        jsonDecode(enFile.readAsStringSync()) as Map<String, dynamic>;
    final Map<String, dynamic> hiJson =
        jsonDecode(hiFile.readAsStringSync()) as Map<String, dynamic>;

    final Set<String> enKeys = enJson.keys
        .where((String k) => !k.startsWith('@'))
        .toSet();
    final Set<String> hiKeys = hiJson.keys
        .where((String k) => !k.startsWith('@'))
        .toSet();

    final Set<String> missingInHindi = enKeys.difference(hiKeys);

    expect(
      missingInHindi,
      isEmpty,
      reason: 'The following keys are missing in app_hi.arb: $missingInHindi',
    );
  });
}
