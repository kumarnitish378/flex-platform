import 'package:flutter_test/flutter_test.dart';
import 'package:smart_cab/core/env.dart';

void main() {
  group('Item 4: Release build default configuration assertions', () {
    test('APP_TESTING defaults to false in standard builds', () {
      expect(Env.isAppTesting, isFalse);
    });

    test('Default API Base URL is configured', () {
      expect(Env.apiBaseUrl, isNotEmpty);
    });
  });
}
