import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:smart_cab_api/smart_cab_api.dart' as api;

import '../../data/api/driver_trips_repository.dart';
import '../../data/api/supervisor_repository.dart';

/// Supervisor trips board screen (S-04).
///
/// Displays active and completed trips board across fleet with pooled trip rider details
/// and night escort gate confirmations (Item 2).
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

  Future<void> _confirmEscort(String tripId, String basis) async {
    try {
      final api.Trip updated = await ref
          .read(supervisorRepositoryProvider)
          .confirmEscort(tripId: tripId, basis: basis);
      if (mounted) {
        setState(() {
          final int index = _trips.indexWhere((t) => t.id == tripId);
          if (index != -1) {
            _trips[index] = updated;
          }
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Escort confirmed for trip $tripId')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.toString())),
        );
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
                    final String tripId = t.id ?? 't_$index';
                    final String tripShortId =
                        tripId.length > 8 ? tripId.substring(0, 8) : tripId;
                    final List<api.TripRider> riders = t.riders?.toList() ?? <api.TripRider>[];
                    final bool isPooled = riders.length > 1;

                    final api.TripEscort? escort = t.escort;
                    final bool escortNeeded =
                        escort != null && escort.required_ && !escort.confirmed;
                    final bool escortConfirmed =
                        escort != null && escort.confirmed;

                    return Card(
                      margin: const EdgeInsets.only(bottom: 12.0),
                      elevation: isPooled || escortNeeded ? 3 : 1,
                      color: escortNeeded ? Colors.red.shade50 : null,
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

                            // Red "Escort needed" Banner & Confirmation Buttons (Item 2)
                            if (escortNeeded) ...<Widget>[
                              Card(
                                key: Key('escort-needed-banner-$tripId'),
                                color: Colors.red.shade100,
                                margin: const EdgeInsets.symmetric(vertical: 8.0),
                                child: Padding(
                                  padding: const EdgeInsets.all(12.0),
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: <Widget>[
                                      Row(
                                        children: <Widget>[
                                          const Icon(Icons.security, color: Colors.red),
                                          const SizedBox(width: 8),
                                          Text(
                                            'Escort needed',
                                            style: TextStyle(
                                              color: Colors.red.shade900,
                                              fontWeight: FontWeight.bold,
                                            ),
                                          ),
                                        ],
                                      ),
                                      const SizedBox(height: 8),
                                      Wrap(
                                        spacing: 8.0,
                                        children: <Widget>[
                                          ElevatedButton(
                                            key: Key('escort-arranged-$tripId'),
                                            onPressed: () =>
                                                _confirmEscort(tripId, 'escort_arranged'),
                                            style: ElevatedButton.styleFrom(
                                              backgroundColor: Colors.red.shade700,
                                              foregroundColor: Colors.white,
                                            ),
                                            child: const Text('Escort arranged'),
                                          ),
                                          if (escort.note != 'last_out' && (escort.note == null || !escort.note!.contains('last_out')))
                                            OutlinedButton(
                                              key: Key('male-co-rider-$tripId'),
                                              onPressed: () =>
                                                  _confirmEscort(tripId, 'male_co_rider_present'),
                                              child: const Text('Male co-rider present'),
                                            ),
                                        ],
                                      ),
                                    ],
                                  ),
                                ),
                              ),
                            ] else if (escortConfirmed) ...<Widget>[
                              Padding(
                                padding: const EdgeInsets.symmetric(vertical: 4.0),
                                child: Row(
                                  children: <Widget>[
                                    const Icon(Icons.verified_user, color: Colors.green, size: 18),
                                    const SizedBox(width: 6),
                                    Expanded(
                                      child: Text(
                                        'Escort confirmed by ${escort.confirmedBy ?? 'supervisor'} at ${escort.confirmedAt?.toIso8601String().substring(11, 16) ?? 'now'}',
                                        style: TextStyle(color: Colors.green.shade800, fontSize: 12),
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ],

                            // Riders list with added detour minutes (A17)
                            if (riders.isNotEmpty) ...<Widget>[
                              const SizedBox(height: 8),
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
