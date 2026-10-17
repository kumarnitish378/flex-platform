import 'package:flutter/material.dart';

/// Background location permission explainer screen (D-02).
///
/// Explains why background location is required for driver duty tracking.
class PermissionExplainerScreen extends StatelessWidget {
  const PermissionExplainerScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);

    return Scaffold(
      key: const Key('D-02'),
      appBar: AppBar(title: const Text('Location Permission')),
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            Icon(
              Icons.location_on,
              size: 72,
              color: theme.colorScheme.primary,
            ),
            const SizedBox(height: 24),
            Text(
              'Background Location Required',
              textAlign: TextAlign.center,
              style: theme.textTheme.headlineSmall,
            ),
            const SizedBox(height: 16),
            Text(
              'Smart Cab needs background location access while you are ON DUTY to transmit GPS pings to supervisors and riders, even when the app is closed or in background.',
              textAlign: TextAlign.center,
              style: theme.textTheme.bodyMedium,
            ),
            const Spacer(),
            ElevatedButton(
              key: const Key('request-location-permission'),
              onPressed: () {
                Navigator.of(context).pop();
              },
              child: const Text('Grant Location Permission'),
            ),
          ],
        ),
      ),
    );
  }
}
