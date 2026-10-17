import 'package:flutter/material.dart';
import 'package:maplibre_gl/maplibre_gl.dart' as maplibre;

import '../common/app_map.dart';

/// Navigation map screen for drivers (D-05).
///
/// Features in-app route navigation map and "Open external nav" button.
class NavigationMapScreen extends StatelessWidget {
  const NavigationMapScreen({
    required this.tripId,
    super.key,
    this.isTestMode = false,
  });

  final String tripId;
  final bool isTestMode;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      key: const Key('D-05'),
      appBar: AppBar(title: const Text('Navigation')),
      body: Stack(
        children: <Widget>[
          AppMap(
            key: const Key('navigation-map'),
            isTestMode: isTestMode,
            initialPosition: const maplibre.LatLng(28.5703, 77.3218),
            routePolyline: const <maplibre.LatLng>[
              maplibre.LatLng(28.5703, 77.3218),
              maplibre.LatLng(28.5750, 77.3250),
              maplibre.LatLng(28.5800, 77.3300),
            ],
          ),

          // Open external nav CTA button at bottom
          Positioned(
            left: 16,
            right: 16,
            bottom: 24,
            child: ElevatedButton.icon(
              key: const Key('open-external-nav'),
              style: ElevatedButton.styleFrom(
                minimumSize: const Size.fromHeight(56),
              ),
              onPressed: () {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Opening external navigation...')),
                );
              },
              icon: const Icon(Icons.open_in_new),
              label: const Text('Open External Nav (Google Maps / OSM)'),
            ),
          ),
        ],
      ),
    );
  }
}
