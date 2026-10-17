import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:smart_cab_api/smart_cab_api.dart' as api;

import '../../data/api/driver_trips_repository.dart';

/// Supervisor trips board screen (S-04).
///
/// Displays active and completed trips board across fleet.
class TripsBoardScreen extends ConsumerStatefulWidget {
  const TripsBoardScreen({super.key});

  @override
  ConsumerState<TripsBoardScreen> createState() => _TripsBoardScreenState();
}

class _TripsBoardScreenState extends ConsumerState<TripsBoardScreen> {
  bool _loading = true;
  List<api.Trip> _trips = <api.Trip>[];

  @override
  void initState() {
    super.initState();
    _fetchTrips();
  }

  Future<void> _fetchTrips() async {
    try {
      final List<api.Trip> list =
          await ref.read(driverTripsRepositoryProvider).getTrips();
      if (mounted) {
        setState(() {
          _trips = list;
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
      key: const Key('S-04'),
      appBar: AppBar(title: const Text('Trips Board')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _trips.isEmpty
              ? const Center(child: Text('No active trips on board.'))
              : ListView.builder(
                  key: const Key('trips-board-list'),
                  itemCount: _trips.length,
                  itemBuilder: (BuildContext context, int index) {
                    final api.Trip t = _trips[index];
                    return ListTile(
                      leading: const Icon(Icons.route),
                      title: Text('Trip #${t.id?.substring(0, 8) ?? ''}'),
                      subtitle: Text('Status: ${t.status?.name} • Stops: ${t.stops?.length ?? 0}'),
                    );
                  },
                ),
    );
  }
}
