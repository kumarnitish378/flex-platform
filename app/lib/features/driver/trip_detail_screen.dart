import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:smart_cab_api/smart_cab_api.dart' as api;

import '../../data/api/driver_trips_repository.dart';

/// Driver trip detail screen (D-04).
///
/// Features ordered stops (rider name, landmark, planned time), stop action buttons
/// (Arrived, Done, No show), and navigation CTA.
class TripDetailScreen extends ConsumerStatefulWidget {
  const TripDetailScreen({required this.tripId, super.key});

  final String tripId;

  @override
  ConsumerState<TripDetailScreen> createState() => _TripDetailScreenState();
}

class _TripDetailScreenState extends ConsumerState<TripDetailScreen> {
  bool _loading = true;
  api.Trip? _trip;
  String? _error;

  @override
  void initState() {
    super.initState();
    _fetchDetail();
  }

  Future<void> _fetchDetail() async {
    try {
      final api.Trip detail = await ref
          .read(driverTripsRepositoryProvider)
          .getTripDetail(widget.tripId);
      if (mounted) {
        setState(() {
          _trip = detail;
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

    return Scaffold(
      key: const Key('D-04'),
      appBar: AppBar(
        title: Text('Trip #${widget.tripId.length > 8 ? widget.tripId.substring(0, 8) : widget.tripId}'),
        actions: <Widget>[
          IconButton(
            icon: const Icon(Icons.navigation),
            tooltip: 'Navigate',
            onPressed: () {
              context.go('/driver/trips/${widget.tripId}/navigate');
            },
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null && _trip == null
              ? Center(child: Text(_error!, style: TextStyle(color: theme.colorScheme.error)))
              : SingleChildScrollView(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: <Widget>[
                      Card(
                        elevation: 2,
                        child: Padding(
                          padding: const EdgeInsets.all(16.0),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: <Widget>[
                              Text(
                                'Status: ${_trip?.status?.name ?? 'Dispatched'}',
                                style: theme.textTheme.titleMedium,
                              ),
                              ElevatedButton.icon(
                                onPressed: () {
                                  context.go('/driver/trips/${widget.tripId}/navigate');
                                },
                                icon: const Icon(Icons.map),
                                label: const Text('Map'),
                              ),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 24),

                      Text(
                        'Ordered Stops',
                        style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 12),

                      if (_trip?.stops == null || _trip!.stops!.isEmpty)
                        const Padding(
                          padding: EdgeInsets.all(16.0),
                          child: Text('No stops assigned for this trip.'),
                        )
                      else
                        ListView.builder(
                          shrinkWrap: true,
                          physics: const NeverScrollableScrollPhysics(),
                          itemCount: _trip!.stops!.length,
                          itemBuilder: (BuildContext context, int index) {
                            final api.TripStop stop = _trip!.stops![index];
                            return Card(
                              margin: const EdgeInsets.only(bottom: 12.0),
                              child: ListTile(
                                leading: CircleAvatar(
                                  child: Text('${index + 1}'),
                                ),
                                title: Text('${stop.stopType?.name.toUpperCase()} - ${stop.riderFirstName ?? 'Rider'}'),
                                subtitle: Text('Landmark: ${stop.landmark ?? 'Map Pin'}\nStatus: ${stop.status?.name}'),
                                isThreeLine: true,
                                trailing: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: <Widget>[
                                    IconButton(
                                      key: Key('action-arrived-${stop.id}'),
                                      icon: const Icon(Icons.place, color: Colors.orange),
                                      tooltip: 'Arrived',
                                      onPressed: () {
                                        ScaffoldMessenger.of(context).showSnackBar(
                                          const SnackBar(content: Text('Marked Arrived')),
                                        );
                                      },
                                    ),
                                    IconButton(
                                      key: Key('action-done-${stop.id}'),
                                      icon: const Icon(Icons.check_circle, color: Colors.green),
                                      tooltip: 'Done',
                                      onPressed: () {
                                        ScaffoldMessenger.of(context).showSnackBar(
                                          const SnackBar(content: Text('Marked Done')),
                                        );
                                      },
                                    ),
                                    IconButton(
                                      key: Key('action-no-show-${stop.id}'),
                                      icon: const Icon(Icons.person_off, color: Colors.red),
                                      tooltip: 'No Show',
                                      onPressed: () {
                                        ScaffoldMessenger.of(context).showSnackBar(
                                          const SnackBar(content: Text('Marked No Show')),
                                        );
                                      },
                                    ),
                                  ],
                                ),
                              ),
                            );
                          },
                        ),
                    ],
                  ),
                ),
    );
  }
}
