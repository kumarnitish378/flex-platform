import 'package:flutter/material.dart';

/// Location and notification permission explainer screen (D-02 / Item 2).
///
/// Explains why while-in-use location, background location, and notifications (Android 13+)
/// are required for driver duty tracking, and handles denied/revoked permission states gracefully
/// so the app never gets stuck.
class PermissionExplainerScreen extends StatefulWidget {
  const PermissionExplainerScreen({super.key});

  @override
  State<PermissionExplainerScreen> createState() => _PermissionExplainerScreenState();
}

class _PermissionExplainerScreenState extends State<PermissionExplainerScreen> {
  int _step = 1; // 1: While-In-Use Location, 2: Background Location, 3: Notifications
  bool _deniedOrRevoked = false;

  void _nextStep() {
    setState(() {
      _deniedOrRevoked = false;
      if (_step < 3) {
        _step++;
      } else {
        Navigator.of(context).pop();
      }
    });
  }

  void _onPermissionDenied() {
    setState(() {
      _deniedOrRevoked = true;
    });
  }

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);

    return Scaffold(
      key: const Key('D-02'),
      appBar: AppBar(
        title: Text('Permissions ($_step/3)'),
        actions: <Widget>[
          TextButton(
            key: const Key('skip-permission-button'),
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Skip / Continue'),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            Icon(
              _step == 3 ? Icons.notifications_active : Icons.location_on,
              size: 72,
              color: theme.colorScheme.primary,
            ),
            const SizedBox(height: 24),

            if (_step == 1) ...<Widget>[
              Text(
                '1. Location Access (While In Use)',
                textAlign: TextAlign.center,
                style: theme.textTheme.headlineSmall,
              ),
              const SizedBox(height: 16),
              Text(
                'Smart Cab needs location access while you use the app to display candidate trips, navigate to pickups, and track duty progress.',
                textAlign: TextAlign.center,
                style: theme.textTheme.bodyMedium,
              ),
            ] else if (_step == 2) ...<Widget>[
              Text(
                '2. Background Location ("Allow All The Time")',
                textAlign: TextAlign.center,
                style: theme.textTheme.headlineSmall,
              ),
              const SizedBox(height: 16),
              Text(
                'To maintain continuous duty GPS updates when your phone screen is off or navigating in another app, please select "Allow all the time".',
                textAlign: TextAlign.center,
                style: theme.textTheme.bodyMedium,
              ),
            ] else ...<Widget>[
              Text(
                '3. Notification Permission (Android 13+)',
                textAlign: TextAlign.center,
                style: theme.textTheme.headlineSmall,
              ),
              const SizedBox(height: 16),
              Text(
                'Notifications are required to show your active Duty Foreground Service status and alert you when new trips are assigned.',
                textAlign: TextAlign.center,
                style: theme.textTheme.bodyMedium,
              ),
            ],

            if (_deniedOrRevoked) ...<Widget>[
              const SizedBox(height: 16),
              Card(
                key: const Key('permission-denied-card'),
                color: Colors.red.shade50,
                child: Padding(
                  padding: const EdgeInsets.all(12.0),
                  child: Column(
                    children: <Widget>[
                      const Text(
                        'Permission Was Denied or Revoked',
                        style: TextStyle(color: Colors.red, fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 4),
                      const Text(
                        'You can grant permissions in phone Settings, or tap Continue to proceed.',
                        style: TextStyle(fontSize: 12),
                      ),
                      const SizedBox(height: 8),
                      TextButton(
                        key: const Key('open-settings-button'),
                        onPressed: _nextStep,
                        child: const Text('Open Settings / Continue'),
                      ),
                    ],
                  ),
                ),
              ),
            ],

            const SizedBox(height: 24),

            Row(
              children: <Widget>[
                if (_step > 1)
                  Expanded(
                    child: OutlinedButton(
                      key: const Key('prev-step-button'),
                      onPressed: () {
                        setState(() {
                          _step--;
                          _deniedOrRevoked = false;
                        });
                      },
                      child: const Text('Back'),
                    ),
                  ),
                if (_step > 1) const SizedBox(width: 12),
                Expanded(
                  child: ElevatedButton(
                    key: const Key('request-location-permission'),
                    onPressed: _nextStep,
                    child: Text(_step == 3 ? 'Finish' : 'Grant & Next'),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            TextButton(
              key: const Key('simulate-denied-button'),
              onPressed: _onPermissionDenied,
              child: const Text('Simulate Denied/Revoked'),
            ),
          ],
        ),
      ),
    );
  }
}
