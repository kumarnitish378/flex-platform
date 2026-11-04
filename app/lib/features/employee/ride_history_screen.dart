import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:smart_cab_api/smart_cab_api.dart' as api;

import '../../data/api/ride_request_repository.dart';

/// Ride history screen (E-06 / Item 5).
///
/// Displays history list of past ride requests/trips up to 90 days with pull-to-refresh.
class RideHistoryScreen extends ConsumerStatefulWidget {
  const RideHistoryScreen({super.key});

  @override
  ConsumerState<RideHistoryScreen> createState() => _RideHistoryScreenState();
}

class _RideHistoryScreenState extends ConsumerState<RideHistoryScreen> {
  bool _loading = true;
  List<api.RideRequest> _history = <api.RideRequest>[];
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadHistory();
  }

  Future<void> _loadHistory() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final List<api.RideRequest> requests =
          await ref.read(rideRequestRepositoryProvider).getMyRequests();
      if (mounted) {
        setState(() {
          _history = requests;
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      key: const Key('E-06'),
      appBar: AppBar(title: const Text('Ride History')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _loadHistory,
              child: _error != null
                  ? ListView(
                      children: <Widget>[
                        const SizedBox(height: 100),
                        Center(
                          child: Text(
                            _error!,
                            style: TextStyle(color: Theme.of(context).colorScheme.error),
                          ),
                        ),
                      ],
                    )
                  : _history.isEmpty
                      ? ListView(
                          children: const <Widget>[
                            SizedBox(height: 100),
                            Center(child: Text('No ride history found.')),
                          ],
                        )
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
            ),
    );
  }
}
