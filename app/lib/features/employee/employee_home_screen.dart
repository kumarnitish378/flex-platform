import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:smart_cab_api/smart_cab_api.dart' as api;

import '../../data/api/ride_request_repository.dart';
import '../../l10n/app_localizations.dart';

/// Employee home screen (E-01).
///
/// Shows active request card (status, ETA, cab number) or a "Request a cab" button.
class EmployeeHomeScreen extends ConsumerStatefulWidget {
  const EmployeeHomeScreen({super.key});

  @override
  ConsumerState<EmployeeHomeScreen> createState() => _EmployeeHomeScreenState();
}

class _EmployeeHomeScreenState extends ConsumerState<EmployeeHomeScreen> {
  bool _loading = true;
  String? _error;
  List<api.RideRequest> _myRequests = <api.RideRequest>[];

  @override
  void initState() {
    super.initState();
    _fetchRequests();
  }

  Future<void> _fetchRequests() async {
    try {
      final List<api.RideRequest> requests =
          await ref.read(rideRequestRepositoryProvider).getMyRequests();
      if (mounted) {
        setState(() {
          _myRequests = requests;
          _loading = false;
          _error = null;
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
    final AppText text = AppText.of(context);
    final ThemeData theme = Theme.of(context);

    // Active request: not completed, cancelled, or expired
    final api.RideRequest? active = _myRequests.cast<api.RideRequest?>().firstWhere(
          (api.RideRequest? req) =>
              req != null &&
              req.status != api.RequestStatus.cancelled &&
              req.status != api.RequestStatus.expired &&
              req.status != api.RequestStatus.dropped,
          orElse: () => null,
        );

    return Scaffold(
      key: const Key('E-01'),
      body: RefreshIndicator(
        onRefresh: _fetchRequests,
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: <Widget>[
              if (_loading)
                const Center(
                  child: Padding(
                    padding: EdgeInsets.all(32.0),
                    child: CircularProgressIndicator(),
                  ),
                )
              else if (_error != null)
                Card(
                  color: theme.colorScheme.errorContainer,
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Text(
                      _error!,
                      style: TextStyle(color: theme.colorScheme.onErrorContainer),
                    ),
                  ),
                )
              else if (active != null)
                Card(
                  key: const Key('active-request-card'),
                  elevation: 3,
                  margin: const EdgeInsets.only(bottom: 24.0),
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: <Widget>[
                            Text(
                              'Active Request',
                              style: theme.textTheme.titleMedium
                                  ?.copyWith(fontWeight: FontWeight.bold),
                            ),
                            Chip(
                              label: Text(active.status?.name ?? 'Active'),
                              backgroundColor: theme.colorScheme.primaryContainer,
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        Text('Pickup: ${active.landmark ?? 'Map Pin'}'),
                        const SizedBox(height: 4),
                        Text('Direction: ${active.direction?.name ?? 'to_office'}'),
                        const SizedBox(height: 16),
                        ElevatedButton.icon(
                          key: const Key('view-active-request'),
                          onPressed: () {
                            if (active.id != null) {
                              context.go('/employee/request/${active.id}');
                            }
                          },
                          icon: const Icon(Icons.arrow_forward),
                          label: const Text('View Request Details'),
                        ),
                      ],
                    ),
                  ),
                )
              else
                Card(
                  elevation: 2,
                  margin: const EdgeInsets.only(bottom: 24.0),
                  child: Padding(
                    padding: const EdgeInsets.all(24.0),
                    child: Column(
                      children: <Widget>[
                        Icon(
                          Icons.local_taxi,
                          size: 64,
                          color: theme.colorScheme.primary,
                        ),
                        const SizedBox(height: 16),
                        Text(
                          'Need a ride?',
                          style: theme.textTheme.headlineSmall,
                        ),
                        const SizedBox(height: 8),
                        Text(
                          'Request a cab to or from office',
                          style: theme.textTheme.bodyMedium,
                        ),
                        const SizedBox(height: 20),
                        ElevatedButton(
                          key: const Key('request-cab-button'),
                          onPressed: () {
                            context.go('/employee/request');
                          },
                          child: Text(text.navRequestCab),
                        ),
                      ],
                    ),
                  ),
                ),

              Text(
                'My Requests',
                style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 12),
              if (_myRequests.isEmpty && !_loading)
                const Padding(
                  padding: EdgeInsets.all(16.0),
                  child: Text('No requests yet.'),
                )
              else
                ListView.builder(
                  key: const Key('scheduled-requests-list'),
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  itemCount: _myRequests.length,
                  itemBuilder: (BuildContext context, int index) {
                    final api.RideRequest req = _myRequests[index];
                    final String reqId = req.id ?? '';
                    final String shortId = reqId.length > 8 ? reqId.substring(0, 8) : reqId;
                    return ListTile(
                      title: Text('Request #$shortId'),
                      subtitle: Text('${req.direction?.name ?? ''} • ${req.status?.name ?? ''}'),
                      trailing: const Icon(Icons.chevron_right),
                      onTap: () {
                        if (reqId.isNotEmpty) {
                          context.go('/employee/request/$reqId');
                        }
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
