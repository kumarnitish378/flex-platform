import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:smart_cab_api/smart_cab_api.dart' as api;

import '../../data/api/driver_trips_repository.dart';

/// Supervisor trips board screen (S-04).
///
/// Displays active and completed trips board across fleet with pooled trip rider details.
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
    final ThemeData theme = Theme.of(context);

    return Scaffold(
      key: const Key('S-04'),
      appBar: AppBar(title: const Text('Trips Board')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _trips.isEmpty
              ? const Center(child: Text('No active trips on board.'))
              : ListView.builder(
                  key: const Key('trips-board-list'),
                  padding: const EdgeInsets.all(16.0),
                  itemCount: _trips.length,
                  itemBuilder: (BuildContext context, int index) {
                    final api.Trip t = _trips[index];
                    final String tripShortId =
                        t.id != null && t.id!.length > 8 ? t.id!.substring(0, 8) : (t.id ?? '');
                    final List<api.TripRider> riders = t.riders?.toList() ?? <api.TripRider>[];
                    final bool isPooled = riders.length > 1;

                    return Card(
                      margin: const EdgeInsets.only(bottom: 12.0),
                      elevation: isPooled ? 3 : 1,
                      child: Padding(
                        padding: const EdgeInsets.all(16.0),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: <Widget>[
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: <Widget>[
                                Text(
                                  'Trip #$tripShortId',
                                  style: theme.textTheme.titleMedium
                                      ?.copyWith(fontWeight: FontWeight.bold),
                                ),
                                Chip(
                                  label: Text(
                                    isPooled
                                        ? 'Pooled (${riders.length} riders)'
                                        : 'Exclusive',
                                  ),
                                  backgroundColor: isPooled
                                      ? theme.colorScheme.primaryContainer
                                      : theme.colorScheme.surfaceContainerHighest,
                                ),
                              ],
                            ),
                            const SizedBox(height: 8),
                            Text('Status: ${t.status?.name ?? 'Dispatched'}'),
                            const SizedBox(height: 8),

                            // Riders list with added detour minutes (A17)
                            if (riders.isNotEmpty) ...<Widget>[
                              const Text('Riders in Stop Order:',
                                  style: TextStyle(fontWeight: FontWeight.bold)),
                              const SizedBox(height: 4),
                              Wrap(
                                spacing: 8.0,
                                children: <Widget>[
                                  for (final api.TripRider r in riders)
                                    Chip(
                                      avatar: const Icon(Icons.person, size: 16),
                                      label: Text(
                                        '${r.riderFirstName ?? 'Rider'}${r.addedMinutes != null ? ' (+${r.addedMinutes}m)' : ''}',
                                      ),
                                    ),
                                ],
                              ),
                            ],
                          ],
                        ),
                      ),
                    );
                  },
                ),
    );
  }
}
