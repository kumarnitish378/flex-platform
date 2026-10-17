import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:smart_cab_api/smart_cab_api.dart' as api;

import '../../data/api/ride_request_repository.dart';

/// Request confirmation screen (E-03).
///
/// Displays summary details for request [requestId], current status "Finding your cab",
/// and a cancel button.
class RequestConfirmationScreen extends ConsumerStatefulWidget {
  const RequestConfirmationScreen({required this.requestId, super.key});

  final String requestId;

  @override
  ConsumerState<RequestConfirmationScreen> createState() =>
      _RequestConfirmationScreenState();
}

class _RequestConfirmationScreenState
    extends ConsumerState<RequestConfirmationScreen> {
  bool _loading = true;
  bool _cancelling = false;
  String? _error;
  api.RideRequest? _request;

  @override
  void initState() {
    super.initState();
    _fetchDetails();
  }

  Future<void> _fetchDetails() async {
    try {
      final api.RideRequest req = await ref
          .read(rideRequestRepositoryProvider)
          .getRequest(widget.requestId);
      if (mounted) {
        setState(() {
          _request = req;
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

  Future<void> _cancelRequest() async {
    setState(() {
      _cancelling = true;
    });

    try {
      final api.RideRequest cancelled = await ref
          .read(rideRequestRepositoryProvider)
          .cancelRequest(widget.requestId, reason: 'Cancelled by employee');
      if (mounted) {
        setState(() {
          _request = cancelled;
          _cancelling = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _cancelling = false;
          _error = e.toString();
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);

    return Scaffold(
      key: const Key('E-03'),
      appBar: AppBar(
        title: const Text('Request Status'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.go('/employee'),
        ),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null && _request == null
              ? Center(
                  child: Padding(
                    padding: const EdgeInsets.all(24.0),
                    child: Text(_error!, style: TextStyle(color: theme.colorScheme.error)),
                  ),
                )
              : SingleChildScrollView(
                  padding: const EdgeInsets.all(24.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: <Widget>[
                      Card(
                        elevation: 3,
                        child: Padding(
                          padding: const EdgeInsets.all(20.0),
                          child: Column(
                            children: <Widget>[
                              Icon(
                                _request?.status == api.RequestStatus.cancelled
                                    ? Icons.cancel_outlined
                                    : Icons.access_time_filled,
                                size: 56,
                                color: _request?.status == api.RequestStatus.cancelled
                                    ? theme.colorScheme.error
                                    : theme.colorScheme.primary,
                              ),
                              const SizedBox(height: 16),
                              Text(
                                _request?.status == api.RequestStatus.cancelled
                                    ? 'Request Cancelled'
                                    : 'Finding your cab',
                                key: const Key('request-status-text'),
                                style: theme.textTheme.headlineSmall,
                              ),
                              const SizedBox(height: 8),
                              Text(
                                'Request ID: ${widget.requestId}',
                                style: theme.textTheme.bodyMedium,
                              ),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 24),

                      // Details list
                      ListTile(
                        leading: const Icon(Icons.location_on_outlined),
                        title: const Text('Landmark'),
                        subtitle: Text(_request?.landmark ?? 'Map Pin'),
                      ),
                      ListTile(
                        leading: const Icon(Icons.swap_calls),
                        title: const Text('Direction'),
                        subtitle: Text(_request?.direction?.name ?? 'to_office'),
                      ),
                      ListTile(
                        leading: const Icon(Icons.info_outline),
                        title: const Text('Status'),
                        subtitle: Text(_request?.status?.name ?? 'requested'),
                      ),

                      if (_error != null) ...<Widget>[
                        const SizedBox(height: 16),
                        Text(_error!, style: TextStyle(color: theme.colorScheme.error)),
                      ],

                      const SizedBox(height: 32),
                      if (_request?.status != api.RequestStatus.cancelled &&
                          _request?.status != api.RequestStatus.expired)
                        OutlinedButton(
                          key: const Key('cancel-request'),
                          onPressed: _cancelling ? null : _cancelRequest,
                          style: OutlinedButton.styleFrom(
                            foregroundColor: theme.colorScheme.error,
                          ),
                          child: _cancelling
                              ? const SizedBox(
                                  height: 20,
                                  width: 20,
                                  child: CircularProgressIndicator(strokeWidth: 2),
                                )
                              : const Text('Cancel Request'),
                        ),
                    ],
                  ),
                ),
    );
  }
}
