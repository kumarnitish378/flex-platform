import 'package:flutter/material.dart';

/// Offline banner widget (D-07).
///
/// Displayed when the driver device goes offline, showing count of queued events.
class OfflineBanner extends StatelessWidget {
  const OfflineBanner({
    required this.queuedCount,
    super.key,
  });

  final int queuedCount;

  @override
  Widget build(BuildContext context) {
    return Material(
      key: const Key('D-07'),
      color: Colors.red.shade800,
      elevation: 4,
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
        child: Row(
          key: const Key('offline-banner'),
          children: <Widget>[
            const Icon(Icons.wifi_off, color: Colors.white),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                'Offline • $queuedCount events queued for sync',
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
