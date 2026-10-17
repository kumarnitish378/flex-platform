import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:smart_cab_api/smart_cab_api.dart' as api;

import '../../data/api/ride_request_repository.dart';

/// Ride history screen (E-06).
///
/// Displays history list of past ride requests/trips up to 90 days.
class RideHistoryScreen extends ConsumerStatefulWidget {
  const RideHistoryScreen({super.key});

  @override
  ConsumerState<RideHistoryScreen> createState() => _RideHistoryScreenState();
}

class _RideHistoryScreenState extends ConsumerState<RideHistoryScreen> {
  bool _loading = true;
  List<api.RideRequest> _history = <api.RideRequest>[];

  @override
  void initState() {
    super.initState();
    _loadHistory();
  }

  Future<void> _loadHistory() async {
    try {
      final List<api.RideRequest> requests =
          await ref.read(rideRequestRepositoryProvider).getMyRequests();
      if (mounted) {
        setState(() {
          _history = requests;
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
    return Scaffold(
      key: const Key('E-06'),
      appBar: AppBar(title: const Text('Ride History')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _history.isEmpty
              ? const Center(child: Text('No ride history found.'))
              : ListView.builder(
                  key: const Key('history-list'),
                  itemCount: _history.length,
                  itemBuilder: (BuildContext context, int index) {
                    final api.RideRequest req = _history[index];
                    return ListTile(
                      leading: const Icon(Icons.history),
                      title: Text(req.landmark ?? 'Ride Request'),
                      subtitle: Text('${req.direction?.name} • ${req.status?.name}'),
                    );
                  },
                ),
    );
  }
}
