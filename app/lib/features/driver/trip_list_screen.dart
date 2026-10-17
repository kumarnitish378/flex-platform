import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:smart_cab_api/smart_cab_api.dart' as api;

import '../../data/api/driver_trips_repository.dart';

/// Driver trip list screen (D-03).
///
/// Shows current active trip on top and upcoming trips below.
class TripListScreen extends ConsumerStatefulWidget {
  const TripListScreen({super.key});

  @override
  ConsumerState<TripListScreen> createState() => _TripListScreenState();
}

class _TripListScreenState extends ConsumerState<TripListScreen> {
  bool _loading = true;
  List<api.Trip> _trips = <api.Trip>[];
  String? _error;

  @override
  void initState() {
    super.initState();
    _fetchTrips();
  }

  Future<void> _fetchTrips() async {
    try {
      final List<api.Trip> trips =
          await ref.read(driverTripsRepositoryProvider).getTrips();
      if (mounted) {
        setState(() {
          _trips = trips;
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
    final ThemeData theme = Theme.of(context);

    final api.Trip? activeTrip = _trips.cast<api.Trip?>().firstWhere(
          (api.Trip? t) =>
              t != null &&
              t.status != api.TripStatus.completed &&
              t.status != api.TripStatus.cancelled &&
              t.status != api.TripStatus.aborted,
          orElse: () => null,
        );

    final List<api.Trip> upcomingTrips = _trips
        .where((api.Trip t) => t.status == api.TripStatus.dispatched)
        .toList();

    return Scaffold(
      key: const Key('D-03'),
      appBar: AppBar(title: const Text('My Trips')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _fetchTrips,
              child: SingleChildScrollView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: <Widget>[
                    if (_error != null) ...<Widget>[
                      Text(_error!, style: TextStyle(color: theme.colorScheme.error)),
                      const SizedBox(height: 16),
                    ],

                    // Current Active Trip Card
                    if (activeTrip != null) ...<Widget>[
                      Text(
                        'Current Active Trip',
                        style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 8),
                      Card(
                        key: const Key('current-trip-card'),
                        elevation: 3,
                        color: theme.colorScheme.primaryContainer,
                        child: Padding(
                          padding: const EdgeInsets.all(16.0),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: <Widget>[
                              Text(
                                'Trip #${activeTrip.id?.substring(0, 8) ?? ''}',
                                style: theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold),
                              ),
                              const SizedBox(height: 8),
                              Text('Status: ${activeTrip.status?.name ?? ''}'),
                              Text('Stops: ${activeTrip.stops?.length ?? 0}'),
                              const SizedBox(height: 16),
                              ElevatedButton.icon(
                                onPressed: () {
                                  context.go('/driver/trips/${activeTrip.id}');
                                },
                                icon: const Icon(Icons.arrow_forward),
                                label: const Text('Open Trip Detail'),
                              ),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 24),
                    ],

                    // Upcoming Trips List
                    Text(
                      'Upcoming Trips',
                      style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 8),
                    if (upcomingTrips.isEmpty)
                      const Padding(
                        padding: EdgeInsets.all(16.0),
                        child: Text('No upcoming trips.'),
                      )
                    else
                      ListView.builder(
                        key: const Key('upcoming-trips-list'),
                        shrinkWrap: true,
                        physics: const NeverScrollableScrollPhysics(),
                        itemCount: upcomingTrips.length,
                        itemBuilder: (BuildContext context, int index) {
                          final api.Trip trip = upcomingTrips[index];
                          return ListTile(
                            leading: const Icon(Icons.directions_car),
                            title: Text('Trip #${trip.id?.substring(0, 8) ?? ''}'),
                            subtitle: Text('Status: ${trip.status?.name}'),
                            trailing: const Icon(Icons.chevron_right),
                            onTap: () {
                              context.go('/driver/trips/${trip.id}');
                            },
                          );
                        },
                      ),
                  ],
                ),
              ),
            ),
    );
  }
}
