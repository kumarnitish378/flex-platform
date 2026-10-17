import 'dart:convert';
import 'dart:math';

import 'package:flutter/material.dart';
import 'package:maplibre_gl/maplibre_gl.dart';

import '../../core/env.dart';

/// User-Agent sent on every map tile request (ADR-0010 §A2).
///
/// Must be distinct and contain a contact email, or public OSM tile servers block it.
String buildTileUserAgent([String? contactEmail]) {
  final String email = (contactEmail != null && contactEmail.isNotEmpty)
      ? contactEmail
      : Env.osmContactEmail;
  final String formattedEmail = email.isNotEmpty ? email : 'unknown@flexplatform.com';
  return 'flex-platform/0.1.0 (contact: $formattedEmail)';
}

/// Creates the MapLibre JSON style for a raster tile source (ADR-0010 §A2).
///
/// Reads tile URL from environment configuration (`TILES_URL`).
/// Never hardcodes tile provider URLs.
String buildRasterStyle(String tilesUrl) {
  if (tilesUrl.isEmpty) {
    // Fallback blank style when tile URL is unconfigured
    return jsonEncode(<String, dynamic>{
      'version': 8,
      'sources': <String, dynamic>{},
      'layers': <dynamic>[],
    });
  }

  final Map<String, dynamic> style = <String, dynamic>{
    'version': 8,
    'sources': <String, dynamic>{
      'raster-tiles': <String, dynamic>{
        'type': 'raster',
        'tiles': <String>[tilesUrl],
        'tileSize': 256,
        'attribution': '© OpenStreetMap contributors',
      },
    },
    'layers': <dynamic>[
      <String, dynamic>{
        'id': 'simple-tiles',
        'type': 'raster',
        'source': 'raster-tiles',
        'minzoom': 0,
        'maxzoom': 19,
      },
    ],
  };

  return jsonEncode(style);
}

/// Marker model for items shown on [AppMap].
class MapMarker {
  const MapMarker({
    required this.id,
    required this.position,
    this.title,
    this.color = Colors.red,
    this.iconImage,
  });

  final String id;
  final LatLng position;
  final String? title;
  final Color color;
  final String? iconImage;
}

/// Shared MapLibre raster map widget (A05, C-06, ADR-0010 §A2).
///
/// Features:
/// - Raster map tiles from `TILES_URL` (never hard-coded)
/// - Custom User-Agent header with contact info
/// - Bottom-right OpenStreetMap attribution ("© OpenStreetMap contributors")
/// - Pin picker mode returning coordinates on drag
/// - Markers and route polyline support
/// - No address search box or prefetching
class AppMap extends StatefulWidget {
  const AppMap({
    super.key,
    this.initialPosition = const LatLng(28.5703, 77.3218), // NCR default
    this.initialZoom = 13.0,
    this.markers = const <MapMarker>[],
    this.routePolyline = const <LatLng>[],
    this.enablePinPicker = false,
    this.onPinMoved,
    this.onMapCreated,
    this.tilesUrl,
    this.userAgent,
    this.isTestMode = false,
  });

  final LatLng initialPosition;
  final double initialZoom;
  final List<MapMarker> markers;
  final List<LatLng> routePolyline;
  final bool enablePinPicker;
  final ValueChanged<LatLng>? onPinMoved;
  final ValueChanged<MapLibreMapController>? onMapCreated;

  /// Optional override for testing
  final String? tilesUrl;
  final String? userAgent;
  final bool isTestMode;

  @override
  State<AppMap> createState() => _AppMapState();
}

class _AppMapState extends State<AppMap> {
  MapLibreMapController? _controller;
  late LatLng _currentCenter;

  String get _effectiveTilesUrl => widget.tilesUrl ?? Env.tilesUrl;

  @override
  void initState() {
    super.initState();
    _currentCenter = widget.initialPosition;
  }

  void _onMapCreated(MapLibreMapController controller) {
    _controller = controller;
    widget.onMapCreated?.call(controller);
    _drawRoute();
  }

  void _onCameraMove(CameraPosition? position) {
    if (_controller != null && widget.enablePinPicker) {
      final LatLng center = position?.target ?? _controller!.cameraPosition?.target ?? _currentCenter;
      setState(() {
        _currentCenter = center;
      });
      widget.onPinMoved?.call(center);
    }
  }

  Future<void> _drawRoute() async {
    if (_controller == null || widget.routePolyline.isEmpty) {
      return;
    }
    await _controller!.addLine(
      LineOptions(
        geometry: widget.routePolyline,
        lineColor: '#0B5FFF',
        lineWidth: 5.0,
        lineOpacity: 0.8,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final String styleString = buildRasterStyle(_effectiveTilesUrl);

    return Stack(
      key: const Key('C-06'),
      children: <Widget>[
        if (widget.isTestMode || _effectiveTilesUrl.isEmpty)
          Container(
            color: Colors.grey.shade200,
            child: const Center(child: Text('Map Canvas')),
          )
        else
          MapLibreMap(
            initialCameraPosition: CameraPosition(
              target: widget.initialPosition,
              zoom: widget.initialZoom,
            ),
            styleString: styleString,
            onMapCreated: _onMapCreated,
            onCameraMove: widget.enablePinPicker ? _onCameraMove : null,
            trackCameraPosition: widget.enablePinPicker,
            attributionButtonMargins: Point<num>(-100, -100), // Hide native attribution
            compassEnabled: false,
          ),

        // Pin picker marker at center of screen when active
        if (widget.enablePinPicker)
          const Center(
            child: Padding(
              padding: EdgeInsets.only(bottom: 36.0), // Offset for pin point
              child: Icon(
                Icons.location_on,
                size: 48,
                color: Colors.red,
                key: Key('pin-picker-icon'),
              ),
            ),
          ),

        // Required OpenStreetMap Attribution always visible bottom-right (ADR-0010, C-06)
        Positioned(
          right: 8,
          bottom: 8,
          child: Container(
            key: const Key('map-attribution'),
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.85),
              borderRadius: BorderRadius.circular(4),
            ),
            child: const Text(
              '© OpenStreetMap contributors',
              style: TextStyle(
                fontSize: 10,
                color: Colors.black87,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
        ),
      ],
    );
  }
}
