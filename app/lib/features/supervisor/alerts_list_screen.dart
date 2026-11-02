import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:smart_cab_api/smart_cab_api.dart' as api;

import '../../data/api/supervisor_repository.dart';

/// Supervisor alerts list screen (S-07 / Item 5).
///
/// Shows raised alerts, SOS notifications, and mode-switch prompts with acknowledge/resolve actions
/// and pull-to-refresh.
class AlertsListScreen extends ConsumerStatefulWidget {
  const AlertsListScreen({super.key});

  @override
  ConsumerState<AlertsListScreen> createState() => _AlertsListScreenState();
}

class _AlertsListScreenState extends ConsumerState<AlertsListScreen> {
  bool _loading = true;
  List<api.Alert> _alerts = <api.Alert>[];
  String? _error;

  @override
  void initState() {
    super.initState();
    _fetchAlerts();
  }

  Future<void> _fetchAlerts() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final List<api.Alert> list =
          await ref.read(supervisorRepositoryProvider).getAlerts();
      if (mounted) {
        setState(() {
          _alerts = list;
          _loading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _loading = false;
          _error = e.toString();
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
    final ThemeData theme = Theme.of(context);

    final List<api.Alert> activeAlerts = _alerts
        .where((api.Alert a) => a.status != api.AlertStatusEnum.resolved)
        .toList();

    return Scaffold(
      key: const Key('S-07'),
      appBar: AppBar(title: const Text('Alerts & SOS')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _fetchAlerts,
              child: _error != null
                  ? ListView(
                      children: <Widget>[
                        const SizedBox(height: 100),
                        Center(
                          child: Text(
                            _error!,
                            style: TextStyle(color: theme.colorScheme.error),
                          ),
                        ),
                      ],
                    )
                  : activeAlerts.isEmpty
                      ? ListView(
                          children: const <Widget>[
                            SizedBox(height: 100),
                            Center(child: Text('No active alerts.')),
                          ],
                        )
                      : ListView.builder(
                          key: const Key('alerts-list'),
                          itemCount: activeAlerts.length,
                          itemBuilder: (BuildContext context, int index) {
                            final api.Alert alert = activeAlerts[index];
                            final String alertId = alert.id ?? '';
                            final bool isCritical =
                                alert.severity == api.AlertSeverityEnum.critical;
                            final bool isModePrompt =
                                alert.type == api.AlertTypeEnum.modePrompt;

                            if (isModePrompt) {
                              return Card(
                                key: Key('mode-prompt-card-$alertId'),
                                margin:
                                    const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                                color: Colors.amber.shade50,
                                child: Padding(
                                  padding: const EdgeInsets.all(16.0),
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: <Widget>[
                                      Row(
                                        children: <Widget>[
                                          const Icon(Icons.mode_standby, color: Colors.amber),
                                          const SizedBox(width: 8),
                                          Text(
                                            'Mode Switch Prompt',
                                            style: theme.textTheme.titleMedium?.copyWith(
                                              fontWeight: FontWeight.bold,
                                              color: Colors.amber.shade900,
                                            ),
                                          ),
                                        ],
                                      ),
                                      const SizedBox(height: 8),
                                      const Text(
                                        'Automated dispatch thresholds exceeded (e.g. rejections/surge). System suggests switching to Manual mode.',
                                      ),
                                      const SizedBox(height: 12),
                                      Row(
                                        mainAxisAlignment: MainAxisAlignment.end,
                                        children: <Widget>[
                                          OutlinedButton(
                                            onPressed: () => _resolve(alertId),
                                            child: const Text('Dismiss'),
                                          ),
                                          const SizedBox(width: 12),
                                          ElevatedButton(
                                            key: Key('switch-to-manual-$alertId'),
                                            onPressed: () async {
                                              await _resolve(alertId);
                                              if (context.mounted) {
                                                ScaffoldMessenger.of(context).showSnackBar(
                                                  const SnackBar(
                                                    content:
                                                        Text('Switched scope to Manual mode'),
                                                  ),
                                                );
                                              }
                                            },
                                            child: const Text('Switch to Manual'),
                                          ),
                                        ],
                                      ),
                                    ],
                                  ),
                                ),
                              );
                            }

                            return Card(
                              margin:
                                  const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                              color: isCritical ? Colors.red.shade50 : null,
                              child: ListTile(
                                leading: Icon(
                                  isCritical ? Icons.warning_amber : Icons.notifications,
                                  color: isCritical ? Colors.red : Colors.orange,
                                  size: 36,
                                ),
                                title: Text('Alert (${alert.type?.name ?? 'System'})'),
                                subtitle: Text(
                                    'Severity: ${alert.severity?.name}\nStatus: ${alert.status?.name}'),
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
            ),
    );
  }
}
