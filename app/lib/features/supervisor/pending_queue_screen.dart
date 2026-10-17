import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:smart_cab_api/smart_cab_api.dart' as api;

import '../../data/api/ride_request_repository.dart';

/// Supervisor pending queue screen (S-02).
///
/// Features list of unassigned ride requests with live waiting times, lateness
/// indicator (escalatedAt), urgency chip, and "Assign" action button.
class PendingQueueScreen extends ConsumerStatefulWidget {
  const PendingQueueScreen({super.key});

  @override
  ConsumerState<PendingQueueScreen> createState() => _PendingQueueScreenState();
}

class _PendingQueueScreenState extends ConsumerState<PendingQueueScreen> {
  bool _loading = true;
  List<api.RideRequest> _requests = <api.RideRequest>[];

  @override
  void initState() {
    super.initState();
    _fetchQueue();
  }

  Future<void> _fetchQueue() async {
    try {
      final List<api.RideRequest> list =
          await ref.read(rideRequestRepositoryProvider).getMyRequests();
      if (mounted) {
        setState(() {
          _requests = list;
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

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);

    return Scaffold(
      key: const Key('S-02'),
      appBar: AppBar(title: const Text('Pending Requests')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _requests.isEmpty
              ? const Center(child: Text('No pending requests.'))
              : ListView.builder(
                  key: const Key('pending-queue-list'),
                  itemCount: _requests.length,
                  itemBuilder: (BuildContext context, int index) {
                    final api.RideRequest req = _requests[index];
                    final bool isLate = req.escalatedAt != null;
                    final String reqId = req.id ?? '';

                    return Card(
                      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                      elevation: isLate ? 4 : 2,
                      color: isLate ? Colors.red.shade50 : null,
                      child: ListTile(
                        leading: CircleAvatar(
                          backgroundColor: isLate
                              ? Colors.red
                              : theme.colorScheme.primaryContainer,
                          child: Icon(
                            isLate ? Icons.priority_high : Icons.hourglass_empty,
                            color: isLate ? Colors.white : theme.colorScheme.primary,
                          ),
                        ),
                        title: Text('Request #${reqId.length > 8 ? reqId.substring(0, 8) : reqId}'),
                        subtitle: Text(
                          'Landmark: ${req.landmark ?? 'Map Pin'}\nDirection: ${req.direction?.name}',
                        ),
                        isThreeLine: true,
                        trailing: ElevatedButton(
                          key: Key('assign-button-$reqId'),
                          onPressed: () {
                            context.go('/supervisor/assign/$reqId');
                          },
                          child: const Text('Assign'),
                        ),
                      ),
                    );
                  },
                ),
    );
  }
}
