import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:maplibre_gl/maplibre_gl.dart';
import 'package:smart_cab/features/common/app_map.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUpAll(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
      const MethodChannel('plugins.flutter.io/maplibre_gl'),
      (MethodCall methodCall) async {
        return null;
      },
    );
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
      const MethodChannel('plugins.flutter.io/maplibre_gl_0'),
      (MethodCall methodCall) async {
        return null;
      },
    );
  });
  group('A05: AppMap widget & policy compliance', () {
    testWidgets('renders map with C-06 key and bottom-right attribution', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: AppMap(
              tilesUrl: 'http://test-tiles.local/{z}/{x}/{y}.png',
              isTestMode: true,
            ),
          ),
        ),
      );

      expect(find.byKey(const Key('C-06')), findsOneWidget);
      expect(find.byKey(const Key('map-attribution')), findsOneWidget);
      expect(find.text('© OpenStreetMap contributors'), findsOneWidget);
    });

    testWidgets('no address search field is present on AppMap (ADR-0010 A1)', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: AppMap(
              tilesUrl: 'http://test-tiles.local/{z}/{x}/{y}.png',
              isTestMode: true,
            ),
          ),
        ),
      );

      expect(find.byType(TextField), findsNothing);
      expect(find.byType(SearchBar), findsNothing);
      expect(find.text('Search'), findsNothing);
    });

    testWidgets('pin picker displays center pin when enabled', (
      WidgetTester tester,
    ) async {
      LatLng? movedLocation;

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AppMap(
              tilesUrl: 'http://test-tiles.local/{z}/{x}/{y}.png',
              isTestMode: true,
              enablePinPicker: true,
              onPinMoved: (LatLng loc) {
                movedLocation = loc;
              },
            ),
          ),
        ),
      );

      expect(find.byKey(const Key('pin-picker-icon')), findsOneWidget);
      expect(movedLocation, isNull);
    });

    test('buildTileUserAgent formats user agent with contact email', () {
      final String userAgent = buildTileUserAgent('dev@flexplatform.com');
      expect(userAgent, contains('flex-platform/0.1.0'));
      expect(userAgent, contains('contact: dev@flexplatform.com'));
    });

    test('buildRasterStyle injects tilesUrl into style JSON', () {
      const String testUrl = 'http://test-tiles.local/{z}/{x}/{y}.png';
      final String styleJson = buildRasterStyle(testUrl);

      final Map<String, dynamic> decoded = jsonDecode(styleJson) as Map<String, dynamic>;
      final Map<String, dynamic> sources = decoded['sources'] as Map<String, dynamic>;
      final Map<String, dynamic> rasterTiles = sources['raster-tiles'] as Map<String, dynamic>;
      final List<dynamic> tiles = rasterTiles['tiles'] as List<dynamic>;

      expect(decoded['version'], 8);
      expect(tiles, contains(testUrl));
      expect(
        rasterTiles['attribution'],
        '© OpenStreetMap contributors',
      );
    });

    test('buildRasterStyle returns empty style when tilesUrl is empty', () {
      final String styleJson = buildRasterStyle('');
      final Map<String, dynamic> decoded = jsonDecode(styleJson) as Map<String, dynamic>;

      expect(decoded['sources'], isEmpty);
      expect(decoded['layers'], isEmpty);
    });
  });
}
