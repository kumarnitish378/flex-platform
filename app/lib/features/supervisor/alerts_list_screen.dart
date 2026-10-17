import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:smart_cab_api/smart_cab_api.dart' as api;

import '../../data/api/supervisor_repository.dart';

/// Supervisor alerts list screen (S-07).
///
/// Shows raised alerts and SOS notifications with acknowledge/resolve actions.
class AlertsListScreen extends ConsumerStatefulWidget {
  const AlertsListScreen({super.key});

  @override
  ConsumerState<AlertsListScreen> createState() => _AlertsListScreenState();
}

class _AlertsListScreenState extends ConsumerState<AlertsListScreen> {
  bool _loading = true;
  List<api.Alert> _alerts = <api.Alert>[];

  @override
  void initState() {
    super.initState();
    _fetchAlerts();
  }

  Future<void> _fetchAlerts() async {
    try {
      final List<api.Alert> list =
          await ref.read(supervisorRepositoryProvider).getAlerts();
      if (mounted) {
        setState(() {
          _alerts = list;
          _loading = false;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _loading = false;
        });
      }
    }
  }

  Future<void> _acknowledge(String alertId) async {
    await ref.read(supervisorRepositoryProvider).acknowledgeAlert(alertId);
    _fetchAlerts();
  }

  Future<void> _resolve(String alertId) async {
    await ref.read(supervisorRepositoryProvider).resolveAlert(alertId);
    _fetchAlerts();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      key: const Key('S-07'),
      appBar: AppBar(title: const Text('Alerts & SOS')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _alerts.isEmpty
              ? const Center(child: Text('No active alerts.'))
              : ListView.builder(
                  key: const Key('alerts-list'),
                  itemCount: _alerts.length,
                  itemBuilder: (BuildContext context, int index) {
                    final api.Alert alert = _alerts[index];
                    final String alertId = alert.id ?? '';
                    final bool isCritical = alert.severity == api.AlertSeverityEnum.critical;

                    return Card(
                      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                      color: isCritical ? Colors.red.shade50 : null,
                      child: ListTile(
                        leading: Icon(
                          isCritical ? Icons.warning_amber : Icons.notifications,
                          color: isCritical ? Colors.red : Colors.orange,
                          size: 36,
                        ),
                        title: Text('Alert (${alert.type?.name ?? 'System'})'),
                        subtitle: Text('Severity: ${alert.severity?.name}\nStatus: ${alert.status?.name}'),
                        isThreeLine: true,
                        trailing: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: <Widget>[
                            IconButton(
                              key: Key('ack-$alertId'),
                              icon: const Icon(Icons.check, color: Colors.blue),
                              tooltip: 'Acknowledge',
                              onPressed: () => _acknowledge(alertId),
                            ),
                            IconButton(
                              key: Key('resolve-$alertId'),
                              icon: const Icon(Icons.done_all, color: Colors.green),
                              tooltip: 'Resolve',
                              onPressed: () => _resolve(alertId),
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
    );
  }
}
